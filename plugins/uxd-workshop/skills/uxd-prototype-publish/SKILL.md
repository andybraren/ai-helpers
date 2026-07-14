---
name: uxd-prototype-publish
description: >-
  Publish a prototype to a merge request or deploy a sanitized copy to GitHub
  Pages, GitLab Pages, or Vercel. Use when sharing a prototype for review,
  opening a designer-friendly MR with pre-flight checks, or deploying a demo URL.
---

# Publish Prototype

Publishes a completed prototype so others can see it. Supports four publishing targets:

- **Repo** — Push prototype code to a git branch and create a merge request, with designer-friendly pre-flight checks (lint, build, rebase, scope audit). Best for team review.
- **Public** — Deploy a sanitized copy to a public GitHub repo with GitHub Pages. Strips all internal/sensitive files. Best for stakeholder or external sharing.
- **GitLab** — Deploy a sanitized copy to a GitLab instance with GitLab Pages. Supports both self-hosted (behind VPN) and gitlab.com. Same sanitization as public.
- **Vercel** — Deploy a sanitized copy to Vercel. Same sensitive-file stripping as public. Best for preview deployments and projects using Vercel.

Also updates the source Jira ticket with a link, quality score, and status labels.

## Conversational Guidance

If the user says "share", "publish", "deploy", "submit", or "I'm done" without specifying a target, ask:

> Your prototype is ready to share. Where should it go?
>
> - **Create a merge request** — I'll push to the repo so your team can review and comment.
> - **Publish to GitHub Pages** — I'll deploy a sanitized version to GitHub Pages with a shareable URL.
> - **Deploy to GitLab Pages** — I'll deploy a sanitized version to a GitLab instance (self-hosted or gitlab.com).
> - **Deploy to Vercel** — I'll deploy a sanitized version to Vercel with a preview URL.

For **repo** target, also ask:

> Open as a **draft** MR (default) or **ready for review**?

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| Prototype files | `.artifacts/{ID}/prototype/` or workspace files | Yes |
| `metadata.json` | `.artifacts/{ID}/metadata.json` | Yes |
| Changeset manifest | `.artifacts/{ID}/changeset.md` | Yes (workspace mode) |
| Workspace analysis | `.artifacts/{ID}/workspace-analysis.json` | Yes (repo target, workspace mode) |
| Review summary | `.artifacts/{ID}/reviews/summary.md` | Recommended |
| Design spec / ticket ref | User-provided or metadata | Recommended (repo target) |

## Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--target` | `repo`, `public`, `gitlab`, `vercel` | `public` | Where to publish |
| `--remote` | Git URL | workspace origin | Remote URL override for repo target |
| `--repo` | `owner/repo` or GitHub URL | — | GitHub repo for public target |
| `--scope` | `draft`, `ready` | `draft` | MR readiness (repo target only) |
| `--dry-run` | flag | Off | Preview without external writes |
| `--skip-jira` | flag | Off | Skip Jira comment and label update |
| `--force` | flag | Off | Submit even if rubric score fails |
| `--no-ssl-verify` | flag | Off | Skip SSL for git push (self-signed certs) |

---

## Step 1: Validate the Prototype

Detect mode and verify required files:

**Workspace mode** (if `workspace-analysis.json` exists):
- Workspace path is accessible
- `changeset.md` lists at least one file
- `metadata.json` exists with required fields

**Standalone mode** (if `.artifacts/{ID}/prototype/` exists):
- `index.html` exists (or at least one HTML file)
- `metadata.json` exists

If validation fails: "Prototype `{ID}` is incomplete. Missing: [list]. Fix before publishing."

## Step 2: Check Review Scores

Read `.artifacts/{ID}/reviews/summary.md` if it exists.

- **Scores pass** (total >= 5, no zeros) → label: `rubric-pass`
- **Scores fail** → label: `needs-attention`
- **No review exists** → warn, recommend running `uxd-prototype-evaluate` first. In `--dry-run` or `--force` mode, proceed anyway.

Unless `--force` is set, block submission if any dimension scored 0.

## Step 2b: Audit CI/CD Configs for Secrets

Before publishing to any target, scan existing CI/CD configuration files in the workspace for sensitive content. This is especially important for workspace mode where the prototype lives inside an existing codebase with its own CI setup.

**Files to scan:** `.gitlab-ci.yml`, `.github/workflows/*.yml`, `.github/workflows/*.yaml`, `Jenkinsfile`, `.circleci/config.yml`, `Dockerfile`, `docker-compose*.yml`

**Patterns to flag:**

- Hardcoded tokens or credentials (e.g., `PRIVATE-TOKEN:`, `Bearer `, `password:`, `secret:`)
- Internal registry URLs (e.g., `registry.internal.example.com`, `quay.io/internal-org`)
- Internal artifact or package repository URLs
- Deploy keys or SSH keys referenced inline
- Hardcoded internal hostnames or IPs in environment variables
- `variables:` blocks with values that look like secrets rather than CI variable references (`$CI_*`, `${{ secrets.* }}`)

**Handling by target:**

- **`public` / `gitlab` / `vercel`**: The publish scripts replace CI files entirely with clean templates, so existing CI content is never carried forward. This audit still runs as a precaution — if secrets are found in CI files, warn the user since those secrets may also be leaked elsewhere in the codebase.
- **`repo`**: CI files are pushed as-is (internal MR). Flag any hardcoded secrets found and recommend using CI variables instead, but do not block the MR.

---

## Step 3: Publish to Target

### Target: repo

Push prototype changes to a git repo and create a merge request. The designer should not need git expertise — handle branch naming, commits, pre-flight checks, and MR description for them.

Read [references/repo-submit-details.md](references/repo-submit-details.md) for branch naming, MR template, pre-flight checks, script usage, and workspace analysis requirements.

#### 3a. Prepare the branch and commits (workspace mode)

1. Confirm the working directory is clean (or only contains this prototype's intended changes). If unrelated uncommitted work exists: **stop** and ask the designer to stash or commit it first.
2. Create a feature branch — never commit directly on `main` or the target branch:
   - Ticket-linked: `design/{ticket}-{short-description}` or `prototype/{ID}`
   - Exploratory: `design/{short-description}`
   - QA fixes: `fix/design-{short-description}`
3. Stage only changeset files (from `changeset.md`). Group into logical commits with user-perspective messages (what changed for the user, not implementation chatter).
4. Rebase onto the latest target branch before push. If conflicts appear, resolve carefully (prefer keeping both changes when safe; regenerate lockfiles rather than hand-editing them). If conflicts are extensive, offer a fresh branch from target and re-apply changes.
5. **Scope check:** Diff against the target branch. Flag files outside the prototype/design scope — especially routes, layout, CI config, `package.json`, tsconfig, webpack/eslint config. Present keep / revert / investigate options before continuing.

Or use the shared script (creates `prototype/{ID}`, commits changeset files, opens the MR):

```bash
python3 plugins/uxd-workshop/skills/uxd-prototype-create/scripts/submit_to_repo.py \
  --rfe-key {ID} --title "{title}" [--remote {remote}] [--no-ssl-verify] [--dry-run]
```

When using the script, still run the pre-flight checks in 3b before treating the MR as ready, and present the MR description for designer approval.

#### 3b. Pre-flight checks (required for repo target)

Run these before opening or marking the MR ready. Do not skip even if the designer says "just push it."

| Check | On failure |
|-------|------------|
| Lint | Auto-fix when possible. Unfixable errors → **blocked**. Warnings only → proceed as draft, note them. |
| Build | **Blocked** until fixed. |
| Tests | **Blocked**, or flag for engineering if failures are clearly pre-existing/out of scope. |
| Token audit | Scan committed files for raw color/spacing/typography values → **degraded**; list locations. Prefer PatternFly tokens (`pf-code-token-check` / `pf-color-scan` when available). |
| Conflict check | **Blocked** until rebase/conflicts are resolved. |

If any check is **blocked**, halt and show results. Do not open a ready-for-review MR.

#### 3c. MR description and designer review

Draft the MR description from the template in [references/repo-submit-details.md](references/repo-submit-details.md). Include: what the user sees differently, design spec/ticket link, PatternFly components used, how to preview, states to check, accessibility checklist, and a short review checklist.

**Always show the description to the designer and get approval before opening the MR.** Use `--scope draft` (default) or `ready` based on their choice.

Labels to apply when conventions allow: design, UX, accessibility (if a11y work is included).

Do not auto-merge. A human reviewer merges.

#### 3d. Standalone mode

For prototypes without a product workspace, initialize and push as a standalone repo (no MR automation):

```bash
cd .artifacts/{ID}/prototype
git init && git add . && git commit -m "feat: prototype for {ID}"
git remote add origin {remote-url} && git push -u origin main
```

> **Sandbox note**: Requires `required_permissions: ["all"]` for git push.

### Target: public

Deploy a sanitized copy to a public GitHub repository with GitHub Pages. This is the workflow for sharing prototypes externally — it strips all internal/sensitive files before pushing.

**Step 3a: GitHub Repository**

Ask the user if they have a repo or should one be created:

```bash
gh repo create <repo-name> --public --description "UX Prototype — {title}"
```

**Step 3b: Run the Publish Script**

```bash
bash "${SKILL_DIR}/scripts/publish-github-pages.sh" \
  --repo "<owner/repo>" \
  --source "<path-to-prototype>"
```

The script handles: temp staging, file copy, sensitive file removal, GitHub Pages workflow, git init + force push, cleanup.

Read [references/sensitive-files.md](references/sensitive-files.md) for the full list of files and directories that are stripped before publishing.

**Step 3c: Enable GitHub Pages**

After push completes:

```bash
gh api repos/<owner>/<repo>/pages -X POST -f build_type=workflow
```

**Step 3d: Confirm Deployment**

Wait for the GitHub Actions workflow, then provide the URL:

```
https://<owner>.github.io/<repo-name>/
```

### Target: gitlab

Deploy a sanitized copy to a GitLab instance with GitLab Pages. Works with both self-hosted GitLab (behind VPN) and gitlab.com. Uses the same sensitive-file stripping as the `public` target.

**Sensitivity note:** Self-hosted GitLab instances behind a VPN are less exposed than public GitHub/gitlab.com deployments, but the same sanitization is applied regardless — internal agent configs, credentials, and design history should never be in a deployed prototype.

**Step 3a: GitLab Project**

Ask the user for the GitLab project path and instance URL:

- **gitlab.com** — provide `namespace/project` (e.g., `my-org/ux-prototype-demo`)
- **Self-hosted** — provide the full URL (e.g., `https://gitlab.internal.example.com/team/prototype`)

If the project doesn't exist yet, the script can create it via the GitLab API (requires a `GITLAB_TOKEN` with `api` scope).

**Step 3b: Run the Publish Script**

```bash
bash "${SKILL_DIR}/scripts/publish-gitlab-pages.sh" \
  --project "<namespace/project>" \
  --source "<path-to-prototype>" \
  [--gitlab-url "<https://gitlab.example.com>"] \
  [--no-ssl-verify]
```

The script handles: temp staging, file copy, sensitive file removal (same list as `publish-github-pages.sh`), `.gitlab-ci.yml` for GitLab Pages, git init + force push, cleanup. Defaults to `https://gitlab.com` if `--gitlab-url` is not provided.

Read [references/sensitive-files.md](references/sensitive-files.md) for the full list of files and directories that are stripped before publishing.

**Step 3c: Confirm Deployment**

After push completes, GitLab CI runs the pages pipeline. Provide the URL:

- **gitlab.com:** `https://<namespace>.gitlab.io/<project>/`
- **Self-hosted:** depends on the instance's Pages domain configuration — check with `curl "${GITLAB_URL}/api/v4/projects/${PROJECT_ID}" --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" | jq .pages_url`

### Target: vercel

Deploy a sanitized copy to Vercel. Uses the same sensitive-file stripping as the `public` target.

**Step 3a: Vercel Project**

Ask the user if they have an existing Vercel project or should deploy fresh:

- **Existing project** — provide the Vercel project name or link
- **New deployment** — the script initializes a new Vercel project

**Step 3b: Run the Publish Script**

```bash
bash "${SKILL_DIR}/scripts/publish-vercel.sh" \
  --source "<path-to-prototype>" \
  [--project-name "<vercel-project-name>"]
```

The script handles: temp staging, file copy, sensitive file removal (same list as `publish-github-pages.sh`), Vercel deployment via `vercel --prod`, cleanup.

Read [references/sensitive-files.md](references/sensitive-files.md) for the full list of files and directories that are stripped before publishing.

**Step 3c: Confirm Deployment**

After deploy completes, the script outputs the production URL:

```
https://<project-name>.vercel.app
```

---

## Step 4: Update Jira (Optional)

If Jira integration is available and `--skip-jira` is not set:

1. Add a comment to the source issue linking to the published location, rubric score, and refinement count.
2. Add labels: `prototype-created` plus the rubric verdict label (`rubric-pass` or `needs-attention`).

Uses the Atlassian MCP if available, otherwise skips silently.

## Step 5: Update Metadata

Update `.artifacts/{ID}/metadata.json` with submission record:

```json
{
  "status": "submitted",
  "submission": {
    "target": "repo",
    "date": "{ISO-8601}",
    "url": "https://gitlab.example.com/org/repo/-/merge_requests/42"
  }
}
```

Update frontmatter:

```bash
python3 "${SKILL_DIR}/scripts/frontmatter.py" set ".artifacts/{ID}/rfe-snapshot.md" \
  status="submitted" updated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

## Step 6: Report

Print a submission summary showing ID, target, rubric score, labels applied, Jira status, published location, and any warnings.

If `--dry-run`: Show what would happen without executing external writes.

---

## Re-Publishing

To update a previously published prototype, run the same workflow again. The public and gitlab targets force-push (replaces entirely). The vercel target redeploys (replaces the previous deployment). The repo target creates a new branch/MR.

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No review exists | Warn and recommend `uxd-prototype-evaluate`. Proceed with `--force`. |
| Rubric score has zeros | Block unless `--force`. Label as `needs-attention`. |
| No Jira key in metadata | Skip Jira update. Log warning. |
| Prototype already submitted | Proceed (creates new submission record, doesn't overwrite). |
| `--dry-run` with missing deps | Succeeds — only validates local state and previews. |
| Large prototype (5+ MB) | Warn before push. Suggest trimming assets. |
| Pre-flight blocked (repo) | Halt. Show failures. Do not open ready MR. |
| Out-of-scope files in diff | Present keep / revert / investigate before push. |
| Designer asks to skip checks | Run checks anyway; explain they protect the first MR experience. |

## Repo target guardrails

- Never commit or push directly to `main` / the merge target branch.
- Never force-push a shared branch. After rebase, prefer `--force-with-lease` only when rewriting your own unpublished branch history is required — and confirm with the designer first.
- Never open an MR without designer review of the description.
- Never modify files outside the prototype/design scope without explicit designer approval.
- Never auto-merge the MR.

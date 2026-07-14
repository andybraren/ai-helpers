# Repo Submit Details

Full procedure for submitting workspace-mode prototypes as merge requests. Load this when `--target=repo` and the prototype is in workspace mode.

## Branch naming

| Pattern | When |
|---------|------|
| `prototype/{ID}` | Default for artifact-based prototypes (matches `submit_to_repo.py`) |
| `design/{ticket}-{short-description}` | Changes tied to a tracked ticket |
| `design/{short-description}` | Exploratory changes without a ticket |
| `fix/design-{short-description}` | Design QA fixes after review |

Never commit on `main` or the merge target branch directly.

## MR description template

```markdown
## What this changes
[1-2 sentences: what the user sees differently]

## Design spec
[Link to design spec, Figma, or Jira ticket]

## PatternFly components used
[List of PatternFly components added or modified]

## How to review
1. [Steps to preview the change in browser]
2. [States to check: default, hover, error, empty, loading, etc.]

## Accessibility
- [ ] Keyboard navigation verified
- [ ] Screen reader considerations documented
- [ ] ARIA labels present where needed

## Checklist
- [ ] PatternFly tokens used (no raw color/spacing values)
- [ ] All states from the design intent are represented
- [ ] Out-of-scope files were not changed (or changes were intentional)
- [ ] Design file / ticket linked

Assisted-by: AI
```

When publishing from the prototype pipeline, also include (when available):

- **Pipeline details** — Mode (auto vs decide), rubric score
- **Key design decisions** — Chosen options and auto/human tags
- **Assumptions** — Scope constraints from `metadata.json`
- **Provenance** — Generated via `uxd-prototype-create` / publish workflow

## Pre-flight checks

| Check | Action on failure |
|-------|-------------------|
| Lint | Auto-fix if possible. Unfixable errors → blocked. Warnings only → degraded (draft OK). |
| Build | Blocked until fixed. |
| Tests | Blocked, or flag pre-existing out-of-scope failures for engineering. |
| Token audit | Degraded: list raw values. Prefer `pf-code-token-check` / `pf-color-scan`. |
| Conflict check | Blocked until rebase/conflicts resolved. |
| Scope check | Flag files outside prototype intent (routes, layout, CI, package.json, tsconfig, bundler/eslint config). |

### Rebase procedure

1. Fetch target: `git fetch origin`
2. If target has new commits, rebase onto `origin/<target-branch>`
3. On conflicts: plan first, keep both changes when safe, regenerate lockfiles instead of hand-merging them
4. Continue rebase, then re-run pre-flight checks

### Scope check procedure

1. List changed files vs target: `git diff --name-only origin/<target-branch>...HEAD`
2. Compare against `changeset.md` / design intent
3. Present out-of-scope files with keep / revert / investigate
4. Revert accidental changes from the target branch before opening the MR

## submit_to_repo.py

The script lives at `plugins/uxd-workshop/skills/uxd-prototype-create/scripts/submit_to_repo.py` (shared with the create skill).

### What the script does

1. Reads `.artifacts/{ID}/workspace-analysis.json` for clone URL, original branch, and workspace path.
2. Reads `.artifacts/{ID}/changeset.md` to identify created/modified files.
3. Creates branch `prototype/{ID}` in the workspace.
4. Stages only changeset files (skips files not on disk).
5. Commits with message: `Prototype: {ID} — {title}`.
6. Detects shallow clones and runs `git fetch --unshallow` (GitLab rejects pushes from shallow repos).
7. Generates a designer-oriented MR description.
8. Pushes with GitLab push options to create the MR during `git push`.
9. Outputs JSON with status, branch, remote, MR URL, and commit hash.

Use the script as a shortcut for branch/commit/push, then still run pre-flight checks and get designer approval of the MR description (update the MR description after push if needed).

### Script output

```json
{
  "status": "pushed",
  "branch": "prototype/PROJ-298",
  "target_branch": "3.5",
  "remote": "https://gitlab.example.com/org/repo.git",
  "merge_request_url": "https://gitlab.example.com/org/repo/-/merge_requests/42",
  "commit": "abc1234",
  "files_committed": 7
}
```

### Prerequisites

- `workspace-analysis.json` must contain `branch` and `clone_url` fields (from `resolve_workspace.py`)
- Git credentials must be configured for the remote
- In Cursor, run with `required_permissions: ["all"]` for git push

### Flags

| Flag | Description |
|------|-------------|
| `--rfe-key` | Prototype ID (required) |
| `--title` | MR title (from metadata) |
| `--remote` | Override remote URL (fork workflows) |
| `--no-ssl-verify` | Skip SSL verification (self-signed certs) |
| `--dry-run` | Show commands without executing |

## Standalone mode alternative

For standalone prototypes without a workspace, the submit creates a fresh repo:

```bash
cd .artifacts/{ID}/prototype
git init
git add .
git commit -m "feat: prototype for {ID}"
git remote add origin {remote-url}
git push -u origin main
```

This does not create a merge request — it is a simple push.

## Verification checklist (repo target)

Before treating the MR as done:

- [ ] Working on a feature branch (not main/target)
- [ ] Pre-flight ran: lint, build, tests, token audit, conflict check, scope check
- [ ] No blocked pre-flight results remain (or designer explicitly chose draft with known degraded items)
- [ ] Commits are logical and use user-perspective messages
- [ ] MR description follows the template
- [ ] Designer reviewed and approved the MR description
- [ ] MR scope matches prototype/design intent

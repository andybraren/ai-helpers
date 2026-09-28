# Phase 0 — Infrastructure checklist (CP0)

**Date:** 2026-09-02  
**Cluster:** UXDPOC7 ROSA (`ux-eval` namespace)

## Resource verification

| Component | Required | Status |
|-----------|----------|--------|
| Langfuse web + worker | Yes | **Local first** (`make langfuse-local-up`); cluster pending capacity |
| PostgreSQL (in-cluster) | Yes | Via Helm |
| ClickHouse (in-cluster) | Yes | Via Helm |
| Redis/Valkey (in-cluster) | Yes | Via Helm |
| Blob storage / MinIO (in-cluster) | Yes | Via Helm |
| 30-day retention | Yes | `LANGFUSE_DATA_RETENTION_DAYS=30` in Helm values |

## Local Langfuse (test before cluster deploy)

```bash
# Requires Docker Desktop or OrbStack
make langfuse-local-up
eval "$(make langfuse-local-env)"
make langfuse-smoke
make run-phase1-verify KEY=RHAISTRAT-1492
```

See `docker/langfuse/README.md`. MLflow observability was retired in favor of
Langfuse; verify cluster capacity before deployment.

## Deployment (cluster)

```bash
oc login https://api.uxdpoc7.9hji.p3.openshiftapps.com:443
bash scripts/deploy-langfuse-ux-eval.sh
```

Route: `https://langfuse-ux-eval.apps.rosa.uxdpoc7.9hji.p3.openshiftapps.com`

## CP0 checklist

- [ ] Langfuse health endpoint returns 200 — **local:** `make langfuse-local-up`; cluster blocked until disk-pressure cleared
- [ ] One smoke trace visible in Langfuse UI — run `eval "$(make langfuse-local-env)" && make langfuse-smoke`
- [x] Cluster resource sheet recorded
- [ ] Provider model names captured from CLI smoke run — pending `claude --print` run

### Cluster findings (ongoing)

- Nodes 146/180: `disk-pressure` taint — blocks new pods + Langfuse deploy
- Autoscaler at max node group size
- Langfuse deploy deferred until disk cleared + `helm` installed

## Local instrumentation (ready before cluster)

| Item | Status |
|------|--------|
| `scripts/langfuse_trace.py` | **Done** |
| `scripts/log-cost-ledger.js` | **Done** |
| `scripts/deploy-langfuse-ux-eval.sh` | **Done** |
| `make langfuse-env` | **Done** |
| `make langfuse-smoke` | **Done** (dry-run OK) |
| `make ledger-smoke` | **Done** |

## Next

Phase 1: `make run-phase1-verify KEY=RHAISTRAT-1492`

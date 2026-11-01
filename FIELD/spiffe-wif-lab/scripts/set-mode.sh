#!/usr/bin/env bash
set -euo pipefail

lab_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$lab_dir"
if [[ $# -lt 1 || $# -gt 2 || ( "$1" != protected && "$1" != weak_audience && "$1" != weak_tenant && "$1" != opa_guard )
      || ( "${2:-read}" != read && "${2:-read}" != insert ) ]]; then
    printf 'Usage: %s protected|weak_audience|weak_tenant|opa_guard [read|insert]\n' "$0" >&2
    exit 2
fi
if [[ ! -f .env ]]; then
    printf 'Run scripts/bootstrap.sh first.\n' >&2
    exit 1
fi
mode=$1
task_kind=${2:-read}
task_id=task-alpha
if [[ "$task_kind" == insert ]]; then
    task_id=task-insert-alpha
fi
umask 077
mkdir -p state
awk '!/^(LAB_MODE|LAB_TASK_KIND|LAB_TASK_ID)=/' .env > state/env.filtered
cat state/env.filtered > .env
printf 'LAB_MODE=%s\nLAB_TASK_KIND=%s\nLAB_TASK_ID=%s\n' \
    "$mode" "$task_kind" "$task_id" >> .env
rm -f state/env.filtered
chmod 600 .env
docker compose up -d --force-recreate mock-api
ready=0
for _ in $(seq 1 30); do
    if docker compose exec -T mock-api python -c 'import httpx; r=httpx.get("http://127.0.0.1:8080/health", trust_env=False, timeout=1); r.raise_for_status()' >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
if [[ "$ready" != 1 ]]; then
    docker compose logs --tail=30 mock-api >&2
    printf 'Mock API did not become ready.\n' >&2
    exit 1
fi
if [[ "$mode" != weak_tenant ]]; then
    if ! docker compose exec -T mock-api python -c 'import httpx; r=httpx.post("http://opa:8181/v1/data/fielddesk/authz/allow", json={"input": {}}, trust_env=False, timeout=3); r.raise_for_status(); assert r.json().get("result") is False' >/dev/null 2>&1; then
        printf 'OPA is unavailable or did not return default deny.\n' >&2
        exit 1
    fi
fi
printf 'Mock API mode: %s, task: %s (synthetic grant reset).\n' "$mode" "$task_kind"

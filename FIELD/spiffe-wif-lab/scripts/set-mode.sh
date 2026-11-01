#!/usr/bin/env bash
set -euo pipefail

lab_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$lab_dir"
if [[ $# -ne 1 || ( "$1" != protected && "$1" != weak_audience && "$1" != weak_tenant ) ]]; then
    printf 'Usage: %s protected|weak_audience|weak_tenant\n' "$0" >&2
    exit 2
fi
if [[ ! -f .env ]]; then
    printf 'Run scripts/bootstrap.sh first.\n' >&2
    exit 1
fi
mode=$1
umask 077
mkdir -p state
awk '!/^LAB_MODE=/' .env > state/env.filtered
cat state/env.filtered > .env
printf 'LAB_MODE=%s\n' "$mode" >> .env
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
printf 'Mock API mode: %s (synthetic task grant reset).\n' "$mode"

#!/usr/bin/env bash
set -euo pipefail

lab_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$lab_dir"

if [[ $# -ne 1 || ( "$1" != protected && "$1" != label-only ) ]]; then
    printf 'Usage: %s protected|label-only\n' "$0" >&2
    exit 2
fi
mode=$1
docker compose exec -T spire-server /opt/spire/bin/spire-server healthcheck \
    -socketPath /var/lib/spire/server/admin.sock >/dev/null

entry_args=(
    -entryID fielddesk-agent
    -parentID spiffe://fielddesk.test/lab-node
    -spiffeID spiffe://fielddesk.test/agent
    -selector docker:label:fielddesk.workload:agent
)
if [[ "$mode" == protected ]]; then
    image_digest=$(docker image inspect --format '{{.Id}}' fielddesk-spiffe-agent:local)
    rogue_digest=$(docker image inspect --format '{{.Id}}' fielddesk-spiffe-rogue:local)
    if [[ ! "$image_digest" =~ ^sha256:[0-9a-f]{64}$ || "$image_digest" == "$rogue_digest" ]]; then
        printf 'Agent and rogue images must have distinct, valid config digests.\n' >&2
        exit 1
    fi
    entry_args+=(-selector "docker:image_config_digest:$image_digest")
fi

# A stable entry ID makes mode switches explicit and repeatable. Issued bearer
# JWT-SVIDs may remain valid until exp; the next fetch tests the new entry.
docker compose exec -T spire-server /opt/spire/bin/spire-server entry delete \
    -entryID fielddesk-agent -socketPath /var/lib/spire/server/admin.sock \
    >/dev/null 2>&1 || true
docker compose exec -T spire-server /opt/spire/bin/spire-server entry create \
    "${entry_args[@]}" \
    -socketPath /var/lib/spire/server/admin.sock >/dev/null

expected_service=agent
if [[ "$mode" == label-only ]]; then
    expected_service=rogue
fi
ready=0
for _ in $(seq 1 20); do
    if docker compose --profile exercise run --pull never --rm --no-deps "$expected_service" --identity-only >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
if [[ "$ready" != 1 ]]; then
    printf 'SPIRE Agent did not serve the new %s entry within 20 seconds.\n' "$mode" >&2
    exit 1
fi
if [[ "$mode" == protected ]]; then
    rogue_denied=0
    for _ in $(seq 1 20); do
        if probe_output=$(docker compose --profile exercise run --pull never --rm --no-deps rogue --identity-only 2>&1); then
            : # The old registration may still be cached by the SPIRE Agent.
        elif [[ "$probe_output" == *"PermissionDenied desc = no identity issued"* ]]; then
            rogue_denied=1
            break
        fi
        sleep 1
    done
    if [[ "$rogue_denied" != 1 ]]; then
        printf 'Rogue probe did not prove a Workload API identity denial; inspect Docker/SPIRE health and retry.\n' >&2
        exit 1
    fi
fi

printf 'Registered agent identity in %s mode.\n' "$mode"
if [[ "$mode" == protected ]]; then
    printf 'Image config digest: %s\n' "$image_digest"
fi

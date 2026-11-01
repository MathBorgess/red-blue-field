#!/usr/bin/env bash
set -euo pipefail

lab_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$lab_dir"
umask 077

for tool in docker openssl; do
    command -v "$tool" >/dev/null || { printf '%s is required\n' "$tool" >&2; exit 1; }
done
docker info >/dev/null || { printf 'Docker is unavailable; start your existing local runtime first.\n' >&2; exit 1; }
docker compose version >/dev/null

mkdir -p state/tls state/data
if [[ ! -f .env ]]; then
    cp .env.example .env
fi
chmod 600 .env

if [[ ! -e state/tls/ca.key && ! -e state/tls/ca.crt ]]; then
    openssl req -x509 -newkey rsa:2048 -noenc -sha256 -days 30 \
        -keyout state/tls/ca.key -out state/tls/ca.crt \
        -subj '/CN=FieldDesk local lab CA' \
        -addext 'basicConstraints=critical,CA:TRUE' \
        -addext 'keyUsage=critical,keyCertSign,cRLSign' >/dev/null 2>&1
fi
if [[ ! -f state/tls/ca.key || ! -f state/tls/ca.crt ]]; then
    printf 'Partial local CA state; inspect state/tls before retrying.\n' >&2
    exit 1
fi
if ! openssl x509 -in state/tls/ca.crt -checkend 3600 -noout >/dev/null; then
    printf 'Local CA expires soon; inspect state/tls and reset this lab deliberately.\n' >&2
    exit 1
fi

if [[ ! -f state/tls/oidc.key ]]; then
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 \
        -out state/tls/oidc.key >/dev/null 2>&1
fi
if [[ ! -f state/tls/oidc.crt ]] || ! openssl x509 -in state/tls/oidc.crt -checkend 3600 -noout >/dev/null 2>&1; then
    openssl req -new -key state/tls/oidc.key -out state/tls/oidc.csr \
        -subj '/CN=oidc.local' >/dev/null 2>&1
    cat > state/tls/oidc.ext <<'EOF'
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:oidc.local
EOF
    openssl x509 -req -in state/tls/oidc.csr \
        -CA state/tls/ca.crt -CAkey state/tls/ca.key -CAcreateserial \
        -out state/tls/oidc.crt -days 7 -sha256 \
        -extfile state/tls/oidc.ext >/dev/null 2>&1
    rm -f state/tls/oidc.csr state/tls/oidc.ext
fi
chmod 600 state/tls/ca.key state/tls/oidc.key
chmod 644 state/tls/ca.crt state/tls/oidc.crt
openssl verify -CAfile state/tls/ca.crt state/tls/oidc.crt >/dev/null
openssl x509 -in state/tls/oidc.crt -noout -ext subjectAltName | grep -q 'DNS:oidc.local'
docker compose config --quiet

# Official SPIRE images run server and OIDC as uid 1000. The OIDC process uses
# the current host uid so it can read its private key without world-readability.
lab_uid=$(id -u)
lab_gid=$(id -g)
awk '!/^(LAB_UID|LAB_GID)=/' .env > state/env.filtered
cat state/env.filtered > .env
printf 'LAB_UID=%s\nLAB_GID=%s\n' "$lab_uid" "$lab_gid" >> .env
rm -f state/env.filtered
chmod 600 .env
docker compose up -d spire-server

wait_exec() {
    local service=$1
    shift
    for _ in $(seq 1 60); do
        if docker compose exec -T "$service" "$@" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    docker compose logs --tail=40 "$service" >&2
    printf '%s did not become ready\n' "$service" >&2
    return 1
}

wait_exec spire-server /opt/spire/bin/spire-server healthcheck \
    -socketPath /var/lib/spire/server/admin.sock
docker compose exec -T spire-server /opt/spire/bin/spire-server bundle show \
    -format pem -socketPath /var/lib/spire/server/admin.sock \
    > state/server-bundle.pem
chmod 644 state/server-bundle.pem
openssl x509 -in state/server-bundle.pem -noout >/dev/null

if ! docker compose ps --status running --services | grep -qx spire-agent; then
    join_output=$(docker compose exec -T spire-server /opt/spire/bin/spire-server token generate \
        -spiffeID spiffe://fielddesk.test/lab-node \
        -socketPath /var/lib/spire/server/admin.sock)
    join_token=$(printf '%s\n' "$join_output" | sed -n 's/^Token:[[:space:]]*//p' | head -n 1)
    if [[ ! "$join_token" =~ ^[A-Za-z0-9._-]+$ ]]; then
        printf 'Could not parse SPIRE node join token.\n' >&2
        exit 1
    fi

    awk '!/^SPIRE_JOIN_TOKEN=/' .env > state/env.filtered
    cat state/env.filtered > .env
    printf 'SPIRE_JOIN_TOKEN=%s\n' "$join_token" >> .env
    rm -f state/env.filtered
    chmod 600 .env
    unset join_token join_output
    docker compose up -d spire-agent
fi
wait_exec spire-agent /opt/spire/bin/spire-agent healthcheck \
    -socketPath /run/spire/agent.sock

# The OIDC provider is infrastructure too; its identity must be tied to its
# pinned image as well as its label. Pull only if the pinned image is absent.
oidc_image=$(docker compose config --images | awk '/^ghcr.io\/spiffe\/oidc-discovery-provider:/ {print; exit}')
if [[ -z "$oidc_image" ]]; then
    printf 'Could not identify the pinned OIDC image.\n' >&2
    exit 1
fi
if ! docker image inspect "$oidc_image" >/dev/null 2>&1; then
    docker compose pull oidc
fi
oidc_digest=$(docker image inspect --format '{{.Id}}' "$oidc_image")
if [[ ! "$oidc_digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
    printf 'Invalid OIDC image config digest.\n' >&2
    exit 1
fi
oidc_entry=$(docker compose exec -T spire-server /opt/spire/bin/spire-server entry show \
    -entryID fielddesk-oidc -socketPath /var/lib/spire/server/admin.sock 2>/dev/null || true)
if [[ "$oidc_entry" != *"docker:image_config_digest:$oidc_digest"* ]]; then
    docker compose exec -T spire-server /opt/spire/bin/spire-server entry delete \
        -entryID fielddesk-oidc -socketPath /var/lib/spire/server/admin.sock \
        >/dev/null 2>&1 || true
    docker compose exec -T spire-server /opt/spire/bin/spire-server entry create \
        -entryID fielddesk-oidc \
        -parentID spiffe://fielddesk.test/lab-node \
        -spiffeID spiffe://fielddesk.test/oidc-provider \
        -selector docker:label:fielddesk.workload:oidc \
        -selector "docker:image_config_digest:$oidc_digest" \
        -socketPath /var/lib/spire/server/admin.sock >/dev/null
fi

# Build sequentially on the 2 CPU / 2 GiB local VM.
docker compose build mock-api
docker compose build agent
docker compose build rogue
"$lab_dir/scripts/register.sh" protected
docker compose up -d oidc mock-api

wait_exec mock-api python -c 'import httpx; r=httpx.get("https://oidc.local:8443/keys", verify="/run/lab/tls/ca.crt", trust_env=False, timeout=3); r.raise_for_status(); assert r.json().get("keys")'
printf 'Local SPIRE, HTTPS JWKS and mock API are ready. Registration: protected.\n'
printf 'Run: docker compose --profile exercise run --pull never --rm agent --ticket=ticket-alpha\n'

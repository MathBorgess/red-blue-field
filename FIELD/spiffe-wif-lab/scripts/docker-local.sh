#!/usr/bin/env bash
set -euo pipefail

# Scope every Docker command to the already-running Colima VM. A private CLI
# config avoids a stale Docker Desktop credential helper for public images.
lab_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
config_dir="$lab_dir/state/docker-config"
mkdir -p "$config_dir/cli-plugins"
if [[ ! -e "$config_dir/config.json" ]]; then
    printf '{}\n' > "$config_dir/config.json"
fi
if [[ ! -e "$config_dir/contexts" ]]; then
    ln -s "$HOME/.docker/contexts" "$config_dir/contexts"
fi
if [[ ! -e "$config_dir/cli-plugins/docker-compose" ]]; then
    compose_binary=$(command -v docker-compose)
    ln -s "$compose_binary" "$config_dir/cli-plugins/docker-compose"
fi
export DOCKER_CONFIG="$config_dir"
export DOCKER_CONTEXT=colima
docker info >/dev/null
exec "$@"

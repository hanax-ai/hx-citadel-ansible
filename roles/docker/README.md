# roles/docker

Installs Docker CE and (optionally) starts containers.

## Variables
- `docker_users` (list): local users to add to `docker` group. Default: `["agent0"]`
- `docker_manage_firewall` (bool): disable host firewall per HX policy. Default: true
- `docker_containers_explicit` (list[dict]): fixed-name containers
- `docker_containers_by_count` (list[dict]): N copies, auto-named `<base_name>-<index>`

## Examples

### A) Three named services
docker_containers_explicit:
  - name: hx-qdrant
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["/data/qdrant:/qdrant/storage"]
  - name: hx-litellm
    image: ghcr.io/berriai/litellm:latest
    ports: ["4000:4000"]

### B) Scale-out workers with auto names
docker_containers_by_count:
  - base_name: hx-worker
    image: alpine:3.20
    count: 3
    start_index: 1
    command: ["sh","-c","sleep 3600"]

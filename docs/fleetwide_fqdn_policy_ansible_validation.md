# HX-Citadel Fleetwide FQDN / Short-Name Policy

## Universal Instruction (drop-in system prompt / policy)

> **Instruction to all AI, scripts, and agents:**
> The HX-Citadel environment is domain-integrated (`dev-test.hana-x.ai`).
> **Always use** each host’s **FQDN** (e.g., `hx-ollama1.dev-test.hana-x.ai`) or its **short name** (e.g., `hx-ollama1`) for *all* references, configs, URLs, and connection strings.
> **Never use** loopback or raw IPs (`localhost`, `127.0.0.1`, `::1`, `192.168.10.x`, etc.) except for temporary diagnostics.
> When generating or modifying configuration files, **replace all local/numeric addresses** with proper FQDNs or short hostnames.
>
> **Correct:**
>
> * `http://hx-orchestrator-server.dev-test.hana-x.ai:8000/events/stats`
> * `redis://hx-sqldb-server.dev-test.hana-x.ai:6379/0`
> * `ssh agent0@hx-dev-server.dev-test.hana-x.ai`
>
> **Prohibited:**
>
> * `http://localhost:8000/events/stats`
> * `http://127.0.0.1:4000/v1/models`
> * `ssh agent0@192.168.10.8`

### Short Form (for playbooks / CI / guardrails)

```yaml
ai_fqdn_policy: |
  Use FQDNs or short names for all services across the HX fleet.
  Do NOT use localhost, 127.0.0.1, ::1, or raw IPs.
  Domain: dev-test.hana-x.ai
```

---

## Ansible Guardrail: Detect & Fail on non-FQDN usage

**Purpose:** Break builds if any config/templates/scripts contain `localhost`, `127.0.0.1`, `::1`, or raw `192.168.10.x` literals (except in an approved allowlist).

> Drop this task file into your role (e.g., `roles/common_dns_guard/tasks/main.yml`) and include it where appropriate.

```yaml
---
# roles/common_dns_guard/tasks/main.yml
- name: Define guardrail vars
  vars:
    hx_domain: "dev-test.hana-x.ai"
    guard_paths:
      - "/etc"
      - "/opt/hx-citadel-shield"
      - "{{ app_dir | default('/opt/hx-citadel-shield') }}"
    # Regex patterns that should NOT appear
    forbidden_patterns:
      - "(?i)\blocalhost\b"
      - "\b127\.0\.0\.1\b"
      - "\b::1\b"
      - "\b192\.168\.10\.(?:[0-9]{1,3})\b"
    # Optional: allow specific files/lines that must keep IPs (health checks, low-level diagnostics)
    allow_globs:
      - "/etc/hosts"           # static host file may contain 127.0.1.1
      - "/etc/resolv.conf"     # managed by systemd-resolved
      - "/etc/systemd/**"      # unit files may reference localhost for internal binds

- name: Gather candidate files
  ansible.builtin.find:
    paths: "{{ guard_paths }}"
    patterns: "*"
    file_type: file
    use_regex: false
    recurse: true
  register: _guard_files

- name: Filter out allowed glob paths
  set_fact:
    _scan_files: "{{ _guard_files.files | map(attribute='path') | list | difference((allow_globs | map('regex_replace', '\\*\\*', '.*') | list) | map('regex_search', '^') | list) }}"
  vars:
    # The above is conservative; if your Ansible version struggles with difference/regex, fall back to shell skip logic below
    dummy: "ignore"

- name: Scan for forbidden patterns (shell grep for speed)
  ansible.builtin.shell: |
    set -o pipefail
    grep -EnH --color=never -R \
      -e "{{ forbidden_patterns | join('" -e "') }}" \
      {{ _guard_files.files | map(attribute='path') | map('quote') | join(' ') }} \
      | grep -Ev "{{ (allow_globs | map('regex_escape') | map('regex_replace', '\\*', '.*') | list) | join('|') }}" || true
  args:
    warn: false
  register: _grep_out
  changed_when: false

- name: Fail if any forbidden usage was found
  ansible.builtin.fail:
    msg: |
      Forbidden non-FQDN usage detected. Replace with FQDNs/short names.
      ----
      {{ _grep_out.stdout | default('') }}
  when: _grep_out.stdout | length > 0
```

> **Notes**
>
> * This uses `grep -R` for performance and then filters allowlisted paths. Adjust `guard_paths` to match your repo and host paths.
> * Tighten/extend `forbidden_patterns` if other subnets or forms show up.
> * If your CI runs on a control node rather than targets, point `guard_paths` to your repo root instead of `/etc`.

---

## Optional: Auto-Remediation (convert IPs → FQDNs)

If you want an assisted rewrite pass (dry-run first), add this task file **after** the guardrail:

```yaml
---
# roles/common_dns_guard/tasks/auto_fix.yml
- name: Map fleet IPs to FQDNs (example — extend as needed)
  vars:
    ip_map:
      "192.168.10.8":  "hx-orchestrator-server.dev-test.hana-x.ai"
      "192.168.10.46": "hx-litellm-server.dev-test.hana-x.ai"
      "192.168.10.47": "hx-prisma-server.dev-test.hana-x.ai"
      "192.168.10.48": "hx-sqldb-server.dev-test.hana-x.ai"
      "192.168.10.50": "hx-ollama1.dev-test.hana-x.ai"
      "192.168.10.52": "hx-ollama2.dev-test.hana-x.ai"
      "192.168.10.11": "hx-webui-server.dev-test.hana-x.ai"
      "192.168.10.53": "hx-qwebui-server.dev-test.hana-x.ai"
  block:
    - name: Preview replacements (no changes, just show)
      ansible.builtin.shell: |
        set -o pipefail
        for ip in {{ ip_map.keys() | list | join(' ') }}; do
          grep -EnH -R "$ip" {{ guard_paths | first }} || true
        done
      register: _preview
      changed_when: false

    - name: Apply replacements (set apply_changes=true to enable)
      when: apply_changes | default(false) | bool
      ansible.builtin.replace:
        path: "{{ item.0 }}"
        regexp: "\b{{ item.1.key | regex_escape }}\b"
        replace: "{{ item.1.value }}"
      loop: "{{ query('ansible.builtin.fileglob', guard_paths | first ~ '/**/*', recursive=True) | product(ip_map | dict2items) | list }}"
```

---

## CI Hook (pre-commit example)

Use `pre-commit` to block commits that introduce disallowed patterns:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: forbid-localhost-and-ips
        name: Forbid localhost/127.0.0.1/::1/192.168.10.x
        entry: bash -lc 'grep -EnH -R -e "\\blocalhost\\b" -e "\\b127\\.0\\.0\\.1\\b" -e "\\b::1\\b" -e "\\b192\\.168\\.10\\.[0-9]{1,3}\\b" || true'
        language: system
        pass_filenames: false
        stages: [commit]
```

---

## Usage Pattern

1. Include the **policy** prompt at the top of AI/automation contexts.
2. Add the **Ansible guardrail** to roles that produce configs or connection strings.
3. (Optional) Enable **auto-fix** + **pre-commit** in repos to prevent regressions.

---

*End of policy & guardrail document.*

---

## Fleet host → FQDN map (Ansible vars)

Drop this into `group_vars/all/fqdn_map.yml` (or include via `vars_files`).

```yaml
hx_domain: dev-test.hana-x.ai
hx_dc_ip: 192.168.10.2

# Short → FQDN
hx_hosts_fqdn:
  hx-dc-server: hx-dc-server.dev-test.hana-x.ai
  hx-ca-server: hx-ca-server.dev-test.hana-x.ai
  hx-orchestrator-server: hx-orchestrator-server.dev-test.hana-x.ai
  hx-vectordb-server: hx-vectordb-server.dev-test.hana-x.ai
  hx-litellm-server: hx-litellm-server.dev-test.hana-x.ai
  hx-prisma-server: hx-prisma-server.dev-test.hana-x.ai
  hx-sqldb-server: hx-sqldb-server.dev-test.hana-x.ai
  hx-ollama1: hx-ollama1.dev-test.hana-x.ai
  hx-ollama2: hx-ollama2.dev-test.hana-x.ai
  hx-webui-server: hx-webui-server.dev-test.hana-x.ai
  hx-dev-server: hx-dev-server.dev-test.hana-x.ai
  hx-test-server: hx-test-server.dev-test.hana-x.ai
  hx-devops-server: hx-devops-server.dev-test.hana-x.ai
  hx-metrics-server: hx-metrics-server.dev-test.hana-x.ai
  hx-fs-server: hx-fs-server.dev-test.hana-x.ai
  hx-qwebui-server: hx-qwebui-server.dev-test.hana-x.ai
  hx-mcp1-server: hx-mcp1-server.dev-test.hana-x.ai

# FQDN → IP (for reporting/validation only; prefer DNS for runtime)
hx_hosts_ip:
  hx-dc-server.dev-test.hana-x.ai: 192.168.10.2
  hx-ca-server.dev-test.hana-x.ai: 192.168.10.4
  hx-orchestrator-server.dev-test.hana-x.ai: 192.168.10.8
  hx-vectordb-server.dev-test.hana-x.ai: 192.168.10.9
  hx-webui-server.dev-test.hana-x.ai: 192.168.10.11
  hx-dev-server.dev-test.hana-x.ai: 192.168.10.12
  hx-test-server.dev-test.hana-x.ai: 192.168.10.13
  hx-devops-server.dev-test.hana-x.ai: 192.168.10.14
  hx-metrics-server.dev-test.hana-x.ai: 192.168.10.16
  hx-fs-server.dev-test.hana-x.ai: 192.168.10.17
  hx-litellm-server.dev-test.hana-x.ai: 192.168.10.46
  hx-prisma-server.dev-test.hana-x.ai: 192.168.10.47
  hx-sqldb-server.dev-test.hana-x.ai: 192.168.10.48
  hx-ollama1.dev-test.hana-x.ai: 192.168.10.50
  hx-ollama2.dev-test.hana-x.ai: 192.168.10.52
  hx-qwebui-server.dev-test.hana-x.ai: 192.168.10.53
  hx-mcp1-server.dev-test.hana-x.ai: 192.168.10.59

# IP → FQDN (handy for auto-fix tasks)
ip_map:
  "192.168.10.2":  hx-dc-server.dev-test.hana-x.ai
  "192.168.10.4":  hx-ca-server.dev-test.hana-x.ai
  "192.168.10.8":  hx-orchestrator-server.dev-test.hana-x.ai
  "192.168.10.9":  "hx-vectordb-server.dev-test.hana-x.ai"
  "192.168.10.11": "hx-webui-server.dev-test.hana-x.ai"
  "192.168.10.53": "hx-qwebui-server.dev-test.hana-x.ai"
  "192.168.10.12": "hx-dev-server.dev-test.hana-x.ai"
  "192.168.10.13": hx-test-server.dev-test.hana-x.ai
  "192.168.10.14": hx-devops-server.dev-test.hana-x.ai
  "192.168.10.16": hx-metrics-server.dev-test.hana-x.ai
  "192.168.10.17": hx-fs-server.dev-test.hana-x.ai
  "192.168.10.46": hx-litellm-server.dev-test.hana-x.ai
  "192.168.10.47": hx-prisma-server.dev-test.hana-x.ai
  "192.168.10.48": hx-sqldb-server.dev-test.hana-x.ai
  "192.168.10.50": hx-ollama1.dev-test.hana-x.ai
  "192.168.10.52": hx-ollama2.dev-test.hana-x.ai
  "192.168.10.59": hx-mcp1-server.dev-test.hana-x.ai
```

> **Usage:**
>
> * Reference `hx_hosts_fqdn["hx-ollama1"]` when templating configs.
> * Use `ip_map` only for lint/auto-rewrite tasks; do not hardcode IPs in runtime configs.

---

## CI Enforcement: pre-commit hook for FQDN policy

Use a lightweight repo-local hook that blocks introducing `localhost`, `127.0.0.1`, `::1`, or `192.168.10.x` literals. The hook prefers **ripgrep** for speed and falls back to **grep**.

### 1) Add the checker script

Create `scripts/check-fqdn.sh` (make it executable):

```bash
#!/usr/bin/env bash
set -euo pipefail

# Paths to include/exclude
INCLUDE_ROOT="${1:-.}"
# Exclude common build/cache/vendor dirs; extend as needed
EXCLUDES=(
  ".git/**" ".github/**" ".venv/**" "venv/**" "node_modules/**" "dist/**" "build/**" "coverage/**" "__pycache__/**" "*.min.js" "*.lock"
)

# Patterns to forbid (case-insensitive for localhost)
PATTERNS=(
  "\blocalhost\b"
  "\b127\.0\.0\.1\b"
  "\b::1\b"
  "\b192\.168\.10\.[0-9]{1,3}\b"
)

use_rg=0
if command -v rg >/dev/null 2>&1; then
  use_rg=1
fi

if [[ $use_rg -eq 1 ]]; then
  # Build rg globs
  RG_ARGS=("--no-heading" "--hidden" "--follow")
  for g in "${EXCLUDES[@]}"; do RG_ARGS+=("--glob" "!$g"); done
  # Build combined regex (OR)
  IFS='|' read -r -a OR_PAT <<< "${PATTERNS[*]}"
  rg "${OR_PAT[*]}" -nH "${RG_ARGS[@]}" "$INCLUDE_ROOT" || true > /tmp/fqdn_hits.txt
else
  # Fallback to grep -R with excludes
  GREP_ARGS=("-R" "-nH" "--binary-files=without-match" "--exclude-dir=.git" "--exclude-dir=.github" "--exclude-dir=.venv" "--exclude-dir=venv" "--exclude-dir=node_modules" "--exclude-dir=dist" "--exclude-dir=build" "--exclude-dir=coverage" "--exclude=*.min.js" "--exclude=*.lock")
  grep "${GREP_ARGS[@]}" -Ei "$(IFS='|'; echo "${PATTERNS[*]}")" "$INCLUDE_ROOT" || true > /tmp/fqdn_hits.txt
fi

if [[ -s /tmp/fqdn_hits.txt ]]; then
  echo "❌ Forbidden non-FQDN usage detected. Replace with FQDNs/short names (domain: dev-test.hana-x.ai)."
  echo "---"
  cat /tmp/fqdn_hits.txt
  echo "---"
  echo "Tip: Use variables/endpoints defined in group_vars/all; avoid localhost and raw IPs."
  exit 1
fi

exit 0
```

### 2) Add the pre-commit config

Create `.pre-commit-config.yaml` in the repo root:

```yaml
repos:
  - repo: local
    hooks:
      - id: fqdn-policy-enforcer
        name: Enforce FQDN/short-name policy (no localhost / 127.0.0.1 / ::1 / 192.168.10.x)
        entry: bash scripts/check-fqdn.sh .
        language: system
        pass_filenames: false
        stages: [commit, push]
```

### 3) Enable it in the repo

```bash
pipx install pre-commit || pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
# Optional: run across the whole repo now
pre-commit run --all-files
```

> Notes:
>
> * Extend `EXCLUDES` in `scripts/check-fqdn.sh` if your repo has extra generated dirs.
> * The script blocks only your fleet subnet (192.168.10.x). Add other forbidden subnets if needed.
> * If you purposefully need a literal IP in a test fixture, commit an allowlisted sample under a dedicated `tests/fixtures/` path and update the excludes accordingly.

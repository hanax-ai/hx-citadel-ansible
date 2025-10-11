# Changelog

## [Unreleased]

### Changed
- **BREAKING**: Made Redis binding IP configurable via `redis_additional_bind_ip` variable
  - Previous: `redis_bind_interface: "127.0.0.1 192.168.10.48"` (hardcoded)
  - Current: `redis_bind_interface: "127.0.0.1 {{ redis_additional_bind_ip | default(ansible_default_ipv4.address) }}"`
  - **Migration**: Set `redis_additional_bind_ip` variable in your environment-specific vars
  - **Impact**: Improves portability across different network environments
  - **Files affected**: `group_vars/db_nodes.yml`, Redis role template and documentation

- **IMPROVEMENT**: Made PostgreSQL configuration path configurable and version-independent
  - Previous: Hardcoded `/etc/postgresql/16/main/postgresql.conf` path
  - Current: Uses `postgresql_config_path` variable derived from `postgresql_version`
  - **Migration**: No changes required - defaults maintain backward compatibility
  - **Impact**: Supports multiple PostgreSQL versions and distributions
  - **Files affected**: `roles/postgresql/tasks/main.yml`, `roles/postgresql/defaults/main.yml`

### Added
- `redis_additional_bind_ip` variable for environment-specific Redis network binding
- Automatic fallback to `ansible_default_ipv4.address` if no additional IP specified
- Documentation for multi-node Redis binding configuration
- `postgresql_version` variable for PostgreSQL version configuration (default: "16")
- `postgresql_config_path` variable for flexible PostgreSQL config file location
- `roles/postgresql/defaults/main.yml` with configurable PostgreSQL defaults

## Previous Changes
- See git history for earlier changes
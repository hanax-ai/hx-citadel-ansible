# Test Scripts

Shell scripts for testing and validation.

## Scripts

- `test_circuit_breaker.sh` - Circuit breaker validation script
  - Tests circuit breaker behavior (open, half-open, closed states)
  - Validates fast-fail on service unavailability
  - Usage: `./test_circuit_breaker.sh`

## Usage

All scripts should be executable and run from the tests/ directory:

```bash
cd tests
./scripts/test_circuit_breaker.sh
```

## Adding New Scripts

1. Create script in `tests/scripts/`
2. Make executable: `chmod +x scripts/your_script.sh`
3. Document in this README
4. Use FQDNs (not IPs) per project policy

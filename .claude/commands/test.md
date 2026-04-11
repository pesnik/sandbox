Run the sandbox E2E test suite.

Steps:
1. Check if the sandbox container is running: `docker ps --filter name=sandbox --format '{{.Status}}'`
2. If not running, run `make up` and wait for healthy: `until docker inspect --format='{{.State.Health.Status}}' sandbox | grep -q healthy; do sleep 1; done`
3. Run tests: `cd tests && pip install -q -r requirements.txt && pytest -v`
4. Report which tests passed/failed and any errors from `make logs` if failures occurred.

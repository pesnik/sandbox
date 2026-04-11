Build the sandbox Docker image and verify it starts cleanly.

Steps:
1. Run `make build` from the repo root
2. If build fails, read the error carefully — common causes are in CLAUDE.md "Known sharp edges"
3. Run `make ci` to build + start + run full test suite
4. If tests fail, run `make logs` to inspect supervisord/api/mcp logs
5. Report image size: `docker images pesnik/sandbox --format '{{.Size}}'`

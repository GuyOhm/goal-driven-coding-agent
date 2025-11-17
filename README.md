## Sandbox MCP Servers

Two Docker images provide sandboxed MCP servers:

- `containers/filesystem/Dockerfile` – exposes file operations (`sandbox_*` tools)
- `containers/executor/Dockerfile` – exposes execution tools for shell/python commands and comes with `pytest` preinstalled so benchmark suites can run without extra setup.

Launch both via Docker Compose:

```bash
docker compose -f containers/docker-compose.mcp.yaml up --build
```

Each container shares the host `sandbox_volumes` directory and listens on ports `7101` (filesystem) and `7102` (executor) via the `streamable-http` MCP transport. Configure environment variables to customize behavior:

| Variable | Description | Default |
| --- | --- | --- |
| `SANDBOX_ROOT` | Mounted sandbox path inside container | `/sandbox` |
| `TRANSPORT` | MCP transport (`stdio`, `sse`, `streamable-http`) | `streamable-http` |
| `HOST` / `PORT` | Bind address for SSE/HTTP | `0.0.0.0` / `710x` |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `PYTHON_BINARY` (executor) | Interpreter used for scripts | `python` |
| `TIMEOUT_SECONDS` (executor) | Default execution timeout | `300` |

The servers run `goal_driven_coding_agent.mcp.servers.filesystem_server` and `goal_driven_coding_agent.mcp.servers.executor_server`, exposing the same MCP interface the coding agent will consume.

### Manual lifecycle

Before running the CLI, start the Docker Compose stack yourself:

```bash
docker compose -f containers/docker-compose.mcp.yaml up --build
```

The agent assumes the filesystem and executor MCP servers are reachable at `http://127.0.0.1:7101/mcp` and `http://127.0.0.1:7102/mcp`. Override these URLs with `--filesystem-server-url` / `--executor-server-url` if you expose them differently. When you’re done, tear the stack down manually:

```bash
docker compose -f containers/docker-compose.mcp.yaml down
```

### Run manifest & tracing

Every agent run emits `run_manifest.json` inside the run’s sandbox directory (e.g., `sandbox_volumes/run-*/run_manifest.json`). The manifest captures:

- Goal, model, timestamps, iteration count, success flag
- LLM invocations (system prompt preview, input preview, response summary, token usage)
- MCP tool calls (tool name, server, arguments, status, output/error preview)
- Any non-fatal cleanup errors encountered during shutdown

The CLI logs the manifest path on completion. Use tools like `jq` to inspect the timeline or ship the JSON to your preferred observability stack.

## Benchmark Mode

Run the agent against the Polyglot Benchmark exercises with the `--benchmarks` flag. The CLI reads each exercise’s `.docs/*.md` instructions, sets an appropriate goal, and executes the agent until every test file passes. The instructions, canonical solution stub, and official tests are injected into the LLM’s initial prompt as read-only context so it starts each attempt with full awareness of the requirements and current code.

- `python -m goal_driven_coding_agent.cli.main --benchmarks` – solve every exercise in `benchmarks/python/exercises/practice`
- `python -m goal_driven_coding_agent.cli.main --benchmarks --benchmarks-limit 3` – run only the first three exercises

When running benchmarks, a unique `run_id` is generated per exercise (or prefixed by `--run-id` when provided). Each iteration still produces a sandbox directory and run manifest just like a single-goal invocation.


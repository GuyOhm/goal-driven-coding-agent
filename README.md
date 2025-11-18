# Goal-Driven Coding Agent

This project contains a simple, fully sandboxed, goal-driven coding agent built using the OpenAI Agents SDK. The agent is designed to solve coding challenges by iteratively writing code, running tests, and refining its approach based on the results.

## Features

- **Autonomous Agentic Loop:** The agent autonomously decides which tools to use and when its task is complete, driven by a clear goal.
- **OpenAI Agents SDK:** Built on the official OpenAI Agents SDK for managing agentic workflows.
- **Sandboxed Environment:** All file operations and code execution occur within a secure, containerized environment using Docker.
- **MCP (Model Context Protocol):** Leverages MCP for communication between the agent and its sandboxed tools, including a filesystem manager and a code executor.
- **Benchmarking:** Includes a suite for running the agent against Polyglot Benchmark exercises to measure performance.

---

## Design and Architecture Report

### 1. Agent Design

The agent's core logic is built around the `openai-agents` library, which provides the main `Runner.run` loop. The agent operates on a simple, iterative "implement-test-refine" cycle:

1.  **Understand the Goal:** The agent is given a high-level goal, which includes the path to a solution file and a test file.
2.  **Implement:** The agent reads the relevant files and writes an initial implementation.
3.  **Test:** It executes the provided `pytest` command within the sandboxed `executor` tool.
4.  **Refine:** It analyzes the `exit_code` and `stdout` from the test run.
    - If the `exit_code` is `0`, it concludes the task is complete and terminates its loop.
    - If the `exit_code` is not `0`, it analyzes the errors and attempts to fix them in the next iteration.

This entire loop is autonomous; the agent itself decides whether to continue iterating or to finish, based on the results of its actions.

### 2. Sandboxing

Security and safety are achieved through a container-based sandboxing approach using Docker and Docker Compose. The environment consists of two main services defined in `containers/docker-compose.mcp.yaml`:

-   **`filesystem-server`:** A container that has access to a dedicated, isolated directory (`sandbox_volumes`). It exposes file management tools (read, write, list files) over an MCP endpoint. The agent can only operate within this directory, preventing any access to the host filesystem.
-   **`executor-server`:** A second container that provides code execution capabilities, also restricted to the same sandbox directory. It exposes a `sandbox_run_command` tool that can execute shell commands, such as running `pytest`.

This architecture ensures that the agent's entire workspace—both for file manipulation and code execution—is strictly confined to the `sandbox_volumes` directory, providing a secure and isolated environment.

### 3. MCP Integration

The agent communicates with its sandboxed tools using the Multi-Capability Protocol (MCP). The two MCP servers listen on `http://127.0.0.1:7101` (filesystem) and `http://127.0.0.1:7102` (executor). The agent, via the OpenAI Agents SDK, connects to these endpoints to discover and invoke the available tools.

-   **Filesystem Tools:** The agent uses tools like `sandbox_read_file` and `sandbox_write_file` to interact with the code.
-   **Executor Tool:** The agent uses the `sandbox_run_command` tool to execute the `pytest` suite and verify its implementation.

The structured input and output of these tools (e.g., JSON containing `exit_code`, `stdout`, `stderr`) is critical for the agent's ability to analyze the results of its actions.

### 4. Benchmark Learnings and Outcomes

The agent was tested against the "Affine Cipher" challenge from the Polyglot Benchmark. The process provided several key insights:

-   **Initial Failures with `gpt-4o-mini`:** The initial runs with the `gpt-4o-mini` model were unsuccessful. The agent made progress but would often get stuck in a "regression loop"—a fix for one part of the problem would break previously working code, and the agent was unable to recover within the 10-turn limit.
-   **Prompt Ambiguity:** The initial goal prompt provided two different ways to run `pytest`, which caused the agent to become confused and waste turns on debugging its own test commands.
-   **Path to Success:** Success was achieved by making two key changes:
    1.  **Simplifying the Prompt:** The goal prompt was simplified to provide a single, unambiguous `pytest` command. This eliminated the agent's confusion.
    2.  **Using a More Powerful Model:** Switching to the `gpt-4o` model provided the necessary reasoning capability to overcome the logical complexity of the coding challenge. The more powerful model did not get stuck in a regression loop and was able to implement the correct logic efficiently.
-   **Final Outcome:** With the refined prompts and the `gpt-4o` model, the agent was able to **solve the "Affine Cipher" benchmark in a single attempt**, demonstrating a clear and effective workflow. The success reporting mechanism was also debugged to correctly reflect the outcome of the run.

---

## Setup and Installation

Follow these steps to set up and run the agent.

**Prerequisites:**
- Python 3.11+
- [Docker](https://www.docker.com/get-started)
- `uv` (or `pip`) for Python package management

**1. Clone the Repository:**
```bash
git clone git@github.com:GuyOhm/goal-driven-coding-agent.git
cd goal-driven-coding-agent
```

**2. Set Up Python Environment:**
Create and activate a virtual environment.
```bash
python -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies:**
```bash
uv pip install -r requirements.txt
```

**4. Configure Environment Variables:**
Copy the example `.env` file and add your OpenAI API key.
```bash
cp .env.example .env
# Now, edit .env and add your OPENAI_API_KEY
```

**5. Start the Sandbox Environment:**
Launch the sandboxed MCP servers using Docker Compose.
```bash
docker compose -f containers/docker-compose.mcp.yaml up --build -d
```
This will start the filesystem and executor containers in the background.

---

## How to Run the Agent

### Run a Single Goal

You can give the agent any coding task using the `--goal` argument.

```bash
uv run python main.py --goal "Implement a function in `test.py` that returns 'hello world'"
```

### Run the Benchmark Suite

To run the agent against the entire Polyglot Benchmark suite:
```bash
uv run python main.py --benchmarks
```

To limit the run to the first `N` benchmarks:
```bash
uv run python main.py --benchmarks --benchmarks-limit 3
```

To use a specific model (like `gpt-4o`):
```bash
uv run python main.py --benchmarks --model gpt-4o
```

### Stopping the Sandbox

When you are finished, stop the Docker containers:
```bash
docker compose -f containers/docker-compose.mcp.yaml down
```

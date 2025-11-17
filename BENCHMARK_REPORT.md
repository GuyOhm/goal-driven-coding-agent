# Benchmark Report: Polyglot Benchmark coding challenges

This report details the results, execution traces, and key learnings from running the goal-driven coding agent on the Polyglot Benchmark in Python.

## Final Benchmark Results

The agent was run against the entire suite of 34 Python benchmark exercises.

-   **Overall Pass Rate:** 33/34 challenges passed
-   **Success Score:** **97%**

The final benchmark run was achieved using the `gpt-5-mini` model.

-   **Model:** `gpt-5-mini`
-   **Link to Final Code Solutions:** [code solutions](./sandbox_volumes/run-20251117T171840Z-7d5cffb0-affine-cipher/benchmarks/python/exercises/practice/)
-   **Link to Execution Traces:** [run_manifest files](./sandbox_volumes/)

---

## Development Journey and Key Learnings

The process of achieving a successful run involved several iterations and provided significant insights into agent design, prompt engineering, and model capabilities.

### 1. Initial State (Model: `gpt-4o-mini`)

The initial attempts using `gpt-4o-mini` were unsuccessful. The agent consistently failed to solve the problem within the 10-turn limit.

-   **Core Issue:** The agent would make initial progress but get stuck in a "regression loop." When attempting to fix one bug (e.g., handling numbers), it would re-introduce other bugs (e.g., incorrect spacing), and was unable to recover.
-   **Prompt-Following:** The agent also struggled with complex or ambiguous prompts. An initial prompt that provided two different ways to run `pytest` caused confusion and wasted turns.

This demonstrated that for logically complex tasks requiring precise code modification, `gpt-4o-mini` lacked the reasoning capacity to avoid simple regressions, even with detailed instructions.

### 2. Intermediate State (Model: `gpt-4o`)

To address the failures of the smaller model, we made two key changes:

1.  **Simplified the Prompts:** The goal prompt was simplified to provide a single, unambiguous `pytest` command. The agent's system instructions were also made more direct, focusing on a clear workflow.
2.  **Upgraded the Model:** We switched to the more powerful `gpt-4o` model.

-   **Outcome:** These changes were immediately effective. The `gpt-4o` agent solved the challenge on its first attempt. It correctly followed the simplified workflow and did not get stuck in a regression loop. This highlighted that a more capable model can overcome logical hurdles that a smaller model cannot.

### 3. Final State (Model: `gpt-5-mini`)

The final tests were run with `gpt-5-mini`, which represents a newer generation of highly efficient models.

-   **Outcome:** `gpt-5-mini` also solved most of the challenges successfully and efficiently. It demonstrated the ability to follow the simplified workflow flawlessly, achieving the goal with a good balance of performance and (assumed) lower cost compared to the larger `gpt-4o` model.

---

## Summary of Learnings

1.  **Prompt Engineering is Critical:**
    -   **Simplicity and Clarity:** Simple, direct, and unambiguous prompts are far more effective than complex ones with many rules. Giving the agent a single, clear command for testing was more effective than providing multiple options.
    -   **Guiding with Tool Outputs:** Instructing the agent to rely on the `exit_code` from the test execution tool was a robust way to guide its main loop (i.e., "if exit_code is 0, you are done").

2.  **Model Choice Matters:**
    -   **`gpt-4o-mini`:** Best for simple, low-cost tasks. It struggled with the logical complexity and state management required for this benchmark.
    -   **`gpt-4o`:** A powerful and reliable choice. It was able to solve the problem easily once the prompts were clear, but at a higher operational cost.
    -   **`gpt-5-mini`:** Appears to strike an excellent balance between the reasoning capabilities of a high-end model and the efficiency of a smaller one, making it a strong candidate for this type of goal-driven coding task.

3.  **Agent Design:**
    -   The final agent design, which uses a simple "implement-test-refine" loop guided by a clear `exit_code` signal, proved to be the most effective architecture. Attempts to add complex "guardrail" instructions to the prompt were less effective than simply using a more capable model with a clear goal.

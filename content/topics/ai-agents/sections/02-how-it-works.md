# How It Works
1. **User request**: agent receives a high-level goal.
2. **Planning**: LLM decomposes the goal into sub-tasks.
3. **Tool selection**: LLM chooses the appropriate tool (API, function, code).
4. **Parameter generation**: LLM generates tool parameters based on context.
5. **Execution**: tool is executed in a sandboxed environment.
6. **Observation**: agent observes the result and decides next step.
7. **Completion**: agent determines the goal is achieved and returns the result.

Components: LLM brain, tool registry, execution sandbox, memory store, planner.

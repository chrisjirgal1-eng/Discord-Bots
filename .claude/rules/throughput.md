# Throughput

Advisory rule. Always loaded. How to move fast without making mistakes.
The goal is fast AND correct. Fast-but-wrong is slower than steady-and-right, because rework
costs more than the time it saved. There is no magic switch. These habits are the speed.

## The five speed habits

1. Parallelize independent work.
   Batch independent tool calls into one message instead of a slow staircase of round trips.
   Fan out independent subtasks with the Workflow tool or parallel subagents.
   This is the biggest wall-clock win. Only serialize when step B needs step A's result.

2. Route by altitude (see model-routing.md).
   Fast model for search, retrieval, and bulk edits. Big model for planning and error recovery.
   A model 30 percent slower compounds across many tool calls and can double a multi-step run.

3. Use /fast for latency on the main loop.
   It is Opus at higher output speed, not a smaller model, so no quality drop. Use it for speed,
   not savings.

4. Keep context lean and cached (see token-efficiency.md).
   A stable prompt prefix stays cached and returns fast. /clear between unrelated tasks.
   Do not reread a file already in context.

5. Act when you have enough.
   Do not re-derive settled facts or re-survey options already decided. Decide and move.
   Plan only when scope is unclear or the change spans many files. Skip the plan for a clear small fix.

## Speed never skips the gate

The "no mistakes" part is not a separate step that slows you down. It is the gate (verification.md):
route the quality verdict to a fresh subagent reading the raw artifact. Cheap relative to rework.
Type-A facts (tests pass, build exits 0) self-check. Type-B judgments go to a separate reviewer.

## The honest rate

Best sustainable rate = parallel where independent, right-sized model per task, cached context,
one verification pass before shipping. That is faster over a run than racing and redoing.

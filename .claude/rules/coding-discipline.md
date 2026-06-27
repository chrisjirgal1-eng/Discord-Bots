# Coding discipline

Advisory rule. Always loaded. Behavioral guidelines to reduce common coding mistakes.
Tradeoff: these bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them, do not pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what is confusing. Ask.

## 2. Simplicity first

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that was not requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask: would a senior engineer say this is overcomplicated? If yes, simplify.

## 3. Surgical changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Do not improve adjacent code, comments, or formatting.
- Do not refactor things that are not broken.
- Match existing style, even if you would do it differently.
- If you notice unrelated dead code, mention it, do not delete it.

When your changes create orphans:
- Remove imports, variables, and functions that YOUR changes made unused.
- Do not remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the request.

## 4. Goal-driven execution

Define success criteria. Loop until verified.

Turn tasks into verifiable goals:
- "Add validation" becomes "write tests for invalid inputs, then make them pass".
- "Fix the bug" becomes "write a test that reproduces it, then make it pass".
- "Refactor X" becomes "ensure tests pass before and after".

For multi-step tasks, state a brief plan, each step with its verify check.
Strong success criteria let me loop independently. Weak criteria need constant clarification.

## Working

These are working if: fewer unnecessary changes in diffs, fewer rewrites from
overcomplication, and clarifying questions come before implementation, not after mistakes.

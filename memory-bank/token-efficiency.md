# Token Efficiency

How to conserve tokens and cut cost. Ranked by impact. Read on demand.

## The one principle

Context is the constraint. Every file read, command output, and message stays in
the window and gets re-billed every turn. Performance drops as the window fills.
Keep the window small and the repeated parts cached.

## Ranked moves

1. Prompt caching. Biggest single win, up to 90%. Repeated context (system prompt,
   big files, CLAUDE.md) caches. First write 1.25x, every reread 10% of input price.
   Example: 50k-token system prompt over 500 req/day dropped $75/day to $7.69/day.
   In Claude Code set ENABLE_PROMPT_CACHING_1H for long sessions.
2. /clear between unrelated tasks. Free. The "kitchen sink session" is the top waste.
   A fresh session with a sharp prompt beats a long polluted one almost every time.
3. Subagents for anything that reads many files. They burn their own window and
   return a short summary. The files they read never touch the main window.
4. Be specific. Vague prompts cost the most. "src/auth/token.ts line 42, null check
   wrong" beats "fix the login bug". Specificity is a token strategy.
5. Plan before coding on multi-file work (Shift+Tab). Cuts trial-and-error waste.
   Skip it for one-line fixes, it adds overhead there.
6. Keep CLAUDE.md under 200 lines. Loads every session, never evicted. Bloat means
   you pay every turn AND rules get ignored. Cut any line that would not cause a mistake.
7. Trim output verbosity. Kill preambles, closings, restating the question.
   Reported up to 63% word cut, honest independent tests show 4-17% on output tokens.

## Command cheat sheet

| Command | Does | When |
| --- | --- | --- |
| /clear | Wipes context | Between unrelated tasks |
| /compact <focus> | Summarizes, keeps key stuff | Near the limit, mid-task |
| /context | Shows where tokens go | Diagnose bloat |
| /btw | Side question, never enters history | Quick checks |
| /recap | Resume summary, no replay | Picking back up |
| subagent | Isolated context | Heavy reads or research |

## Expected result

Compounded, most people see 40-70% reduction. Up to 85-90% with caching dialed in.

## Sources

- Claude Code best practices: https://code.claude.com/docs/en/best-practices
- Anthropic prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- claude-token-efficient: https://github.com/drona23/claude-token-efficient

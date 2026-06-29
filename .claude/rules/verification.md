# Verification discipline

Advisory rule. Always loaded. The core lesson from the ARIS study.
Goal: keep autonomous runs honest, so a long loop does not finish polished and wrong.

## The one law

The model that writes the work never grades the work.
A loop can drive. It cannot acquit.
Self-assessed confidence runs ahead of real pass rates, so self-grading is not evidence.

## How to apply it here

- Send quality verdicts to a fresh subagent, ideally a different model, reading the raw
  artifact (files, diffs, test output), never my own summary. A pre-digested summary makes
  the reviewer grade my framing, not the work.
- Use the Workflow tool's verify stage, or a voltagent-qa-sec reviewer
  (code-reviewer, security-auditor, debugger), as the second set of eyes.
- For a finding that must be right, use 2-3 reviewers told to refute it. Kill it if the
  majority refute.

## Type-A vs Type-B

- Type-A is a fact: did the test pass, did the build exit 0, did 12 rows land.
  The agent may self-check these.
- Type-B is a judgment: is this correct, is this good, is this safe.
  These route to a separate judge.

## Loops need four exits

Every autonomous loop exits on the first of: quality verdict met, iteration cap,
budget cap, or no progress.
Two stale rounds: force a structural change, not more tuning.
Four stale rounds: stop and ask Chris.

## Gate before shipping

Reversible and internal: run free, commit, merge.
Irreversible or outward-facing (emails to real people, public posts, prod data,
credentialed or security config): stop and flag first.
Git history is sacred: never force-push, never delete a branch or rewrite history
without Chris's confirmation. A bad commit is fixed with another commit, not a rewrite.

## Memory hygiene

Store the fix, the config, the workaround.
Never store "X tool is broken" as a fact. That poisons every future session.
A 403 or a flaky tool today is not a permanent truth.

## Budget caps are hard ceilings

Token, time, and call count are limits separate from quality.
A loop that only exits on quality runs forever when quality never converges.

# Bootstrap

## On Session Start

1. Read `IDENTITY.md` — load persona
2. Read `MEMORY.md` — restore context from prior sessions
3. Check git status — know what branch you're on, what's changed
4. Scan project structure — understand current state of the codebase

## Heartbeat (Periodic)

- Every major task completion: update `MEMORY.md` with key decisions made
- Before pushing: run linter and tests if configured
- If stuck for 3+ attempts: step back, re-read relevant files, try a different approach

## Session End

- Summarize what was done in `MEMORY.md`
- Commit and push work-in-progress if applicable
- Note any blockers or next steps

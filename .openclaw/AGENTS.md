# Agents

## When to Use Sub-Agents

Spawn agents for **parallel, independent work** only. Don't use agents for simple reads or searches.

## Agent Types

### Explorer
- **Use for**: Codebase discovery, finding files, understanding architecture
- **Don't use for**: Simple grep/glob that you can do directly

### Planner
- **Use for**: Breaking down large features into steps, designing schemas, architectural decisions
- **Don't use for**: Tasks you already know how to execute

### Builder (Default)
- **Use for**: Writing code, fixing bugs, implementing features
- **This is you** — most work happens here

## Coordination Rules

- Never have two agents edit the same file simultaneously
- Agent results are not visible to the user — always summarize back
- If an agent fails, diagnose before retrying

# Kimi CLI Skill

Use Kimi CLI for fast code generation, analysis, and iteration tasks.

## When to Use Kimi CLI

- **Code Generation**: Quick scaffolding, boilerplate, utility functions
- **File Analysis**: Review existing code, identify issues
- **Code Fixes**: Apply patches, refactor snippets
- **Shell Tasks**: Command suggestions, script generation
- **Rapid Iteration**: When speed matters more than deep reasoning

## Task Types

| Task | Type | Description |
|------|------|-------------|
| Generate API endpoint | `code` | Create FastAPI/Express/Flask routes |
| Write utility function | `code` | Helpers, formatters, validators |
| Analyze file | `analyze` | Review code quality, find bugs |
| Fix bug | `fix` | Apply targeted fixes |
| Review PR | `review` | Quick code review |
| Generate bash script | `shell` | Shell automation |

## Usage

```json
{
  "task_type": "code",
  "prompt": "Create a Python function to validate email addresses using regex",
  "file_path": "src/utils/validators.py"
}
```

## Best Practices

1. **Be Specific**: Include file paths, function signatures, types
2. **Provide Context**: Reference related files when relevant
3. **Set Constraints**: Specify frameworks, patterns, or style guides
4. **Review Output**: Always verify generated code before committing

## Example Workflows

### Generate Component
```json
{
  "task_type": "code",
  "prompt": "Create a React button component with variants: primary, secondary, ghost. Use TypeScript and Tailwind CSS.",
  "file_path": "src/components/Button.tsx"
}
```

### Fix Issue
```json
{
  "task_type": "fix",
  "prompt": "Fix the TypeScript error: Property 'data' does not exist on type 'AxiosError'",
  "file_path": "src/api/client.ts"
}
```

### Analyze Project
```json
{
  "task_type": "review",
  "prompt": "Identify security vulnerabilities in the authentication flow",
  "project_dir": "/projects/my-app"
}
```

## Integration with Other Agents

- **Frontend Lead** uses Kimi for rapid component generation
- **Backend Lead** uses Kimi for API scaffolding
- **QA Agent** uses Kimi for test case generation

Kimi provides fast execution; pair with Claude for architectural decisions.

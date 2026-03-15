# Claude CLI Skill

Use Claude CLI for architectural decisions, design, and complex planning tasks.

## When to Use Claude CLI

- **Architecture Design**: System structure, tech stack decisions
- **UI/UX Design**: Component hierarchies, design systems
- **API Design**: Endpoint structure, data contracts
- **Database Design**: Schema design, relationships, indexing
- **Project Planning**: Task breakdown, estimates, dependencies
- **Deep Code Review**: Architecture, patterns, maintainability

## Task Types

| Task | Type | Description |
|------|------|-------------|
| Design system architecture | `architecture` | High-level structure, services, data flow |
| Create component hierarchy | `frontend` | React component trees, state management |
| Define design system | `design` | Colors, typography, spacing, components |
| Design REST/GraphQL API | `api` | Endpoints, schemas, authentication |
| Design database schema | `database` | Tables, relations, migrations |
| Plan project phases | `planning` | Milestones, tasks, estimates |
| Architecture review | `review` | Deep technical review |

## Usage

```json
{
  "task_type": "architecture",
  "prompt": "Design a scalable e-commerce backend with microservices: catalog, cart, orders, payments. Use Node.js, PostgreSQL, Redis."
}
```

## Best Practices

1. **Provide Context**: Business requirements, constraints, scale expectations
2. **Ask for Trade-offs**: Get multiple options with pros/cons
3. **Request Diagrams**: Ask for ASCII/text diagrams of architecture
4. **Iterate**: Break complex designs into phases

## Example Workflows

### System Architecture
```json
{
  "task_type": "architecture",
  "prompt": "Design a real-time chat application architecture. Requirements: 100k concurrent users, message persistence, read receipts, typing indicators."
}
```

### Component Hierarchy
```json
{
  "task_type": "frontend",
  "prompt": "Design a dashboard component hierarchy for an analytics app. Include: sidebar navigation, data tables, charts, filters, export functionality."
}
```

### API Design
```json
{
  "task_type": "api",
  "prompt": "Design RESTful API for a todo app with: projects, tasks, labels, due dates, priorities. Include auth and pagination."
}
```

### Database Schema
```json
{
  "task_type": "database",
  "prompt": "Design PostgreSQL schema for a social media app: users, posts, comments, likes, follows, notifications. Include indexes for performance."
}
```

### Project Planning
```json
{
  "task_type": "planning",
  "prompt": "Break down building a full-stack SaaS app into phases. Include: auth, billing, core features, admin panel. Estimate each phase."
}
```

## Integration with Other Agents

- **CEO Agent** uses Claude for strategy and planning
- **CTO Agent** uses Claude for architecture decisions
- **Design Lead** uses Claude for design systems
- **Tech Lead** uses Claude for API and database design

Claude provides depth and reasoning; pair with Kimi for rapid implementation.

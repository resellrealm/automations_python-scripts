# Full-Stack App Development Skill

Build complete web applications with modern tech stack.

## Tech Stack (Default)

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend | Next.js API Routes / Express / FastAPI |
| Database | PostgreSQL (via Supabase or local) |
| Auth | NextAuth.js / Supabase Auth |
| Deployment | Vercel / Railway / VPS |

## Development Workflow

### Phase 1: Planning (Claude)
1. CEO/PM defines app requirements
2. CTO designs system architecture
3. Design Lead creates wireframes
4. Output: Architecture doc, task breakdown

### Phase 2: Setup (Kimi)
1. Initialize Next.js project
2. Setup Tailwind, TypeScript config
3. Setup database connection
4. Output: Working project scaffold

### Phase 3: Backend (Kimi + Claude)
1. Design API endpoints (Claude)
2. Implement database models (Kimi)
3. Build API routes (Kimi)
4. Add authentication (Kimi)
5. Output: Working backend

### Phase 4: Frontend (Claude + Kimi)
1. Design component hierarchy (Claude)
2. Create design system (Claude)
3. Build UI components (Kimi)
4. Implement pages (Kimi)
5. Wire up API (Kimi)
6. Output: Working frontend

### Phase 5: Polish (Both)
1. Add error handling
2. Loading states
3. Responsive design
4. SEO, meta tags
5. Output: Production-ready app

### Phase 6: QA & Deploy (QA Agent)
1. Test all features
2. Fix bugs
3. Performance check
4. Deploy
5. Output: Live app

## Coordination Rules

1. **API Contract First**: Backend and frontend agree on API spec before coding
2. **Component Library**: Shared UI components in `components/ui/`
3. **Type Safety**: Share TypeScript types between frontend and backend
4. **Environment Config**: Use `.env.local` for secrets, `.env.example` for template

## Project Structure

```
my-app/
├── src/
│   ├── app/                 # Next.js app router
│   │   ├── (auth)/          # Auth group
│   │   ├── api/             # API routes
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/              # Shared UI components
│   │   └── features/        # Feature-specific components
│   ├── lib/
│   │   ├── db.ts            # Database client
│   │   ├── auth.ts          # Auth config
│   │   └── utils.ts         # Helpers
│   └── types/
│       └── index.ts         # Shared types
├── prisma/                  # Database schema (if using Prisma)
├── public/                  # Static assets
├── .env.local
├── next.config.js
├── tailwind.config.ts
└── package.json
```

## Example Ticket Flow

**Ticket**: "Build a todo app with projects and labels"

1. **CEO** creates ticket, assigns to CTO
2. **CTO** (Claude): Designs architecture, API spec
   - Creates sub-tickets for frontend, backend
3. **Backend Lead** (Kimi):
   - Sets up Next.js project
   - Creates Prisma schema
   - Implements `/api/todos`, `/api/projects`
4. **Frontend Lead** (Claude + Kimi):
   - Designs UI mockups
   - Builds components: TodoList, ProjectSidebar
   - Implements pages
5. **QA Agent**: Tests, files bugs
6. **Deploy**: Push to Vercel

## Common Patterns

### CRUD Operations
```typescript
// API route pattern
GET    /api/items       # List all
POST   /api/items       # Create
GET    /api/items/[id]  # Get one
PATCH  /api/items/[id]  # Update
DELETE /api/items/[id]  # Delete
```

### Form Handling
```typescript
// Use React Hook Form + Zod for validation
const form = useForm<FormData>({
  resolver: zodResolver(schema)
})
```

### Data Fetching
```typescript
// Use SWR or TanStack Query
const { data, error } = useSWR('/api/items', fetcher)
```

# Development Roadmap

**Project Type:** Internal Business Tool Boilerplate  
**Target Scale:** Small team (< 50 users)  
**Compliance:** GDPR  
**Integration:** Webhooks + Batch file processing  
**Users:** Junior developers with AI coding assistants  
**Deployment:** Dockerized

---

## Current State ✅

- JWT Authentication with refresh tokens
- Admin role-based access (basic)
- Comprehensive audit logging
- **Soft delete system with Trash/Recycle bin**
- Auto database migrations on startup
- File upload infrastructure
- Email integration (SMTP)
- Background job processing (Celery)
- API rate limiting
- Environment-aware status bar

---

## Phase 1: Data Safety & Compliance

### 1.1 Soft Deletes System ✅ **IMPLEMENTED**
**Priority:** HIGH | **Effort:** Medium | **Timeline:** Week 1 | **Status:** Complete

Replace hard deletes with soft delete pattern:
- ✅ Add `deleted_at` timestamp to base model (`SoftDeleteMixin`)
- ✅ Global query filter to exclude deleted records by default
- ✅ Admin "Trash" view with restore/purge functionality
- ✅ Manual purge only (no auto-purge per decision)
- ✅ Integration with existing audit logging

**Files created/modified:**
- `backend/app/models/base.py` - Added `SoftDeleteMixin`
- `backend/app/models/user.py` - Applied mixin
- `backend/app/models/task.py` - Applied mixin
- `backend/app/api/deps.py` - Added deleted filter
- `backend/app/services/trash.py` - Trash management service
- `backend/app/api/api_v1/endpoints/trash.py` - Trash API endpoints
- `backend/app/schemas/trash.py` - Trash schemas
- `frontend/src/pages/Trash.tsx` - Trash management UI
- `frontend/src/pages/Tasks.tsx` - Updated delete to use AlertDialog

---

### 1.2 GDPR Compliance Module ⏸️ **ON HOLD**
**Priority:** MEDIUM | **Effort:** Medium | **Timeline:** TBD | **Status:** Deferred

GDPR-required features for data subjects. **Deferred** until more business entities with personal data are added to the system.

**Prerequisites for implementation:**
- Clear definition of what constitutes personal data per entity
- Decision on audit log retention (anonymize vs delete)
- Data export format (JSON/PDF/both)
- Self-service vs admin-controlled workflow

**Planned features when implemented:**
- **Data Export:** Download all personal data as JSON/ZIP
- **Right to Erasure:** Request account deletion (with audit trail)
- **Privacy Policy Tracking:** Versioned policy acceptance
- **Data Retention:** Automated enforcement of retention policies
- **Consent Management:** Granular consent tracking

**Files to create:**
- `backend/app/services/gdpr.py` - Export/erasure logic
- `backend/app/api/api_v1/endpoints/gdpr.py` - GDPR endpoints
- New: Privacy settings page
- New: Data export download

---

## Phase 2: Access Control

### 2.1 Granular RBAC System 📝 **PLANNED**
**Priority:** HIGH | **Effort:** High | **Timeline:** Week 3-4 | **Status:** Ready for implementation

Hierarchical RBAC with component-scoped roles and tree-based hierarchy.

**Architecture:**
- **Combined roles**: Union of permissions across multiple roles per user
- **Tree hierarchy**: Multi-level manager-subordinate relationships
- **Component-scoped**: Roles apply to specific components (tasks, users, etc.)
- **Explicit permissions**: No default roles, no admin bypass
- **DB queries**: Real-time permission checks

**Database Schema:**
```
users: id, manager_id, ... (self-referential hierarchy)
roles: id, component, name, permissions (JSON)
user_roles: user_id, role_id
```

**Permission Structure (per component):**
```json
{
  "create": "own|subordinates|all|null",
  "read": "own|subordinates|all|null",
  "update": "own|subordinates|all|null",
  "delete": "own|subordinates|all|null"
}
```

**Example Tasks Component Roles:**
- **Tasks: User** → CRUD own tasks only
- **Tasks: Manager** → CRUD own + subordinates' tasks
- **Tasks: Admin** → CRUD any task

**Key Features:**
- Recursive hierarchy traversal (manager sees all levels below)
- Permission union (user with multiple roles gets broadest permissions)
- Resource-level filtering (query only accessible records)
- UI permission guards (hide inaccessible components)
- Admin management interface (roles, assignments, hierarchy)

**Implementation Plan:** See `/docs/rbac-implementation-plan.md`

**Files:**
- Backend: Role/UserRole models, RBAC service, permission dependencies, admin API
- Frontend: usePermission hook, PermissionGuard component, Admin RBAC UI

**Estimated:** 4-6 days (2-3 backend, 2-3 frontend)
- **Manager:** Can manage users in their scope, view reports
- **User:** Standard access to own data
- **Viewer:** Read-only access

**Permission Examples:**
- `users.view_all` vs `users.view_own`
- `tasks.manage_all` vs `tasks.manage_own`
- `audit.view` (admin only)
- `data.export` (manager+)

**Files to create:**
- `backend/app/models/role.py`
- `backend/app/core/permissions.py` - Permission decorators
- `backend/app/api/deps.py` - Permission dependencies
- Frontend permission hooks/components

---

## Phase 3: Integration Layer

### 3.1 Webhook System
**Priority:** MEDIUM | **Effort:** Medium | **Timeline:** Week 5

Event-driven integration for external systems:

**Features:**
- Webhook subscription management (URL, events, secret)
- Event types: user.created, user.updated, task.created, task.updated, etc.
- HMAC signature verification
- Retry logic with exponential backoff (max 5 attempts)
- Delivery logs and debugging UI
- Webhook testing tool (send test payload)

**Architecture:**
- Async delivery via Celery
- Idempotency key support
- Circuit breaker pattern for failing endpoints

**Files to create:**
- `backend/app/models/webhook.py`
- `backend/app/services/webhook.py` - Delivery logic
- `backend/app/api/api_v1/endpoints/webhooks.py`
- New: Webhook management UI

---

### 3.2 Batch File Processing
**Priority:** MEDIUM | **Effort:** Medium | **Timeline:** Week 6

Handle bulk data operations via file upload:

**Features:**
- Upload → Queue → Process pipeline
- Supported formats: CSV, Excel (.xlsx)
- Progress tracking (WebSocket or polling)
- Row-level validation with error reporting
- Downloadable error reports
- Import templates (example files)

**Use Cases:**
- Bulk user import
- Bulk task creation
- Data migration from legacy systems
- Report generation and export

**Files to create:**
- `backend/app/services/batch_processor.py`
- `backend/app/api/api_v1/endpoints/batch.py`
- New: Batch upload UI with progress
- New: Import templates

---

## Phase 4: Developer Experience

### 4.1 Comprehensive Testing Suite
**Priority:** HIGH | **Effort:** Medium | **Timeline:** Week 4

Ensure reliability for junior developers:

**Backend Tests:**
- Unit tests for all service functions
- API integration tests (pytest + httpx)
- Authentication flow tests
- Permission/authorization tests
- Database model tests
- Test coverage target: 80%+

**Frontend Tests:**
- Component tests with Vitest + React Testing Library
- Hook tests
- Integration tests for main flows
- E2E tests with Playwright:
  - Login/logout flow
  - CRUD operations
  - Admin functions
  - File uploads

**Test Infrastructure:**
- Factory Boy for test data
- Database rollback per test
- Mock email/webhook services
- GitHub Actions CI/CD pipeline

**Files to create:**
- `backend/tests/factories.py`
- `backend/tests/test_*.py` (expand coverage)
- `frontend/src/**/*.test.tsx`
- `e2e/**/*.spec.ts`

---

### 4.2 API Documentation & SDK
**Priority:** MEDIUM | **Effort:** Low | **Timeline:** Week 5

Lower barrier for integration:

**Features:**
- Enhanced OpenAPI spec with examples
- TypeScript client auto-generation
- Postman collection export endpoint
- API usage examples in docs
- Interactive API explorer (existing Swagger UI)

**Files to modify:**
- `backend/app/main.py` - Enhance OpenAPI metadata
- `backend/app/schemas/*.py` - Add examples
- New: API client generation script

---

### 4.3 Development Tools
**Priority:** LOW | **Effort:** Low | **Timeline:** Week 6

Improve developer workflow:

**Features:**
- Database seeding with realistic test data
- CLI commands for admin tasks:
  - `create-admin` - Create admin user
  - `reset-password` - Reset user password
  - `cleanup-audit` - Purge old audit logs
  - `export-data` - Data export utilities
- Enhanced health check dashboard
- Request/response logging toggle

**Files to create:**
- `backend/app/core/management.py` - CLI commands
- `backend/scripts/seed.py` - Database seeding

---

## Implementation Guidelines

### For AI Coding Agents

**When implementing features:**
1. Always check `AGENTS.md` for project conventions
2. Use `import type` for TypeScript interfaces
3. Follow existing patterns in `backend/app/services/`
4. Add audit logging for all data changes
5. Include permission checks in new endpoints
6. Write tests alongside implementation

**Code patterns to follow:**
```python
# Backend - Service layer pattern
async def create_resource(db: AsyncSession, data: ResourceCreate) -> Resource:
    resource = Resource(**data.model_dump())
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    
    # Audit logging
    await log_model_change(db, AuditAction.CREATE, resource)
    return resource

# Frontend - Hook pattern
export function useResource() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: resourceApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resources"] });
      toast.success("Resource created");
    },
  });
}
```

---

## Decision Points

### Before Phase 1

1. **✅ Soft Delete Retention Period**
   - **DECISION:** Retain until explicit purge (no automatic purging)
   - Admin must manually purge from Trash
   - Audit trail preserved indefinitely for compliance

2. **✅ RBAC Scope**
   - **DECISION:** Resource-level permissions required
   - Examples: "Manager can only see their department's users", "Team Lead can view but not delete their team's tasks"
   - Implementation: Permission matrix with resource scoping

### Before Phase 3

3. **✅ Webhook Events Priority**
   - **DECISION:** Nice to have, implement if time permits
   - Priority events if implemented: User lifecycle, Task changes
   - File upload events: Not needed initially

4. **✅ Batch Processing File Types**
   - **DECISION:** CSV is mandatory, JSON is optional
   - CSV import for bulk operations (users, tasks)
   - JSON support for API integrations
   - Excel (.xlsx) deferred to later phase

### Before Phase 4

5. **✅ Test Coverage Target**
   - **DECISION:** 80% coverage target
   - Focus on critical paths: auth, permissions, data operations
   - E2E tests for main user flows

6. **✅ Documentation Style**
   - **DECISION:** Both inline and separate guides
   - Inline: Verbose JSDoc/docstrings for AI agents
   - Guides: Markdown files for architecture and usage
   - Examples: Code patterns in `/docs/examples/`

---

## Success Criteria

**Phase 1 Complete When:**
- Deleted records can be restored from Trash
- GDPR data export produces valid JSON
- Account deletion request creates audit trail

**Phase 2 Complete When:**
- Admin can create custom roles
- Permissions control API access
- UI hides unauthorized actions

**Phase 3 Complete When:**
- External system receives webhook on user creation
- Batch CSV upload creates users with validation
- Failed webhooks retry automatically

**Phase 4 Complete When:**
- 80% test coverage achieved
- CI/CD runs tests on PR
- New developer can onboard in < 30 minutes

---

## Notes

- All phases assume Docker-based development workflow
- Database migrations handled automatically (already implemented)
- Audit logging should capture all changes (already implemented)
- Frontend uses shadcn/ui components consistently
- Backend follows FastAPI best practices with async SQLAlchemy

**Last Updated:** 2026-02-20  
**Next Review:** After Phase 2 completion

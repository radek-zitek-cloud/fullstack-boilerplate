# RBAC Implementation Plan

## Decisions Locked
- **Combined roles**: Union of permissions across multiple roles
- **Tree hierarchy**: Multi-level, manager sees all subordinates recursively
- **Component-scoped**: Roles don't span components, use multiple roles
- **No default roles**: New users have no permissions until explicitly assigned
- **Explicit admin**: Admin must have explicit roles, no bypass
- **DB queries**: Check permissions via database on each request
- **Hide UI**: Components hidden if no access
- **Admin management**: Admin UI for role management

---

## Database Schema

### 1. User Hierarchy Extension
```python
# backend/app/models/user.py
manager_id: Mapped[Optional[int]] = mapped_column(
    ForeignKey("users.id"), nullable=True
)
subordinates: Mapped[List["User"]] = relationship(
    "User",
    back_populates="manager",
    remote_side="User.id",
    lazy="selectin"
)
manager: Mapped[Optional["User"]] = relationship(
    "User",
    back_populates="subordinates",
    lazy="selectin"
)
```

### 2. Role Model
```python
# backend/app/models/role.py
class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    component: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Permissions: {"create": "own", "read": "subordinates", "update": null, "delete": null}
    # scope: "own", "subordinates", "all", null (deny)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    
    __table_args__ = (
        UniqueConstraint('component', 'name', name='uix_role_component_name'),
    )
```

### 3. UserRole Association
```python
# backend/app/models/user_role.py
class UserRole(Base, TimestampMixin):
    __tablename__ = "user_roles"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    
    user: Mapped["User"] = relationship("User", back_populates="roles")
    role: Mapped["Role"] = relationship("Role", lazy="selectin")
```

### 4. User Model Update
```python
# backend/app/models/user.py - add to User class
roles: Mapped[List["UserRole"]] = relationship(
    "UserRole", back_populates="user", lazy="selectin"
)
```

---

## Backend Implementation

### Phase 1: Core Services

#### File: `backend/app/services/rbac.py`
```python
# Key functions to implement:

async def check_permission(
    db: AsyncSession,
    user_id: int,
    component: str,
    action: str,
    resource_owner_id: Optional[int] = None
) -> bool:
    """Check if user has permission for action."""

async def get_user_permissions(
    db: AsyncSession,
    user_id: int,
    component: str
) -> Dict[str, Optional[str]]:
    """Get effective permissions (union of all roles)."""

async def is_in_hierarchy(
    db: AsyncSession,
    manager_id: int,
    subordinate_id: int
) -> bool:
    """Check if subordinate is in manager's tree."""

async def get_all_subordinate_ids(
    db: AsyncSession,
    manager_id: int
) -> List[int]:
    """Get all subordinate IDs recursively."""
```

#### File: `backend/app/core/permissions.py`
```python
# Permission dependency factory

def require_permission(component: str, action: str):
    """Create FastAPI dependency for permission check."""
    
async def get_current_user_permissions(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserPermissions:
    """Get all permissions for current user (for JWT/cache if needed later)."""
```

### Phase 2: Task Endpoint Updates

Update `backend/app/api/api_v1/endpoints/tasks.py`:

```python
# Replace current_user["id"] checks with permission checks

@router.get("/")
async def get_tasks(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Use permission service to filter based on read scope
    perms = await get_user_permissions(db, current_user["id"], "tasks")
    # Filter query based on scope (own/subordinates/all)

@router.get("/{task_id}")
async def get_task(
    task_id: int,
    current_user: dict = Depends(require_permission("tasks", "read")),
    db: AsyncSession = Depends(get_db)
):
    # Permission dependency handles check

@router.put("/{task_id}")
async def update_task(
    task_id: int,
    # ...
    current_user: dict = Depends(require_permission("tasks", "update")),
):
    # Check if user can update this specific task (ownership/hierarchy)
```

### Phase 3: Admin API Endpoints

#### File: `backend/app/api/api_v1/endpoints/admin_roles.py`
```python
# Admin-only endpoints

@router.get("/roles")
async def list_roles(component: Optional[str] = None):
    """List all roles, optionally filtered by component."""

@router.post("/roles")
async def create_role(role_data: RoleCreate):
    """Create new role (admin only)."""

@router.put("/roles/{role_id}")
async def update_role(role_id: int, role_data: RoleUpdate):
    """Update role permissions (admin only)."""

@router.delete("/roles/{role_id}")
async def delete_role(role_id: int):
    """Delete role (admin only)."""

@router.get("/users/{user_id}/roles")
async def get_user_roles(user_id: int):
    """Get roles assigned to user."""

@router.post("/users/{user_id}/roles")
async def assign_role(user_id: int, role_assignment: RoleAssignment):
    """Assign role to user (admin only)."""

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role(user_id: int, role_id: int):
    """Remove role from user (admin only)."""

@router.put("/users/{user_id}/manager")
async def set_manager(user_id: int, manager_id: Optional[int]):
    """Set user's manager (admin only)."""
```

---

## Frontend Implementation

### Phase 1: Permission Hook

#### File: `frontend/src/hooks/usePermission.ts`
```typescript
interface Permissions {
  create: "own" | "subordinates" | "all" | null;
  read: "own" | "subordinates" | "all" | null;
  update: "own" | "subordinates" | "all" | null;
  delete: "own" | "subordinates" | "all" | null;
}

export function usePermission(component: string) {
  const { user } = useAuth();
  
  const { data: permissions, isLoading } = useQuery<Permissions>({
    queryKey: ['permissions', component, user?.id],
    queryFn: () => rbacApi.getPermissions(component),
    enabled: !!user,
  });
  
  const can = (action: keyof Permissions): boolean => {
    return permissions?.[action] !== null;
  };
  
  const scope = (action: keyof Permissions): string | null => {
    return permissions?.[action] ?? null;
  };
  
  const canAccessResource = (
    action: keyof Permissions,
    resourceOwnerId: number
  ): boolean => {
    const permScope = scope(action);
    if (!permScope) return false;
    if (permScope === "all") return true;
    if (permScope === "own") return resourceOwnerId === user?.id;
    // "subordinates" requires async hierarchy check
    return false; // Handled separately
  };
  
  return { can, scope, canAccessResource, permissions, isLoading };
}
```

### Phase 2: Permission-Based UI Components

#### File: `frontend/src/components/PermissionGuard.tsx`
```typescript
interface PermissionGuardProps {
  component: string;
  action: "create" | "read" | "update" | "delete";
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGuard({ 
  component, 
  action, 
  children, 
  fallback = null 
}: PermissionGuardProps) {
  const { can } = usePermission(component);
  
  if (!can(action)) {
    return fallback;
  }
  
  return <>{children}</>;
}
```

### Phase 3: Update Tasks Page

#### File: `frontend/src/pages/Tasks.tsx` updates:
```typescript
function Tasks() {
  const { can } = usePermission("tasks");
  
  return (
    <div>
      {/* Only show Create button if user has create permission */}
      <PermissionGuard component="tasks" action="create">
        <Button onClick={() => setIsDialogOpen(true)}>
          New Task
        </Button>
      </PermissionGuard>
      
      <TasksList />
    </div>
  );
}

function TaskCard({ task }: { task: Task }) {
  const { user } = useAuth();
  const { can, scope } = usePermission("tasks");
  
  // Determine if user can edit this specific task
  const canEditThis = () => {
    if (!can("update")) return false;
    const editScope = scope("update");
    if (editScope === "all") return true;
    if (editScope === "own") return task.user_id === user?.id;
    // "subordinates" - need hierarchy check
    return false;
  };
  
  return (
    <Card>
      {/* ... */}
      {canEditThis() && (
        <Button onClick={() => handleEdit(task)}>Edit</Button>
      )}
    </Card>
  );
}
```

### Phase 4: Admin RBAC UI

#### File: `frontend/src/pages/Admin/Roles.tsx`
```typescript
// Admin interface to:
// - View all roles grouped by component
// - Create new roles with permission matrix
// - Edit existing role permissions
// - Delete roles

interface RoleForm {
  component: string;
  name: string;
  description: string;
  permissions: {
    create: "own" | "subordinates" | "all" | null;
    read: "own" | "subordinates" | "all" | null;
    update: "own" | "subordinates" | "all" | null;
    delete: "own" | "subordinates" | "all" | null;
  };
}
```

#### File: `frontend/src/pages/Admin/UserRoles.tsx`
```typescript
// Admin interface to:
// - Search/select user
// - View user's current roles
// - Assign/remove roles
// - Set user's manager
```

#### File: `frontend/src/pages/Admin/OrganizationTree.tsx`
```typescript
// Visual hierarchy tree showing:
// - User hierarchy (who reports to whom)
// - Roles assigned to each user
// - Click to reassign manager
```

---

## Migration Strategy

### Database Migration
```python
# Migration steps:
1. Add User.manager_id column (nullable)
2. Create Role table
3. Create UserRole table
4. Seed initial roles for "tasks" component
5. Assign "Tasks: Admin" role to existing admin users
```

### Backward Compatibility
- Existing `is_admin` field kept temporarily
- Gradual migration: check both old and new permission systems
- Remove `is_admin` after full RBAC rollout

---

## Testing Strategy

### Backend Tests
```python
# Test hierarchy traversal
async def test_is_in_hierarchy():
    # A → B → C hierarchy
    # B should be in A's hierarchy
    # C should be in A's hierarchy
    # A should NOT be in B's hierarchy

# Test permission union
async def test_combined_roles():
    # User has Role1: {read: "own"} and Role2: {read: "all"}
    # Should have read: "all" (broadest scope)

# Test resource filtering
async def test_task_filtering():
    # Manager with "subordinates" read scope
    # Should see own tasks + all subordinate tasks
```

### Frontend Tests
```typescript
// Test permission hook
// Test PermissionGuard component
// Test admin role management
```

---

## Files to Create/Modify

### Backend (New Files)
- `backend/app/models/role.py`
- `backend/app/models/user_role.py`
- `backend/app/schemas/role.py`
- `backend/app/services/rbac.py`
- `backend/app/core/permissions.py`
- `backend/app/api/api_v1/endpoints/admin_roles.py`

### Backend (Modified)
- `backend/app/models/user.py` - add hierarchy + roles relationship
- `backend/app/models/__init__.py` - export new models
- `backend/app/api/deps.py` - add permission dependencies
- `backend/app/api/api_v1/api.py` - add admin roles router
- `backend/app/api/api_v1/endpoints/tasks.py` - use permissions

### Frontend (New Files)
- `frontend/src/hooks/usePermission.ts`
- `frontend/src/services/rbac.ts`
- `frontend/src/components/PermissionGuard.tsx`
- `frontend/src/pages/Admin/Roles.tsx`
- `frontend/src/pages/Admin/UserRoles.tsx`
- `frontend/src/pages/Admin/OrganizationTree.tsx`

### Frontend (Modified)
- `frontend/src/pages/Tasks.tsx` - use permission system
- `frontend/src/components/Layout.tsx` - add admin nav links
- `frontend/src/App.tsx` - add admin routes

---

## Implementation Order

1. **Database models** (User hierarchy, Role, UserRole)
2. **Core RBAC service** (check_permission, hierarchy traversal)
3. **Admin API** (CRUD roles, assign roles, set manager)
4. **Update Task endpoints** (use RBAC)
5. **Frontend permission hook**
6. **Update Tasks UI** (permission guards)
7. **Admin RBAC UI** (role management, user assignment, hierarchy)

**Estimated effort:** 2-3 days for backend, 2-3 days for frontend

**Ready to proceed with implementation?**

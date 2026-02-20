import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Plus, Pencil, Trash2, Shield, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

interface Role {
  id: number;
  component: string;
  name: string;
  description: string;
  permissions: Record<string, string | null>;
  created_at: string;
  updated_at: string;
}

const VALID_ACTIONS = ["create", "read", "update", "delete"] as const;
const VALID_SCOPES = [
  { value: "own", label: "Own", description: "Own resources only" },
  { value: "subordinates", label: "Team", description: "Own + subordinates" },
  { value: "all", label: "All", description: "Full access" },
  { value: null, label: "Deny", description: "No access" },
] as const;

const DEFAULT_COMPONENTS = ["tasks", "users", "audit"];

interface RoleFormData {
  component: string;
  name: string;
  description: string;
  permissions: Record<string, string | null>;
}

const defaultPermissions: Record<string, string | null> = {
  create: null,
  read: null,
  update: null,
  delete: null,
};

export default function RolesManagement() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [roleToDelete, setRoleToDelete] = useState<Role | null>(null);
  const [formData, setFormData] = useState<RoleFormData>({
    component: "tasks",
    name: "",
    description: "",
    permissions: { ...defaultPermissions },
  });

  const { data: roles, isLoading } = useQuery<Role[]>({
    queryKey: ["admin", "roles"],
    queryFn: async () => {
      const response = await api.get("/admin/rbac/roles");
      return response.data;
    },
    enabled: user?.is_admin,
  });

  const createRoleMutation = useMutation({
    mutationFn: async (data: RoleFormData) => {
      await api.post("/admin/rbac/roles", data);
    },
    onSuccess: () => {
      toast.success("Role created successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "roles"] });
      resetForm();
      setIsDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create role");
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<RoleFormData> }) => {
      await api.put(`/admin/rbac/roles/${id}`, data);
    },
    onSuccess: () => {
      toast.success("Role updated successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "roles"] });
      resetForm();
      setIsDialogOpen(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update role");
    },
  });

  const deleteRoleMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/admin/rbac/roles/${id}`);
    },
    onSuccess: () => {
      toast.success("Role deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "roles"] });
      setRoleToDelete(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete role");
    },
  });

  const resetForm = () => {
    setEditingRole(null);
    setFormData({
      component: "tasks",
      name: "",
      description: "",
      permissions: { ...defaultPermissions },
    });
  };

  const handleOpenDialog = (role?: Role) => {
    if (role) {
      setEditingRole(role);
      setFormData({
        component: role.component,
        name: role.name,
        description: role.description || "",
        permissions: { ...role.permissions },
      });
    } else {
      resetForm();
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingRole) {
      updateRoleMutation.mutate({
        id: editingRole.id,
        data: {
          description: formData.description,
          permissions: formData.permissions,
        },
      });
    } else {
      createRoleMutation.mutate(formData);
    }
  };

  const updatePermission = (action: string, scope: string | null) => {
    setFormData((prev) => ({
      ...prev,
      permissions: {
        ...prev.permissions,
        [action]: scope,
      },
    }));
  };

  const groupedRoles = roles?.reduce((acc, role) => {
    if (!acc[role.component]) {
      acc[role.component] = [];
    }
    acc[role.component].push(role);
    return acc;
  }, {} as Record<string, Role[]>);

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-64">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              Only administrators can manage roles.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Roles Management</h1>
          <p className="text-muted-foreground">
            Create and manage roles for access control across components.
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => handleOpenDialog()}>
              <Plus className="w-4 h-4 mr-2" />
              Create Role
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingRole ? "Edit Role" : "Create New Role"}
              </DialogTitle>
              <DialogDescription>
                Define permissions for this role. Each action can have a scope
                from "own" (most restrictive) to "all" (most permissive).
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="component">Component</Label>
                  <Select
                    value={formData.component}
                    onValueChange={(value) =>
                      setFormData((prev) => ({ ...prev, component: value }))
                    }
                    disabled={!!editingRole}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select component" />
                    </SelectTrigger>
                    <SelectContent>
                      {DEFAULT_COMPONENTS.map((comp) => (
                        <SelectItem key={comp} value={comp}>
                          {comp.charAt(0).toUpperCase() + comp.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {editingRole && (
                    <p className="text-xs text-muted-foreground">
                      Component cannot be changed after creation
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">Role Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, name: e.target.value }))
                    }
                    placeholder="e.g., Manager, Editor, Viewer"
                    disabled={!!editingRole}
                    required
                  />
                  {editingRole && (
                    <p className="text-xs text-muted-foreground">
                      Role name cannot be changed after creation
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    placeholder="Describe what this role can do..."
                    rows={2}
                  />
                </div>

                <div className="space-y-4">
                  <Label>Permissions</Label>
                  <div className="space-y-3">
                    {VALID_ACTIONS.map((action) => (
                      <div
                        key={action}
                        className="flex items-center justify-between p-3 border rounded-lg bg-muted/50"
                      >
                        <div className="flex items-center gap-3">
                          <Shield className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium capitalize">{action}</span>
                        </div>
                        <Select
                          value={formData.permissions[action] ?? "null"}
                          onValueChange={(value) =>
                            updatePermission(
                              action,
                              value === "null" ? null : value
                            )
                          }
                        >
                          <SelectTrigger className="w-[220px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="w-[220px]">
                            {VALID_SCOPES.map((scope) => (
                              <SelectItem
                                key={scope.value ?? "null"}
                                value={scope.value ?? "null"}
                              >
                                <div className="flex flex-col">
                                  <span>{scope.label}</span>
                                  <span className="text-xs text-muted-foreground truncate max-w-[180px]">
                                    {scope.description}
                                  </span>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    resetForm();
                    setIsDialogOpen(false);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={
                    !formData.name ||
                    createRoleMutation.isPending ||
                    updateRoleMutation.isPending
                  }
                >
                  {editingRole
                    ? updateRoleMutation.isPending
                      ? "Updating..."
                      : "Update Role"
                    : createRoleMutation.isPending
                    ? "Creating..."
                    : "Create Role"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="text-center py-8">Loading roles...</div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedRoles || {}).map(([component, componentRoles]) => (
            <Card key={component}>
              <CardHeader>
                <CardTitle className="capitalize flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  {component} Component
                </CardTitle>
                <CardDescription>
                  {componentRoles.length} role(s) defined for {component}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {componentRoles.map((role) => (
                    <div
                      key={role.id}
                      className="flex items-start justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{role.name}</h3>
                          <Badge variant="secondary" className="text-xs">
                            ID: {role.id}
                          </Badge>
                        </div>
                        {role.description && (
                          <p className="text-sm text-muted-foreground">
                            {role.description}
                          </p>
                        )}
                        <div className="flex gap-2 flex-wrap">
                          {Object.entries(role.permissions).map(
                            ([action, scope]) =>
                              scope && (
                                <Badge
                                  key={action}
                                  variant={scope === "all" ? "default" : "secondary"}
                                  className="text-xs"
                                >
                                  {action}: {scope}
                                </Badge>
                              )
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleOpenDialog(role)}
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={() => setRoleToDelete(role)}
                          disabled={deleteRoleMutation.isPending}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}

          {!roles?.length && (
            <Card>
              <CardContent className="py-12 text-center">
                <Shield className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No roles defined</h3>
                <p className="text-muted-foreground mb-4">
                  Get started by creating your first role for access control.
                </p>
                <Button onClick={() => handleOpenDialog()}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create First Role
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!roleToDelete} onOpenChange={() => setRoleToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Delete Role?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the role <strong>"{roleToDelete?.name}"</strong>?
              <br /><br />
              This action cannot be undone. This will remove the role from all users who have been assigned it.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setRoleToDelete(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => roleToDelete && deleteRoleMutation.mutate(roleToDelete.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteRoleMutation.isPending}
            >
              {deleteRoleMutation.isPending ? "Deleting..." : "Delete Role"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
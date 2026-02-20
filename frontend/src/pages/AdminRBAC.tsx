import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
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
import { toast } from "sonner";

interface Role {
  id: number;
  component: string;
  name: string;
  description: string;
  permissions: Record<string, string | null>;
}

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
}

export default function AdminRBAC() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedUser, setSelectedUser] = useState<number | null>(null);
  const [selectedRole, setSelectedRole] = useState<number | null>(null);

  const { data: roles } = useQuery<Role[]>({
    queryKey: ["admin", "roles"],
    queryFn: async () => {
      const response = await api.get("/admin/rbac/roles");
      return response.data;
    },
    enabled: user?.is_admin,
  });

  const { data: users } = useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const response = await api.get("/users/");
      return response.data;
    },
    enabled: user?.is_admin,
  });

  const assignRoleMutation = useMutation({
    mutationFn: async ({ userId, roleId }: { userId: number; roleId: number }) => {
      await api.post(`/admin/rbac/users/${userId}/roles`, { role_id: roleId });
    },
    onSuccess: () => {
      toast.success("Role assigned successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "user-roles"] });
      setSelectedRole(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to assign role");
    },
  });

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-64">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              Only administrators can manage RBAC settings.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const groupedRoles = roles?.reduce((acc, role) => {
    if (!acc[role.component]) {
      acc[role.component] = [];
    }
    acc[role.component].push(role);
    return acc;
  }, {} as Record<string, Role[]>);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">RBAC Management</h1>
        <p className="text-muted-foreground">
          Manage roles and permissions for users.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Assign Role to User</CardTitle>
            <CardDescription>
              Select a user and assign them a role.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Select User</label>
              <Select
                value={selectedUser?.toString()}
                onValueChange={(value) => setSelectedUser(Number(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a user" />
                </SelectTrigger>
                <SelectContent>
                  {users?.map((u) => (
                    <SelectItem key={u.id} value={u.id.toString()}>
                      {u.first_name || u.last_name
                        ? `${u.first_name || ""} ${u.last_name || ""} (${u.email})`
                        : u.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Select Role</label>
              <Select
                value={selectedRole?.toString()}
                onValueChange={(value) => setSelectedRole(Number(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a role" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(groupedRoles || {}).map(([component, componentRoles]) => (
                    <div key={component}>
                      <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase">
                        {component}
                      </div>
                      {componentRoles.map((role) => (
                        <SelectItem key={role.id} value={role.id.toString()}>
                          {role.name}
                        </SelectItem>
                      ))}
                    </div>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={() => {
                if (selectedUser && selectedRole) {
                  assignRoleMutation.mutate({
                    userId: selectedUser,
                    roleId: selectedRole,
                  });
                }
              }}
              disabled={!selectedUser || !selectedRole || assignRoleMutation.isPending}
              className="w-full"
            >
              {assignRoleMutation.isPending ? "Assigning..." : "Assign Role"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Available Roles</CardTitle>
            <CardDescription>
              Roles defined in the system.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(groupedRoles || {}).map(([component, componentRoles]) => (
                <div key={component} className="space-y-2">
                  <h3 className="font-semibold capitalize">{component}</h3>
                  <div className="space-y-2">
                    {componentRoles.map((role) => (
                      <div
                        key={role.id}
                        className="p-3 border rounded-lg bg-muted/50"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{role.name}</span>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {role.description}
                        </p>
                        <div className="flex gap-2 mt-2 flex-wrap">
                          {Object.entries(role.permissions).map(([action, scope]) => (
                            scope && (
                              <Badge key={action} variant="secondary" className="text-xs">
                                {action}: {scope}
                              </Badge>
                            )
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

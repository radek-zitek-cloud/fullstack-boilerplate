import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Plus, Trash2, User as UserIcon, Shield, Search, X, Edit2, MoreHorizontal } from "lucide-react";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_admin: boolean;
  roles?: Role[];
}

interface Role {
  id: number;
  component: string;
  name: string;
  description: string;
  permissions: Record<string, string | null>;
}

interface UserFormData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_admin: boolean;
}

const initialUserForm: UserFormData = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  is_active: true,
  is_admin: false,
};

export default function UserRolesManagement() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<number | null>(null);
  const [isAssignDialogOpen, setIsAssignDialogOpen] = useState(false);
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [roleToRemove, setRoleToRemove] = useState<{ userId: number; roleId: number; roleName: string } | null>(null);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [userForm, setUserForm] = useState<UserFormData>(initialUserForm);

  const { data: users, isLoading: usersLoading } = useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const response = await api.get("/admin/rbac/users");
      return response.data;
    },
    enabled: user?.is_admin,
  });

  const { data: roles, isLoading: rolesLoading } = useQuery<Role[]>({
    queryKey: ["admin", "roles"],
    queryFn: async () => {
      const response = await api.get("/admin/rbac/roles");
      return response.data;
    },
    enabled: user?.is_admin,
  });

  const createUserMutation = useMutation({
    mutationFn: async (data: UserFormData) => {
      await api.post("/admin/rbac/users", data);
    },
    onSuccess: () => {
      toast.success("User created successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      setIsUserDialogOpen(false);
      setUserForm(initialUserForm);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create user");
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<UserFormData> }) => {
      await api.put(`/admin/rbac/users/${id}`, data);
    },
    onSuccess: () => {
      toast.success("User updated successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      setIsUserDialogOpen(false);
      setUserForm(initialUserForm);
      setIsEditMode(false);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update user");
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/admin/rbac/users/${id}`);
    },
    onSuccess: () => {
      toast.success("User deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      setUserToDelete(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete user");
    },
  });

  const assignRoleMutation = useMutation({
    mutationFn: async ({ userId, roleId }: { userId: number; roleId: number }) => {
      await api.post(`/admin/rbac/users/${userId}/roles`, { role_id: roleId });
    },
    onSuccess: () => {
      toast.success("Role assigned successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      setIsAssignDialogOpen(false);
      setSelectedUser(null);
      setSelectedRole(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to assign role");
    },
  });

  const removeRoleMutation = useMutation({
    mutationFn: async ({ userId, roleId }: { userId: number; roleId: number }) => {
      await api.delete(`/admin/rbac/users/${userId}/roles/${roleId}`);
    },
    onSuccess: () => {
      toast.success("Role removed successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      setRoleToRemove(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to remove role");
    },
  });

  const handleCreateUser = () => {
    setIsEditMode(false);
    setUserForm(initialUserForm);
    setIsUserDialogOpen(true);
  };

  const handleEditUser = (userData: User) => {
    setIsEditMode(true);
    setSelectedUser(userData);
    setUserForm({
      email: userData.email,
      password: "",
      first_name: userData.first_name || "",
      last_name: userData.last_name || "",
      is_active: userData.is_active,
      is_admin: userData.is_admin,
    });
    setIsUserDialogOpen(true);
  };

  const handleSaveUser = () => {
    if (isEditMode && selectedUser) {
      const updateData: Partial<UserFormData> = {
        email: userForm.email,
        first_name: userForm.first_name,
        last_name: userForm.last_name,
        is_active: userForm.is_active,
        is_admin: userForm.is_admin,
      };
      if (userForm.password) {
        updateData.password = userForm.password;
      }
      updateUserMutation.mutate({ id: selectedUser.id, data: updateData });
    } else {
      createUserMutation.mutate(userForm);
    }
  };

  const filteredUsers = users?.filter((u) => {
    const searchLower = searchQuery.toLowerCase();
    const userRoles = u.roles || [];
    return (
      u.email.toLowerCase().includes(searchLower) ||
      u.first_name?.toLowerCase().includes(searchLower) ||
      u.last_name?.toLowerCase().includes(searchLower) ||
      userRoles.some((r: Role) =>
        r.name.toLowerCase().includes(searchLower) ||
        r.component.toLowerCase().includes(searchLower)
      )
    );
  });

  const getUserDisplayName = (userData: User) => {
    if (userData.first_name || userData.last_name) {
      return `${userData.first_name || ""} ${userData.last_name || ""}`.trim();
    }
    return userData.email;
  };

  const getUserInitials = (userData: User) => {
    if (userData.first_name && userData.last_name) {
      return `${userData.first_name[0]}${userData.last_name[0]}`.toUpperCase();
    }
    return userData.email.substring(0, 2).toUpperCase();
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
              Only administrators can manage users and role assignments.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">User Management</h1>
          <p className="text-muted-foreground">
            Manage users and their role assignments across the system.
          </p>
        </div>
        <Button onClick={handleCreateUser}>
          <Plus className="w-4 h-4 mr-2" />
          Create User
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search users or roles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
        {searchQuery && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6"
            onClick={() => setSearchQuery("")}
          >
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Users List */}
      {usersLoading ? (
        <div className="text-center py-8">Loading users...</div>
      ) : (
        <div className="space-y-4">
          {filteredUsers?.map((userData) => {
            const userRoles = userData.roles || [];

            return (
              <Card key={userData.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <Avatar>
                        <AvatarFallback>{getUserInitials(userData)}</AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg">
                            {getUserDisplayName(userData)}
                          </CardTitle>
                          {userData.is_admin && (
                            <Badge variant="default" className="text-xs">
                              Admin
                            </Badge>
                          )}
                          {!userData.is_active && (
                            <Badge variant="secondary" className="text-xs">
                              Inactive
                            </Badge>
                          )}
                        </div>
                        <CardDescription>{userData.email}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedUser(userData);
                          setIsAssignDialogOpen(true);
                        }}
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Role
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEditUser(userData)}>
                            <Edit2 className="w-4 h-4 mr-2" />
                            Edit User
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setUserToDelete(userData)}
                            className="text-destructive"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete User
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {userRoles.length === 0 ? (
                    <p className="text-sm text-muted-foreground italic">
                      No roles assigned
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {userRoles.map((role) => (
                        <Badge
                          key={role.id}
                          variant="secondary"
                          className="flex items-center gap-1 px-3 py-1"
                        >
                          <Shield className="w-3 h-3" />
                          <span className="font-medium">
                            {role.component}: {role.name}
                          </span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-4 w-4 ml-1 hover:bg-destructive/20"
                            onClick={() =>
                              setRoleToRemove({
                                userId: userData.id,
                                roleId: role.id,
                                roleName: `${role.component}: ${role.name}`,
                              })
                            }
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}

          {filteredUsers?.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <UserIcon className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No users found</h3>
                <p className="text-muted-foreground">
                  {searchQuery
                    ? "No users match your search criteria"
                    : "No users in the system"}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Create/Edit User Dialog */}
      <Dialog open={isUserDialogOpen} onOpenChange={setIsUserDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{isEditMode ? "Edit User" : "Create User"}</DialogTitle>
            <DialogDescription>
              {isEditMode
                ? "Update user details. Leave password blank to keep current password."
                : "Create a new user account."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                value={userForm.email}
                onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                placeholder="user@example.com"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                <Input
                  id="first_name"
                  value={userForm.first_name}
                  onChange={(e) => setUserForm({ ...userForm, first_name: e.target.value })}
                  placeholder="John"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                <Input
                  id="last_name"
                  value={userForm.last_name}
                  onChange={(e) => setUserForm({ ...userForm, last_name: e.target.value })}
                  placeholder="Doe"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">
                {isEditMode ? "Password (leave blank to keep current)" : "Password *"}
              </Label>
              <Input
                id="password"
                type="password"
                value={userForm.password}
                onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                placeholder={isEditMode ? "••••••••" : "Enter password"}
              />
            </div>

            <div className="flex items-center gap-6 pt-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_active"
                  checked={userForm.is_active}
                  onCheckedChange={(checked) =>
                    setUserForm({ ...userForm, is_active: checked as boolean })
                  }
                />
                <Label htmlFor="is_active" className="font-normal cursor-pointer">
                  Active
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_admin"
                  checked={userForm.is_admin}
                  onCheckedChange={(checked) =>
                    setUserForm({ ...userForm, is_admin: checked as boolean })
                  }
                />
                <Label htmlFor="is_admin" className="font-normal cursor-pointer">
                  Admin
                </Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsUserDialogOpen(false);
                setUserForm(initialUserForm);
                setIsEditMode(false);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveUser}
              disabled={
                !userForm.email ||
                (!isEditMode && !userForm.password) ||
                createUserMutation.isPending ||
                updateUserMutation.isPending
              }
            >
              {createUserMutation.isPending || updateUserMutation.isPending
                ? "Saving..."
                : isEditMode
                ? "Update User"
                : "Create User"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Role Dialog */}
      <Dialog open={isAssignDialogOpen} onOpenChange={setIsAssignDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Assign Role to User</DialogTitle>
            <DialogDescription>
              Select a role to assign to {selectedUser ? getUserDisplayName(selectedUser) : "the user"}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>User</Label>
              <Select
                value={selectedUser?.id?.toString()}
                onValueChange={(value) => {
                  const u = users?.find((user) => user.id === Number(value));
                  setSelectedUser(u || null);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a user" />
                </SelectTrigger>
                <SelectContent>
                  {users?.map((u) => (
                    <SelectItem key={u.id} value={u.id.toString()}>
                      {getUserDisplayName(u)} ({u.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Role</Label>
              <Select
                value={selectedRole?.toString()}
                onValueChange={(value) => setSelectedRole(Number(value))}
                disabled={!selectedUser}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={
                      selectedUser ? "Select a role" : "Select a user first"
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(groupedRoles || {}).map(([component, componentRoles]) => (
                    <div key={component}>
                      <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase">
                        {component}
                      </div>
                      {componentRoles.map((role) => {
                        const userRoleData = users?.find(
                          (u) => u.id === selectedUser?.id
                        );
                        const alreadyHasRole = userRoleData?.roles?.some(
                          (r: Role) => r.id === role.id
                        );
                        return (
                          <SelectItem
                            key={role.id}
                            value={role.id.toString()}
                            disabled={alreadyHasRole}
                          >
                            <div className="flex flex-col">
                              <span>{role.name}</span>
                              {alreadyHasRole && (
                                <span className="text-xs text-muted-foreground">
                                  Already assigned
                                </span>
                              )}
                            </div>
                          </SelectItem>
                        );
                      })}
                    </div>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsAssignDialogOpen(false);
                setSelectedUser(null);
                setSelectedRole(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (selectedUser && selectedRole) {
                  assignRoleMutation.mutate({
                    userId: selectedUser.id,
                    roleId: selectedRole,
                  });
                }
              }}
              disabled={!selectedUser || !selectedRole || assignRoleMutation.isPending}
            >
              {assignRoleMutation.isPending ? "Assigning..." : "Assign Role"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove Role Confirmation */}
      <AlertDialog
        open={!!roleToRemove}
        onOpenChange={() => setRoleToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Role?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove the role{" "}
              <strong>"{roleToRemove?.roleName}"</strong> from this user?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setRoleToRemove(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                roleToRemove &&
                removeRoleMutation.mutate({
                  userId: roleToRemove.userId,
                  roleId: roleToRemove.roleId,
                })
              }
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={removeRoleMutation.isPending}
            >
              {removeRoleMutation.isPending ? "Removing..." : "Remove Role"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete User Confirmation */}
      <AlertDialog
        open={!!userToDelete}
        onOpenChange={() => setUserToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the user{" "}
              <strong>"{userToDelete?.email}"</strong>? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setUserToDelete(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                userToDelete && deleteUserMutation.mutate(userToDelete.id)
              }
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteUserMutation.isPending}
            >
              {deleteUserMutation.isPending ? "Deleting..." : "Delete User"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

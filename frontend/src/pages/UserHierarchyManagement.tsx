import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { 
  Users, 
  Search, 
  X, 
  Network, 
  UserPlus, 
  ArrowUp,
  ChevronRight,
  ChevronDown,
  Users2
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_admin: boolean;
  manager_id?: number;
  full_name?: string;
}

interface HierarchyData {
  user_id: number;
  user_email: string;
  user_full_name: string;
  manager: {
    id: number;
    email: string;
    full_name: string;
  } | null;
  subordinates: {
    id: number;
    email: string;
    full_name: string;
  }[];
  total_subordinates: number;
}

interface TreeNode {
  user: User;
  children: TreeNode[];
  level: number;
}

export default function UserHierarchyManagement() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [expandedUsers, setExpandedUsers] = useState<Set<number>>(new Set());
  const [isManagerDialogOpen, setIsManagerDialogOpen] = useState(false);
  const [selectedManagerId, setSelectedManagerId] = useState<string>("");

  const { data: users, isLoading: usersLoading } = useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const response = await api.get("/admin/rbac/users");
      return response.data;
    },
    enabled: user?.is_admin,
  });

  const { data: hierarchyData, isLoading: hierarchyLoading } = useQuery<HierarchyData[]>({
    queryKey: ["admin", "hierarchy"],
    queryFn: async () => {
      if (!users) return [];
      const promises = users.map(async (u) => {
        try {
          const response = await api.get(`/admin/rbac/hierarchy/${u.id}`);
          return response.data;
        } catch {
          return {
            user_id: u.id,
            user_email: u.email,
            user_full_name: u.full_name || u.email,
            manager: null,
            subordinates: [],
            total_subordinates: 0,
          };
        }
      });
      return Promise.all(promises);
    },
    enabled: user?.is_admin && !!users,
  });

  const updateManagerMutation = useMutation({
    mutationFn: async ({ userId, managerId }: { userId: number; managerId: number | null }) => {
      await api.put(`/admin/rbac/users/${userId}/manager`, null, {
        params: { manager_id: managerId },
      });
    },
    onSuccess: () => {
      toast.success("Manager assigned successfully");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "hierarchy"] });
      setIsManagerDialogOpen(false);
      setSelectedUser(null);
      setSelectedManagerId("");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to assign manager");
    },
  });

  // Build tree structure from flat user list
  const buildTree = (): TreeNode[] => {
    if (!users) return [];

    const userMap = new Map<number, User>();
    users.forEach((u) => userMap.set(u.id, u));

    const childrenMap = new Map<number, number[]>();
    users.forEach((u) => {
      if (u.manager_id) {
        const siblings = childrenMap.get(u.manager_id) || [];
        siblings.push(u.id);
        childrenMap.set(u.manager_id, siblings);
      }
    });

    const buildNode = (userId: number, level: number): TreeNode => {
      const user = userMap.get(userId)!;
      const childIds = childrenMap.get(userId) || [];
      return {
        user,
        children: childIds.map((id) => buildNode(id, level + 1)),
        level,
      };
    };

    // Find root users (those without managers)
    const rootUsers = users.filter((u) => !u.manager_id);
    return rootUsers.map((u) => buildNode(u.id, 0));
  };

  const toggleExpanded = (userId: number) => {
    setExpandedUsers((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) {
        next.delete(userId);
      } else {
        next.add(userId);
      }
      return next;
    });
  };

  const getUserDisplayName = (userData: User | { first_name?: string; last_name?: string; email: string; full_name?: string }) => {
    if ("full_name" in userData && userData.full_name) {
      return userData.full_name;
    }
    if ("first_name" in userData && (userData.first_name || userData.last_name)) {
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

  const handleAssignManager = (userData: User) => {
    setSelectedUser(userData);
    setSelectedManagerId(userData.manager_id?.toString() || "none");
    setIsManagerDialogOpen(true);
  };

  const handleSaveManager = () => {
    if (selectedUser) {
      const managerId = selectedManagerId === "none" ? null : parseInt(selectedManagerId);
      updateManagerMutation.mutate({ userId: selectedUser.id, managerId });
    }
  };

  // Filter users based on search
  const filteredUsers = users?.filter((u) => {
    if (!searchQuery) return true;
    const searchLower = searchQuery.toLowerCase();
    return (
      u.email.toLowerCase().includes(searchLower) ||
      u.first_name?.toLowerCase().includes(searchLower) ||
      u.last_name?.toLowerCase().includes(searchLower)
    );
  });

  const tree = buildTree();

  const renderTreeNode = (node: TreeNode) => {
    const hasChildren = node.children.length > 0;
    const isExpanded = expandedUsers.has(node.user.id);
    const userHierarchy = hierarchyData?.find((h) => h.user_id === node.user.id);

    return (
      <div key={node.user.id} className="select-none">
        <div
          className={cn(
            "flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-accent cursor-pointer transition-colors",
            node.level > 0 && "ml-8"
          )}
          style={{ marginLeft: `${node.level * 24}px` }}
        >
          <button
            onClick={() => hasChildren && toggleExpanded(node.user.id)}
            className={cn(
              "w-6 h-6 flex items-center justify-center rounded hover:bg-accent-foreground/10",
              !hasChildren && "invisible"
            )}
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>

          <Avatar className="h-8 w-8">
            <AvatarFallback className="text-xs">{getUserInitials(node.user)}</AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium truncate">
                {getUserDisplayName(node.user)}
              </span>
              {node.user.is_admin && (
                <Badge variant="default" className="text-xs">Admin</Badge>
              )}
              {!node.user.is_active && (
                <Badge variant="secondary" className="text-xs">Inactive</Badge>
              )}
            </div>
            <div className="text-xs text-muted-foreground truncate">
              {node.user.email}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {userHierarchy && userHierarchy.total_subordinates > 0 && (
              <Badge variant="outline" className="text-xs flex items-center gap-1">
                <Users2 className="w-3 h-3" />
                {userHierarchy.total_subordinates}
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleAssignManager(node.user);
              }}
            >
              <ArrowUp className="w-4 h-4 mr-1" />
              {node.user.manager_id ? "Change Manager" : "Assign Manager"}
            </Button>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="mt-1">
            {node.children.map((child) => renderTreeNode(child))}
          </div>
        )}
      </div>
    );
  };

  // Render flat list view for search results
  const renderFlatList = () => {
    if (!filteredUsers) return null;

    return filteredUsers.map((userData) => {
      const userHierarchy = hierarchyData?.find((h) => h.user_id === userData.id);
      const hasManager = !!userData.manager_id;

      return (
        <Card key={userData.id} className="mb-3">
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
                      <Badge variant="default" className="text-xs">Admin</Badge>
                    )}
                    {!userData.is_active && (
                      <Badge variant="secondary" className="text-xs">Inactive</Badge>
                    )}
                  </div>
                  <CardDescription>{userData.email}</CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {userHierarchy && userHierarchy.total_subordinates > 0 && (
                  <Badge variant="outline" className="text-xs flex items-center gap-1">
                    <Users2 className="w-3 h-3" />
                    {userHierarchy.total_subordinates} subordinates
                  </Badge>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleAssignManager(userData)}
                >
                  <ArrowUp className="w-4 h-4 mr-2" />
                  {hasManager ? "Change Manager" : "Assign Manager"}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-sm">
                <span className="text-muted-foreground">Manager: </span>
                {userHierarchy?.manager ? (
                  <span className="font-medium">
                    {userHierarchy.manager.full_name || userHierarchy.manager.email}
                  </span>
                ) : (
                  <span className="text-muted-foreground italic">No manager assigned</span>
                )}
              </div>
              {userHierarchy && userHierarchy.subordinates.length > 0 && (
                <div className="text-sm">
                  <span className="text-muted-foreground">Direct subordinates: </span>
                  <span className="font-medium">{userHierarchy.subordinates.length}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      );
    });
  };

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-64">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              Only administrators can manage user hierarchy.
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
          <h1 className="text-2xl font-bold">User Hierarchy</h1>
          <p className="text-muted-foreground">
            Manage organizational structure and reporting relationships.
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search users..."
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

      {/* Content */}
      {usersLoading || hierarchyLoading ? (
        <div className="text-center py-8">Loading hierarchy...</div>
      ) : searchQuery ? (
        // Flat list view for search
        <div className="space-y-4">
          {renderFlatList()}
          {filteredUsers?.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No users found</h3>
                <p className="text-muted-foreground">
                  No users match your search criteria
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        // Tree view
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Network className="w-5 h-5" />
              <CardTitle>Organization Chart</CardTitle>
            </div>
            <CardDescription>
              Click on the arrow to expand/collapse branches. Click "Assign Manager" to change reporting relationships.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {tree.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No users in hierarchy</h3>
                <p className="text-muted-foreground">
                  Start by assigning managers to users
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {tree.map((node) => renderTreeNode(node))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Assign Manager Dialog */}
      <Dialog open={isManagerDialogOpen} onOpenChange={setIsManagerDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Assign Manager</DialogTitle>
            <DialogDescription>
              Select a manager for {selectedUser ? getUserDisplayName(selectedUser) : "this user"}.
              Users cannot be their own manager, and circular dependencies are prevented.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Manager</Label>
              <Select
                value={selectedManagerId}
                onValueChange={setSelectedManagerId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a manager" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Manager (Top Level)</SelectItem>
                  {users
                    ?.filter((u) => u.id !== selectedUser?.id) // Can't be own manager
                    .map((u) => (
                      <SelectItem key={u.id} value={u.id.toString()}>
                        {getUserDisplayName(u)} ({u.email})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {selectedUser?.manager_id && (
              <div className="text-sm text-muted-foreground">
                Current manager: {" "}
                {(() => {
                  const currentManager = users?.find(
                    (u) => u.id === selectedUser.manager_id
                  );
                  return currentManager
                    ? getUserDisplayName(currentManager)
                    : "Unknown";
                })()}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsManagerDialogOpen(false);
                setSelectedUser(null);
                setSelectedManagerId("");
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveManager}
              disabled={updateManagerMutation.isPending}
            >
              {updateManagerMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

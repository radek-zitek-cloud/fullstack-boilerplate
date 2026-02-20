import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";

export interface Permissions {
  create: "own" | "subordinates" | "all" | null;
  read: "own" | "subordinates" | "all" | null;
  update: "own" | "subordinates" | "all" | null;
  delete: "own" | "subordinates" | "all" | null;
}

const fetchPermissions = async (component: string): Promise<Permissions> => {
  const response = await api.get<Permissions>(`/admin/rbac/permissions/${component}`);
  return response.data;
};

export function usePermission(component: string) {
  const { user } = useAuth();

  const { data: permissions, isLoading } = useQuery<Permissions>({
    queryKey: ["permissions", component, user?.id],
    queryFn: () => fetchPermissions(component),
    enabled: !!user,
  });

  const can = (action: keyof Permissions): boolean => {
    return permissions?.[action] !== null && permissions?.[action] !== undefined;
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
    // For "subordinates", we'd need to check the hierarchy
    // This is a simplified version
    return false;
  };

  return { can, scope, canAccessResource, permissions, isLoading };
}

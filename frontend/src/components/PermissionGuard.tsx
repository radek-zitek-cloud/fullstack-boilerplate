import { usePermission } from "@/hooks/usePermission";

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
  fallback = null,
}: PermissionGuardProps) {
  const { can } = usePermission(component);

  if (!can(action)) {
    return fallback;
  }

  return <>{children}</>;
}

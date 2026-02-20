import { Outlet, Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { usePermission } from "@/hooks/usePermission";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LayoutDashboard, CheckSquare, LogOut, User, Settings, Shield, ClipboardList, Trash2, KeyRound, ShieldCheck, Users, Network } from "lucide-react";
import StatusBar from "./StatusBar";

function Navigation() {
  const location = useLocation();
  const { can: canAccessTasks } = usePermission("tasks");

  const hasTasksAccess = canAccessTasks("read") || canAccessTasks("create") || 
                         canAccessTasks("update") || canAccessTasks("delete");

  return (
    <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
      <Link
        to="/"
        className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
          location.pathname === "/"
            ? "border-primary text-foreground"
            : "border-transparent text-muted-foreground hover:border-border hover:text-foreground"
        }`}
      >
        <LayoutDashboard className="w-4 h-4 mr-2" />
        Dashboard
      </Link>
      {hasTasksAccess && (
        <Link
          to="/tasks"
          className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
            location.pathname === "/tasks"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:border-border hover:text-foreground"
          }`}
        >
          <CheckSquare className="w-4 h-4 mr-2" />
          Tasks
        </Link>
      )}
    </div>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <nav className="bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <span className="text-xl font-bold text-foreground">Boilerplate</span>
              </div>
              <Navigation />
            </div>
            <div className="flex items-center">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    <span className="hidden sm:inline">{user?.first_name || user?.email}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <div className="px-2 py-1.5">
                    <div className="text-sm font-medium text-foreground">
                      {user?.email}
                    </div>
                    {user?.is_admin && (
                      <div className="text-xs text-muted-foreground flex items-center mt-1">
                        <Shield className="w-3 h-3 mr-1" />
                        Administrator
                      </div>
                    )}
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/profile" className="cursor-pointer">
                      <User className="w-4 h-4 mr-2" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/settings" className="cursor-pointer">
                      <Settings className="w-4 h-4 mr-2" />
                      Settings
                    </Link>
                  </DropdownMenuItem>
                  {user?.is_admin && (
                    <>
                      <DropdownMenuItem asChild>
                        <Link to="/audit-logs" className="cursor-pointer">
                          <ClipboardList className="w-4 h-4 mr-2" />
                          Audit Logs
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link to="/trash" className="cursor-pointer">
                          <Trash2 className="w-4 h-4 mr-2" />
                          Trash
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link to="/admin/rbac" className="cursor-pointer">
                          <KeyRound className="w-4 h-4 mr-2" />
                          RBAC Management
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild className="pl-8">
                        <Link to="/admin/roles" className="cursor-pointer">
                          <ShieldCheck className="w-4 h-4 mr-2" />
                          Roles
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild className="pl-8">
                        <Link to="/admin/user-roles" className="cursor-pointer">
                          <Users className="w-4 h-4 mr-2" />
                          Users
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild className="pl-8">
                        <Link to="/admin/hierarchy" className="cursor-pointer">
                          <Network className="w-4 h-4 mr-2" />
                          Hierarchy
                        </Link>
                      </DropdownMenuItem>
                    </>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} className="cursor-pointer text-destructive">
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8 pb-20">
        <Outlet />
      </main>
      
      <StatusBar />
    </div>
  );
}

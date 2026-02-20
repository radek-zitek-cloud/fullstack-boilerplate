import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { auditApi, type AuditLog } from "@/services/audit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw, Eye, ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";

const ACTION_COLORS: Record<string, string> = {
  create: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  update: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  delete: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  read: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
  login: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
  logout: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
  password_change: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
  password_reset: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300",
};

export default function AuditLogs() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(25);
  const [tables, setTables] = useState<string[]>([]);
  const [actions, setActions] = useState<string[]>([]);
  
  // Filters
  const [filters, setFilters] = useState({
    table_name: "",
    action: "",
    user_id: "",
    record_id: "",
  });

  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  useEffect(() => {
    if (user?.is_admin) {
      fetchAuditLogs();
      fetchMetadata();
    }
  }, [user, skip, filters]);

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      const response = await auditApi.getAuditLogs({
        ...filters,
        skip,
        limit,
      });
      setLogs(response.items);
      setTotal(response.total);
    } catch (error) {
      toast.error("Failed to load audit logs");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetadata = async () => {
    try {
      const [tablesData, actionsData] = await Promise.all([
        auditApi.getAuditedTables(),
        auditApi.getAuditActions(),
      ]);
      setTables(tablesData);
      setActions(actionsData);
    } catch (error) {
      console.error("Failed to load metadata:", error);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setSkip(0); // Reset to first page when filtering
  };

  const clearFilters = () => {
    setFilters({
      table_name: "",
      action: "",
      user_id: "",
      record_id: "",
    });
    setSkip(0);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatJson = (obj: Record<string, unknown> | null) => {
    if (!obj) return "None";
    return JSON.stringify(obj, null, 2);
  };

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-64">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              You do not have permission to view audit logs. This feature is
              restricted to administrators only.
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
          <h1 className="text-2xl font-bold">Audit Logs</h1>
          <p className="text-muted-foreground">
            Track all CRUD operations and user activities across the system.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={fetchAuditLogs}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Select
              value={filters.table_name}
              onValueChange={(value) => handleFilterChange("table_name", value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Table Name" />
              </SelectTrigger>
              <SelectContent>
                {tables.map((table) => (
                  <SelectItem key={table} value={table}>
                    {table}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.action}
              onValueChange={(value) => handleFilterChange("action", value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                {actions.map((action) => (
                  <SelectItem key={action} value={action}>
                    {action}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Input
              placeholder="User ID"
              value={filters.user_id}
              onChange={(e) => handleFilterChange("user_id", e.target.value)}
              type="number"
            />

            <Input
              placeholder="Record ID"
              value={filters.record_id}
              onChange={(e) => handleFilterChange("record_id", e.target.value)}
            />
          </div>

          <div className="mt-4 flex justify-end">
            <Button variant="ghost" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Activity Log</CardTitle>
            <span className="text-sm text-muted-foreground">
              Showing {logs.length} of {total} entries
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Table</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                    </TableCell>
                  </TableRow>
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="text-center py-8 text-muted-foreground"
                    >
                      No audit logs found.
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-xs">
                        #{log.id}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={
                            ACTION_COLORS[log.action] ||
                            "bg-gray-100 text-gray-800"
                          }
                        >
                          {log.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {log.table_name}
                      </TableCell>
                      <TableCell>
                        {log.user_email || (
                          <span className="text-muted-foreground">System</span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {log.description || "-"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {formatDate(log.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setSelectedLog(log)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle>Audit Log Details</DialogTitle>
                              <DialogDescription>
                                Detailed information about this audit log entry.
                              </DialogDescription>
                            </DialogHeader>

                            {selectedLog && (
                              <div className="space-y-4 mt-4">
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <label className="text-sm font-medium">
                                      ID
                                    </label>
                                    <p className="text-sm">#{selectedLog.id}</p>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">
                                      Action
                                    </label>
                                    <Badge
                                      variant="secondary"
                                      className={
                                        ACTION_COLORS[selectedLog.action] ||
                                        ""
                                      }
                                    >
                                      {selectedLog.action}
                                    </Badge>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">
                                      Table
                                    </label>
                                    <p className="text-sm">
                                      {selectedLog.table_name}
                                    </p>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">
                                      Record ID
                                    </label>
                                    <p className="text-sm">
                                      {selectedLog.record_id || "-"}
                                    </p>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">
                                      User
                                    </label>
                                    <p className="text-sm">
                                      {selectedLog.user_email || "System"}
                                    </p>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">
                                      Timestamp
                                    </label>
                                    <p className="text-sm">
                                      {formatDate(selectedLog.created_at)}
                                    </p>
                                  </div>
                                </div>

                                {selectedLog.endpoint && (
                                  <div>
                                    <label className="text-sm font-medium">
                                      Endpoint
                                    </label>
                                    <p className="text-sm font-mono">
                                      {selectedLog.method} {selectedLog.endpoint}
                                    </p>
                                  </div>
                                )}

                                {selectedLog.ip_address && (
                                  <div>
                                    <label className="text-sm font-medium">
                                      IP Address
                                    </label>
                                    <p className="text-sm font-mono">
                                      {selectedLog.ip_address}
                                    </p>
                                  </div>
                                )}

                                {selectedLog.description && (
                                  <div>
                                    <label className="text-sm font-medium">
                                      Description
                                    </label>
                                    <p className="text-sm">
                                      {selectedLog.description}
                                    </p>
                                  </div>
                                )}

                                {selectedLog.old_values && (
                                  <div>
                                    <label className="text-sm font-medium">
                                      Old Values
                                    </label>
                                    <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-auto">
                                      {formatJson(selectedLog.old_values)}
                                    </pre>
                                  </div>
                                )}

                                {selectedLog.new_values && (
                                  <div>
                                    <label className="text-sm font-medium">
                                      New Values
                                    </label>
                                    <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-auto">
                                      {formatJson(selectedLog.new_values)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            )}
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <Button
              variant="outline"
              onClick={() => setSkip((prev) => Math.max(0, prev - limit))}
              disabled={skip === 0 || loading}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Previous
            </Button>

            <span className="text-sm text-muted-foreground">
              Page {Math.floor(skip / limit) + 1} of{" "}
              {Math.ceil(total / limit) || 1}
            </span>

            <Button
              variant="outline"
              onClick={() => setSkip((prev) => prev + limit)}
              disabled={skip + limit >= total || loading}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

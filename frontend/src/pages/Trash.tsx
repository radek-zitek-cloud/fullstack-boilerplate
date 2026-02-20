import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Loader2, RefreshCw, RotateCcw, Trash2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

interface TrashItem {
  id: number;
  type: string;
  name: string;
  deleted_at: string;
  deleted_by: string | null;
  data: Record<string, unknown>;
}

interface TrashResponse {
  items: TrashItem[];
  total: number;
  skip: number;
  limit: number;
}

export default function Trash() {
  const { user } = useAuth();
  const [items, setItems] = useState<TrashItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [emptying, setEmptying] = useState(false);

  useEffect(() => {
    if (user?.is_admin) {
      fetchTrash();
    }
  }, [user]);

  const fetchTrash = async () => {
    try {
      setLoading(true);
      const response = await api.get<TrashResponse>("/trash/");
      setItems(response.data.items);
    } catch (error) {
      toast.error("Failed to load trash items");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const restoreItem = async (type: string, id: number) => {
    try {
      setRestoring(id);
      await api.post(`/trash/restore/${type}/${id}`);
      toast.success(`${type} restored successfully`);
      fetchTrash();
    } catch (error) {
      toast.error(`Failed to restore ${type}`);
      console.error(error);
    } finally {
      setRestoring(null);
    }
  };

  const deletePermanently = async (type: string, id: number) => {
    try {
      setDeleting(id);
      await api.delete(`/trash/${type}/${id}`);
      toast.success(`${type} permanently deleted`);
      fetchTrash();
    } catch (error) {
      toast.error(`Failed to delete ${type}`);
      console.error(error);
    } finally {
      setDeleting(null);
    }
  };

  const emptyTrash = async () => {
    try {
      setEmptying(true);
      const response = await api.delete("/trash/");
      toast.success(`Trash emptied: ${response.data.deleted.users} users, ${response.data.deleted.tasks} tasks deleted`);
      fetchTrash();
    } catch (error) {
      toast.error("Failed to empty trash");
      console.error(error);
    } finally {
      setEmptying(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "user":
        return "👤";
      case "task":
        return "📋";
      default:
        return "📄";
    }
  };

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-64">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              You do not have permission to view the trash. This feature is
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
          <h1 className="text-2xl font-bold">Trash</h1>
          <p className="text-muted-foreground">
            View and restore deleted items or permanently remove them.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={fetchTrash}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            <span className="ml-2">Refresh</span>
          </Button>

          {items.length > 0 && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" disabled={emptying}>
                  {emptying ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  <span className="ml-2">Empty Trash</span>
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-destructive" />
                    Empty Trash?
                  </AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete all {items.length} items in the trash.
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={emptyTrash}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    Delete All
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Deleted Items</CardTitle>
          <CardDescription>
            {items.length === 0
              ? "Trash is empty"
              : `${items.length} item(s) in trash`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Trash2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Trash is empty</p>
              <p className="text-sm mt-1">
                Deleted items will appear here and can be restored
              </p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Deleted At</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((item) => (
                    <TableRow key={`${item.type}-${item.id}`}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span>{getTypeIcon(item.type)}</span>
                          <span className="capitalize">{item.type}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{item.name}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDate(item.deleted_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => restoreItem(item.type, item.id)}
                            disabled={restoring === item.id}
                          >
                            {restoring === item.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <RotateCcw className="w-4 h-4" />
                            )}
                            <span className="ml-1">Restore</span>
                          </Button>

                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-destructive hover:text-destructive"
                                disabled={deleting === item.id}
                              >
                                {deleting === item.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Trash2 className="w-4 h-4" />
                                )}
                                <span className="ml-1">Delete</span>
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle className="flex items-center gap-2">
                                  <AlertTriangle className="w-5 h-5 text-destructive" />
                                  Permanently Delete?
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will permanently delete the {item.type} &quot;{item.name}&quot;.
                                  This action cannot be undone.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => deletePermanently(item.type, item.id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Delete Permanently
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

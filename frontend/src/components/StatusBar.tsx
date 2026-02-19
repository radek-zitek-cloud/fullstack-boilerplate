import { useEffect, useState } from "react";
import axios from "axios";
import { CheckCircle, XCircle, Server, GitBranch } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL?.replace("/api/v1", "") || "http://localhost:8000";

export default function StatusBar() {
  const [health, setHealth] = useState<{ status: string; version?: string } | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());
  const [appVersion] = useState(import.meta.env.VITE_APP_VERSION || "0.2.0");

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`, {
        timeout: 5000,
      });
      setHealth(response.data);
      setIsOnline(true);
    } catch (error) {
      setIsOnline(false);
      setHealth(null);
    }
    setLastChecked(new Date());
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="fixed bottom-0 left-0 right-0 bg-card border-t border-border py-2 px-4 text-xs">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* App Version */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <GitBranch className="w-3 h-3" />
            <span>v{appVersion}</span>
          </div>

          {/* Separator */}
          <span className="text-border">|</span>

          {/* Backend Status */}
          <div className="flex items-center gap-1.5">
            {isOnline ? (
              <>
                <CheckCircle className="w-3 h-3 text-green-500" />
                <span className="text-green-600 dark:text-green-400">Backend Online</span>
              </>
            ) : (
              <>
                <XCircle className="w-3 h-3 text-red-500" />
                <span className="text-red-600 dark:text-red-400">Backend Offline</span>
              </>
            )}
          </div>

          {/* Backend Version */}
          {health?.version && (
            <>
              <span className="text-border">|</span>
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Server className="w-3 h-3" />
                <span>API v{health.version}</span>
              </div>
            </>
          )}
        </div>

        {/* Last Checked */}
        <div className="text-muted-foreground">
          Checked: {lastChecked.toLocaleTimeString()}
        </div>
      </div>
    </footer>
  );
}

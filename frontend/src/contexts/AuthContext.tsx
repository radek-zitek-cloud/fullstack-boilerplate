import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import api from "@/lib/api";

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  note?: string;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, first_name?: string, last_name?: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<User>) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get("/users/me");
      setUser(response.data);
    } catch (error) {
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await api.post("/auth/login", { email, password });
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    
    await fetchUser();
  };

  const register = async (email: string, password: string, first_name?: string, last_name?: string) => {
    const response = await api.post("/auth/register", { email, password, first_name, last_name });
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    
    await fetchUser();
  };

  const updateProfile = async (data: Partial<User>) => {
    const response = await api.patch("/users/me", data);
    setUser(response.data);
  };

  const changePassword = async (currentPassword: string, newPassword: string) => {
    await api.post("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfile,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

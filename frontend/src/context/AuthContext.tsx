import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, tokenStorage, apiErrorMessage } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const ended = () => { queryClient.clear(); setUser(null); setIsLoading(false); };
    window.addEventListener("session-ended", ended);
    const token = tokenStorage.getAccess() || tokenStorage.getRefresh();
    if (!token) {
      setIsLoading(false);
      return () => window.removeEventListener("session-ended", ended);
    }
    api
      .get<User>("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => tokenStorage.clear())
      .finally(() => setIsLoading(false));
    return () => window.removeEventListener("session-ended", ended);
  }, [queryClient]);

  async function login(email: string, password: string) {
    tokenStorage.clear();
    queryClient.clear();
    try {
      const { data } = await api.post("/auth/login", { email, password });
      tokenStorage.set(data.access_token, data.refresh_token);
      const me = await api.get<User>("/auth/me");
      setUser(me.data);
    } catch (error) {
      tokenStorage.clear();
      throw new Error(apiErrorMessage(error, "Não foi possível iniciar sessão."));
    }
  }

  function logout() {
    const refresh = tokenStorage.getRefresh();
    if (refresh) void api.post("/auth/logout", { refresh_token: refresh }).catch(() => {});
    tokenStorage.clear();
    queryClient.clear();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  return ctx;
}

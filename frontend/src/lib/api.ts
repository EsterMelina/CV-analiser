import axios from "axios";

const ACCESS_TOKEN_KEY = "recruiter_access_token";
const REFRESH_TOKEN_KEY = "recruiter_refresh_token";
let generation = 0;
export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  generation: () => generation,
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },
  clear: () => {
    generation++;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    window.dispatchEvent(new Event("session-ended"));
  },
};

export const api = axios.create({ baseURL: "/api", timeout: 30000 });
api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  (config as any)._sessionGeneration = generation;
  return config;
});

let refreshFlight: { generation: number; promise: Promise<void> } | null = null;
export function refreshSession(): Promise<void> {
  const started = generation;
  if (refreshFlight?.generation === started) return refreshFlight.promise;
  const refreshToken = tokenStorage.getRefresh();
  const promise = (async () => {
    try {
      if (!refreshToken) throw new Error("Sessão expirada");
      const { data } = await axios.post("/api/auth/refresh", { refresh_token: refreshToken }, { timeout: 15000 });
      if (generation !== started) throw new axios.CanceledError("Sessão alterada");
      tokenStorage.set(data.access_token, data.refresh_token);
    } catch (error) {
      if (generation === started) tokenStorage.clear();
      throw error;
    } finally {
      if (refreshFlight?.generation === started) refreshFlight = null;
    }
  })();
  refreshFlight = { generation: started, promise };
  return promise;
}

api.interceptors.response.use(
  (response) => {
    if ((response.config as any)._sessionGeneration !== generation) throw new axios.CanceledError("Sessão alterada");
    return response;
  },
  async (error) => {
    const original = error.config;
    if (!original || original._sessionGeneration !== generation) return Promise.reject(error);
    const isTokenEndpoint = ["/auth/login", "/auth/refresh", "/auth/logout"].includes(original.url);
    if (error.response?.status === 401 && !original._retry && !isTokenEndpoint) {
      original._retry = true;
      await refreshSession();
      return api(original);
    }
    return Promise.reject(error);
  }
);

export function apiErrorMessage(error: unknown, fallback = "Ocorreu um erro inesperado."): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    if (error.code === "ECONNABORTED" || error.code === "ETIMEDOUT")
      return "O servidor demorou demasiado a responder. Actualize a lista para verificar se o pedido foi guardado antes de repetir.";
    if (!error.response)
      return "Não foi possível contactar o servidor. Verifique a ligação e se a API está a correr.";
    if (error.response.status >= 500)
      return "O servidor encontrou um erro. Tente novamente; se persistir, consulte o terminal da API.";
  }
  return fallback;
}

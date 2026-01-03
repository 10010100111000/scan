import { defineStore } from "pinia";
import { ref } from "vue";
import http from "@/api/http";

interface LoginPayload {
  username: string;
  password: string;
}

interface SetupPayload {
  username: string;
  password: string;
}

interface TokenResponse {
  accessToken: string;
  tokenType?: string;
}

interface StatusResponse {
  first_run: boolean;
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("scan_token"));
  const username = ref<string | null>(null);
  const firstRun = ref<boolean | null>(null);
  const loadingStatus = ref(false);

  const setToken = (value: string | null) => {
    token.value = value;
    if (value) {
      localStorage.setItem("scan_token", value);
    } else {
      localStorage.removeItem("scan_token");
    }
  };

  const fetchStatus = async () => {
    if (loadingStatus.value) return firstRun.value;
    loadingStatus.value = true;
    try {
      const { data } = await http.get<{ data: StatusResponse }>("/api/auth/status");
      firstRun.value = data.data.first_run;
    } catch {
      firstRun.value = false;
    } finally {
      loadingStatus.value = false;
    }
    return firstRun.value;
  };

  const login = async (payload: LoginPayload) => {
    const { data } = await http.post<{ data: TokenResponse }>("/api/auth/login", payload);
    setToken(data.data.accessToken);
    username.value = payload.username;
  };

  const setupAdmin = async (payload: SetupPayload) => {
    await http.post("/api/auth/setup", payload);
    firstRun.value = false;
  };

  const logout = () => {
    setToken(null);
    username.value = null;
  };

  return {
    token,
    username,
    firstRun,
    loadingStatus,
    setToken,
    fetchStatus,
    login,
    setupAdmin,
    logout,
  };
});

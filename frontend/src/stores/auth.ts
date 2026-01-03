import { defineStore } from "pinia";
import { ref } from "vue";
import apiClient from "@/utils/http";

interface LoginPayload {
  username: string;
  password: string;
}

interface TokenResponse {
  accessToken: string;
  tokenType?: string;
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("access_token"));
  const username = ref<string | null>(null);

  const setToken = (value: string | null) => {
    token.value = value;
    if (value) {
      localStorage.setItem("access_token", value);
    } else {
      localStorage.removeItem("access_token");
    }
  };

  const login = async (payload: LoginPayload) => {
    const { data } = await apiClient.post<{ data: TokenResponse }>("/auth/login", payload);
    setToken(data.data.accessToken);
    username.value = payload.username;
  };

  const logout = () => {
    setToken(null);
    username.value = null;
  };

  return {
    token,
    username,
    setToken,
    login,
    logout,
  };
});

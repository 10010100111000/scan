import axios from "axios";
import router from "@/router";

const apiBase = import.meta.env.VITE_API_BASE || "";

const http = axios.create({
  baseURL: apiBase,
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("scan_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("scan_token");
      router.replace("/login");
    }
    return Promise.reject(error);
  }
);

export default http;

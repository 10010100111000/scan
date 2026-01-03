import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
});

// 自动附加 Authorization
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("scan_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (username, password) => {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const res = await api.post("/api/v1/auth/login", form);
  return res.data;
};

export const registerAdmin = async (payload) => {
  const res = await api.post("/api/v1/auth/admin/init", payload);
  return res.data;
};

export const forgotPassword = async (payload) => {
  const res = await api.post("/api/v1/auth/forgot", payload);
  return res.data;
};

export const fetchAuthStatus = async () => {
  const res = await api.get("/api/v1/auth/status");
  return res.data;
};

export const createOrganization = async (name) => {
  const res = await api.post("/api/v1/orgs/organizations", { name });
  return res.data;
};

export const createAsset = async (orgId, payload) => {
  const res = await api.post(`/api/v1/orgs/${orgId}/assets`, payload);
  return res.data;
};

export const triggerScan = async (assetId, configName) => {
  const res = await api.post(`/api/v1/assets/${assetId}/scan`, { config_name: configName });
  return res.data;
};

export const getTask = async (id) => {
  const res = await api.get(`/api/v1/tasks/${id}`);
  return res.data;
};

export const listTasks = async (params = {}) => {
  const res = await api.get("/api/v1/tasks", { params });
  return res.data;
};

export const fetchPorts = async (assetId) => {
  const res = await api.get(`/api/v1/results/assets/${assetId}/ports`);
  return res.data;
};

export const fetchWeb = async (assetId) => {
  const res = await api.get(`/api/v1/results/assets/${assetId}/web`);
  return res.data;
};

export const fetchVulns = async (assetId) => {
  const res = await api.get(`/api/v1/results/assets/${assetId}/vulns`);
  return res.data;
};

export const fetchHosts = async (assetId) => {
  const res = await api.get(`/api/v1/results/assets/${assetId}/hosts`);
  return res.data.items || [];
};

export const fetchScanConfigs = async () => {
  const res = await api.get("/api/v1/assets/scan-configs");
  return res.data;
};

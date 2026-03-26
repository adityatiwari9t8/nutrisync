import axios from "axios";

const STORAGE_TOKEN_KEY = "nutrisync_token";
const STORAGE_USER_KEY = "nutrisync_user";
let unauthorizedHandler = null;

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(STORAGE_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearAuth();
      if (unauthorizedHandler) {
        unauthorizedHandler();
      }
    }
    return Promise.reject(error);
  },
);

export const storeAuth = (payload) => {
  localStorage.setItem(STORAGE_TOKEN_KEY, payload.access_token);
  localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(payload.user));
};

export const clearAuth = () => {
  localStorage.removeItem(STORAGE_TOKEN_KEY);
  localStorage.removeItem(STORAGE_USER_KEY);
};

export const setUnauthorizedHandler = (handler) => {
  unauthorizedHandler = handler;
};

export const getStoredUser = () => {
  const raw = localStorage.getItem(STORAGE_USER_KEY);
  return raw ? JSON.parse(raw) : null;
};

export const getStoredToken = () => localStorage.getItem(STORAGE_TOKEN_KEY);

export const getErrorMessage = (error, fallback = "Something went wrong.") =>
  error?.response?.data?.error || error?.message || fallback;

export default api;

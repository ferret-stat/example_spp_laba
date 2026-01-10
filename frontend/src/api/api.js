import axios from "axios";

const API_URL = "/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((p) => {
    error ? p.reject(error) : p.resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) return Promise.reject(error);

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      isRefreshing = true;

      try {
        const response = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newToken = response.data.access_token;
        localStorage.setItem("access_token", newToken);
        api.defaults.headers.common.Authorization = `Bearer ${newToken}`;

        processQueue(null, newToken);
        return api(originalRequest);
      } catch (e) {
        processQueue(e);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        return Promise.reject(e);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;

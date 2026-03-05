import axios from "axios";

const api = axios.create({
  // Uses VITE_API_URL when set (Render deployment).
  // Falls back to "" so Vite's dev-server proxy handles /api/* locally.
  baseURL: import.meta.env.VITE_API_URL || "",
  withCredentials: true,
});

export default api;
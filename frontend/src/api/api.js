import axios from "axios";

const api = axios.create({
  baseURL: "https://ml-life-span.onrender.com",
  withCredentials: true
});

export default api;
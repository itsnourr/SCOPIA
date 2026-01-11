import axios from "axios";

const API = "http://localhost:8443/api/colmap";

export const runColmap = () =>
  axios.get(`${API}/run`);

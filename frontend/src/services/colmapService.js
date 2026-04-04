import axios from "axios";
const API = "http://localhost:8443/api/colmap";

export const runColmap = (caseId) =>
  axios.get(`${API}/run?caseId=${caseId}`);

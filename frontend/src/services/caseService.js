import axios from "axios";

const API = "http://localhost:8443/api/case";

export const getAllActiveCases = () =>
  axios.get(`${API}/all`);

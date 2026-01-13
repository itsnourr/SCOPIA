import axios from "axios";
// TODO: Change hardocded case-key to one passed from route (or earlier file importing this function) 
const API = "http://localhost:8443/api/colmap";

export const runColmap = (caseKey) =>
  axios.get(`${API}/run?caseKey=${caseKey}`);

import axios from "axios";

const API = "http://localhost:8443/api/graph";

export const loadGraph = (caseId) =>
  axios.get(`${API}/${caseId}`);

export const saveGraph = (graph) =>
  axios.post(`${API}/`, graph);

// export const addNode = (caseId, node) =>
//   axios.post(`${API}/${caseId}/nodes`, node);

// export const addLink = (caseId, link) =>
//   axios.post(`${API}/${caseId}/links`, link);

// export const deleteNode = (caseId, nodeId) =>
//   axios.delete(`${API}/${caseId}/nodes/${nodeId}`);

// export const deleteLink = (linkId) =>
//   axios.delete(`${API}/${caseId}/links/${linkId}`);

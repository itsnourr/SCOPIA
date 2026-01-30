import axios from "axios";

const API = "/api/graph";

export const loadGraph = (caseKey) =>
  axios.get(`${API}/${caseKey}`);

export const addNode = (caseKey, node) =>
  axios.post(`${API}/${caseKey}/nodes`, node);

export const addLink = (caseKey, link) =>
  axios.post(`${API}/${caseKey}/links`, link);

export const deleteNode = (caseKey, nodeId) =>
  axios.delete(`${API}/${caseKey}/nodes/${nodeId}`);

export const deleteLink = (linkId) =>
  axios.delete(`${API}/${caseKey}/links/${linkId}`);

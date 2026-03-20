import axios from "axios";

const API = "http://localhost:8443/api/suspect";

export const getAllSuspects = () =>
  axios.get(`${API}/all`);

export const getSuspectsByCaseId = (caseId) =>
  axios.get(`${API}/case/${caseId}`);

export const createSuspect = (suspect) =>
  axios.post(`${API}/create`, suspect);

export const createSuspectToCase = (caseId, suspect) =>
  axios.post(`${API}/create/case/${caseId}`, suspect);

export const updateSuspect = (id, suspect) =>
  axios.put(`${API}/update/${id}`, suspect);

export const deleteSuspect = (id) =>
  axios.delete(`${API}/delete/${id}`);
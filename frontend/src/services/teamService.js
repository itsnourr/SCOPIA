import axios from "axios";

const API = "http://localhost:8443/api/team";

export const getAllTeams = () =>
  axios.get(API);

export const getTeamByCaseId = (caseId) =>
  axios.get(`${API}/${caseId}`);

export const addMemberToTeam = (caseId, userId) =>
  axios.post(`${API}/${caseId}/members/${userId}`);

export const removeMemberFromTeam = (caseId, userId) =>
  axios.delete(`${API}/${caseId}/members/${userId}`);

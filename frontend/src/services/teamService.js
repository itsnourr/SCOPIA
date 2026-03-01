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

// TeamService.js
// PURE STATIC JSON — NO API, NO MUTATION

// Static team data matching your 6 cases
// const teamsData = [
//   { caseId: 1, userIds: [101, 102] },
//   { caseId: 2, userIds: [103] },
//   { caseId: 3, userIds: [] },
//   { caseId: 4, userIds: [101] },
//   { caseId: 5, userIds: [104, 105] },
//   { caseId: 6, userIds: [] }
// ];

// // ---------------- DUMMY GET ALL ----------------
// export const getAllTeams = () => {
//   return new Promise((resolve) => {
//     resolve({ data: teamsData });
//   });
// };
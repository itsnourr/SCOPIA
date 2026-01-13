import axios from "axios";

const API = "http://localhost:8443/api/assignee";

/* Coworker: Users assigned to the current case */
export const getUsersForCurrentCase = (caseId) =>
  axios.get(`${API}/case/${caseId}/users`);

/* Leader: All users with role "criminologist" */
export const getCriminologists = () =>
  axios.get(`${API}/criminologists`);

/* Superadmin: All users */
export const getAllUsers = () =>
  axios.get(`${API}/all`);

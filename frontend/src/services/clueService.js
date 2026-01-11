import axios from "axios";

const API = "http://localhost:8443/api/clue";

export const getAllClues = () =>
  axios.get(`${API}/all`);

export const createClue = (clue) =>
  axios.post(`${API}/create`, clue);

export const updateClue = (id, clue) =>
  axios.put(`${API}/update/${id}`, clue);

export const deleteClue = (id) =>
  axios.delete(`${API}/delete/${id}`);

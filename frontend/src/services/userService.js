import axios from "axios";

const API = "http://localhost:8443/api/user"; 

export const login = (username, password) => {
  return axios.post(`${API}/login`, {
    username,
    password
  });
};

export const signup = (username, password) => {
  return axios.post(`${API}/signup`, {
    username,
    password
  });
};

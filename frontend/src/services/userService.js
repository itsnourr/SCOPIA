import axios from "axios";
import { navigate } from "@reach/router";

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

export const logout = () => {
  localStorage.removeItem("currentUserId");
  navigate("/login");
}

export const mapUserIdToUsername = (userId) => {
  return axios.get(`${API}/id/${userId}/username`);
};

export const getCurrentUserId = () => {
  return localStorage.getItem("currentUserId");
};
import axios from "axios";
// import { navigate } from "@react/router";

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
  // navigate("/login");
}

// export const mapUserIdToUsername = (userId) => {
//   const res =  axios.get(`${API}/id/${userId}/username`);
//   console.log(res);
//   return res.data.username;    
// };

export const mapUserIdToUsername = async (userId) => {
  const res = await axios.get(`${API}/id/${userId}/username`);
  console.log("returned" + res.data); // 
  return res.data; // just return the string
};

export const mapUserIdToUsernameByBulk = async (userIds) => {
  const res = await axios.get(`${API}/usernames`, {
    params: { ids: userIds } // axios handles ?ids=1,2,3
  });

  return res.data; // { 1: "john", 2: "sarah" }
};

export const getCurrentUserId = () => {
  return localStorage.getItem("currentUserId");
};

// Returns the currently logged-in username
export function getCurrentUsername() {
  const userId = getCurrentUserId();
  if (!userId) {
    return null; // No user logged in
  }
  return mapUserIdToUsername(userId); // Returns a promise that resolves to the username
}

export function validatePassword(password) {
  return axios.post(`${API}/password/validate`, 
    { username: getCurrentUsername(), password: password });
}

export function changePassword(newPassword) {
  return axios.post(`${API}/password/change`, { username: getCurrentUsername(), password: newPassword });
}
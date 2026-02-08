import axios from "axios";

const API = "http://localhost:8443/api/case";

export const getAllCases = async () => {
  const response = await axios.get(`${API}/all`);
  return response.data;
};

export const getAllOpenCases = async () => {
  const response = await axios.get(`${API}/all/open`);
  return response.data;
};

export const getAllActiveCases = async () => {
  const response = await axios.get(`${API}/all/open`);
  return response.data;
};

export const getAllArchivedCases = async () => {
  const response = await axios.get(`${API}/all/archived`);
  return response.data;
};

export const getMyOpenCases = async () => {
  const response = await axios.get(`${API}/all/open`);
  return response.data;
};

export const getMyArchivedCases = async () => {
  const response = await axios.get(`${API}/all/archived`);
  return response.data;
};

export const createCase = async ({ caseKey, caseName, description }) => {
  const response = await axios.post(`${API}/create`, {
    caseKey,
    caseName,
    description,
  });
  return response.data;
};

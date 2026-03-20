import axios from "axios";

const API = "http://localhost:8443/api/case";

// get case details by id
export const getCaseById = async (caseId) => {
  const response = await axios.get(`${API}/${caseId}`);
  return response.data;
}

export const getAllCases = async () => {
  const response = await axios.get(`${API}/all`);
  return response.data;
}; 

export const getAllOpenCases = async () => {
  const response = await axios.get(`${API}/all/open`);
  return response.data;
};

export const getAllActiveCases = () => {
  const mockCases = [
    { caseId: 1 },
    { caseId: 2 },
    { caseId: 3 },
    { caseId: 4 },
    { caseId: 5 },
    { caseId: 6 },
  ];

  return Promise.resolve({ data: mockCases });
};

export const getAllArchivedCases = async () => {
  const response = await axios.get(`${API}/all/archived`);
  return response.data;
};

export const getMyOpenCases = async () => {
  const username = localStorage.getItem("currentUsername");
  const response = await axios.get(`${API}/all/open/${username}`);
  console.log("Fetched open cases for user:", username, response.data);
  return response.data;
};

export const getMyArchivedCases = async () => {
  const username = localStorage.getItem("currentUsername");
  const response = await axios.get(`${API}/all/archived/${username}`);
  console.log("Fetched archived cases for user:", username, response.data);
  return response.data;
};

export const createCase = async ({ caseKey, caseName, description }) => {
  const response = await axios.post(`${API}/create`, {
    caseKey,
    caseName,
    description,
    status: "open"
  });
  return response.data;
};

export const archiveCase = async (caseId) => {
  const response = await axios.post(`${API}/archive/${caseId}`);
  return response.data;
};

export const updateCase = async (caseId, { caseKey, caseName, description }) => {
  const response = await axios.put(`${API}/update/${caseId}`, {
    caseKey,
    caseName,
    description
  });
  return response.data;
};

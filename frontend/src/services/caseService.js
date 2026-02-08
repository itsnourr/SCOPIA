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

export const getAllActiveCases = async () => { // to be deleted
  const response = await axios.get(`${API}/all/open`);
  return response.data;
};

export const getAllArchivedCases = async () => {
  const response = await axios.get(`${API}/all/archived`);
  return response.data;
};

// export const getMyOpenCases = async () => {
//   const response = await axios.get(`${API}/all/open`);
//   return response.data;
// };

export const getMyOpenCases = async () => { // delete later, uncomment above
  // TEMP: frontend-only dummy data
  return [
    {
      caseId: 1,
      caseName: "Bank Robbery - Downtown",
      description: "Armed robbery reported at downtown bank branch.",
      createdAt: "2025-02-01T10:15:30",
      status: "open",
      teamAssignedId: 3,
      location: "Downtown Beirut",
      coordinates: "33.8938,35.5018",
      reportDate: "2025-02-01T09:45:00",
      crimeTime: "2025-02-01T09:30:00"
    },
    {
      caseId: 2,
      caseName: "Warehouse Fire Investigation",
      description: "Suspicious fire broke out in an abandoned warehouse.",
      createdAt: "2025-02-03T14:20:00",
      status: "open",
      teamAssignedId: 5,
      location: "Port Area",
      coordinates: "33.9012,35.5195",
      reportDate: "2025-02-03T13:50:00",
      crimeTime: "2025-02-03T13:10:00"
    },
    {
      caseId: 3,
      caseName: "Missing Person Case",
      description: "Adult male reported missing for 48 hours.",
      createdAt: "2025-02-05T08:05:10",
      status: "open",
      teamAssignedId: 2,
      location: "Hamra",
      coordinates: "33.8986,35.4822",
      reportDate: "2025-02-05T07:40:00",
      crimeTime: null
    }
  ];
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

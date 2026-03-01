import axios from "axios";

const API = "http://localhost:8443/api/suspect";

// export const getAllSuspects = () =>
//   axios.get(`${API}/all`);

export const getAllSuspects = async () => { // delete later, uncomment above
  return {
    data: [
      {
        suspectId: 1,
        full_name: "Karim Haddad",
        alias: "The Fox",
        date_of_birth: "1991-04-12",
        nationality: "Lebanese"
      },
      {
        suspectId: 2,
        full_name: "Sami Khalil",
        alias: "Ghost",
        date_of_birth: "1988-09-21",
        nationality: "Syrian"
      },
      {
        suspectId: 3,
        full_name: "Nour Rajeh",
        alias: "Shadow",
        date_of_birth: "1995-01-03",
        nationality: "Lebanese"
      },
      {
        suspectId: 4,
        full_name: "Cezar El Khatib",
        alias: "Falcon",
        date_of_birth: "1985-07-18",
        nationality: "Jordanian"
      },
      {
        suspectId: 5,
        full_name: "Ali Mansour",
        alias: "Viper",
        date_of_birth: "1993-11-27",
        nationality: "Lebanese"
      },
      {
        suspectId: 6,
        full_name: "Rami Trad",
        alias: "Hunter",
        date_of_birth: "1990-06-14",
        nationality: "Palestinian"
      },
      {
        suspectId: 7,
        full_name: "Tarek Nassar",
        alias: "Phantom",
        date_of_birth: "1987-02-08",
        nationality: "Egyptian"
      },
      {
        suspectId: 8,
        full_name: "Youssef Saleh",
        alias: "Wolf",
        date_of_birth: "1992-12-30",
        nationality: "Lebanese"
      }
    ]
  };
};

export const createSuspect = (suspect) =>
  axios.post(`${API}/create`, suspect);

export const updateSuspect = (id, suspect) =>
  axios.put(`${API}/update/${id}`, suspect);

export const deleteSuspect = (id) =>
  axios.delete(`${API}/delete/${id}`);
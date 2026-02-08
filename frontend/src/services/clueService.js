import axios from "axios";

const API = "http://localhost:8443/api/clue";

// export const getAllClues = () => 
//   axios.get(`${API}/all`);

export const getAllClues = async () => { // delete later, uncomment above
  return { data:[
    {
      clueId: 1,
      type: "Physical",
      category: "Weapon",
      pickerId: 12,
      clueDesc: "Knife found near the victim with partial fingerprints.",
      coordinates: "33.8938,35.5018"
    },
    {
      clueId: 2,
      type: "Digital",
      category: "Phone",
      pickerId: 8,
      clueDesc: "Deleted messages recovered from suspect's phone.",
      coordinates: "33.8986,35.4822"
    },
    {
      clueId: 3,
      type: "Witness",
      category: "Statement",
      pickerId: 15,
      clueDesc: "Witness saw a man wearing a black jacket leaving the area.",
      coordinates: "33.8986,35.4822"
    },
    {
      clueId: 4,
      type: "Forensic",
      category: "DNA",
      pickerId: 4,
      clueDesc: "Blood sample collected from broken window.",
      coordinates: "33.9012,35.5195"
    },
    {
      clueId: 5,
      type: "Physical",
      category: "Weapon",
      pickerId: 12,
      clueDesc: "Knife found near the victim with partial fingerprints.",
      coordinates: "33.8938,35.5018"
    },
    {
      clueId: 6,
      type: "Digital",
      category: "Phone",
      pickerId: 8,
      clueDesc: "Deleted messages recovered from suspect's phone.",
      coordinates: "33.8986,35.4822"
    },
    {
      clueId: 7,
      type: "Witness",
      category: "Statement",
      pickerId: 15,
      clueDesc: "Witness saw a man wearing a black jacket leaving the area.",
      coordinates: "33.8986,35.4822"
    },
    {
      clueId: 8,
      type: "Forensic",
      category: "DNA",
      pickerId: 4,
      clueDesc: "Blood sample collected from broken window.",
      coordinates: "33.9012,35.5195"
    },
    {
      clueId: 9,
      type: "Physical",
      category: "Weapon",
      pickerId: 12,
      clueDesc: "Knife found near the victim with partial fingerprints and we do not really know what happenned afterwards, that's terrifying.",
      coordinates: "33.8938,35.5018"
    },
    {
      clueId: 10,
      type: "Digital",
      category: "Phone",
      pickerId: 8,
      clueDesc: "Deleted messages recovered from suspect's phone.",
      coordinates: "33.8986,35.4822"
    },
    {
      clueId: 11,
      type: "Witness",
      category: "Statement",
      pickerId: 15,
      clueDesc: "Witness saw a man wearing a black jacket leaving the area.",
      coordinates: "33.8986,35.4822"
    },
    {
      clueId: 12,
      type: "Forensic",
      category: "DNA",
      pickerId: 4,
      clueDesc: "Blood sample collected from broken window.",
      coordinates: "33.9012,35.5195"
    }
  ]};
};


export const createClue = (clue) =>
  axios.post(`${API}/create`, clue);

export const updateClue = (id, clue) =>
  axios.put(`${API}/update/${id}`, clue);

export const deleteClue = (id) =>
  axios.delete(`${API}/delete/${id}`);

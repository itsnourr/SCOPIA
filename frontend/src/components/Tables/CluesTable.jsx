import { useEffect, useState } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Button } from "primereact/button";
import { InputText } from "primereact/inputtext";
import { Dialog } from "primereact/dialog";
import { Dropdown } from "primereact/dropdown";

import UserSelector from "../Selectors/UserSelector"; // adjust path if needed

import {
  getAllClues,
  createClue,
  updateClue,
  deleteClue
} from "../../services/clueService";

export default function CluesTable() {

  // ---------------- State ----------------

  const emptyClue = () => ({
    clueId: null,
    type: "",
    category: "",
    pickerId: "",
    clueDesc: "",
    coordinates: ""
  });

  const [clues, setClues] = useState([]);
  const [loading, setLoading] = useState(false);

  const [dialogVisible, setDialogVisible] = useState(false);
  const [dialogMode, setDialogMode] = useState("create"); // create | edit

  const [newClue, setNewClue] = useState(emptyClue());
  const [selectedUserId, setSelectedUserId] = useState("");

  // ---------------- Effects ----------------

  useEffect(() => {
    loadClues();
  }, []);

  const loadClues = async () => {
    setLoading(true);
    const res = await getAllClues();
    setClues(res.data);
    setLoading(false);
  };

  // ---------------- CRUD ----------------

  const openCreateDialog = () => {
    setDialogMode("create");
    setNewClue(emptyClue());
    setSelectedUserId("");
    setDialogVisible(true);
  };

  const openEditDialog = (rowData) => {
    setDialogMode("edit");
    setNewClue(rowData);
    setSelectedUserId(rowData.pickerId);
    setDialogVisible(true);
  };

  const saveClue = async () => {
    const payload = {
      ...newClue,
      pickerId: selectedUserId
    };

    if (dialogMode === "create") {
      const res = await createClue(payload);
      setClues((prev) => [...prev, res.data]);
    } else {
      await updateClue(payload.clueId, payload);
      setClues((prev) =>
        prev.map((c) => (c.clueId === payload.clueId ? payload : c))
      );
    }

    setDialogVisible(false);
    setNewClue(emptyClue());
  };

  const removeClue = async (rowData) => {
    await deleteClue(rowData.clueId);
    setClues((prev) =>
      prev.filter((c) => c.clueId !== rowData.clueId)
    );
  };

  // ---------------- Classification ----------------

  const clueSubcategoryToCategoryMap = {
    // Object Evidence
    "Weapon": "Object",
    "Knife": "Object",
    "Gun": "Object",
    "Blunt Object": "Object",
    "Tool": "Object",
    "Crowbar": "Object",
    "Screwdriver": "Object",
    "Clothing": "Object",
    "Shoes": "Object",
    "Broken Glass": "Object",
    "Paint Chips": "Object",
    "Rope": "Object",
    "Tape": "Object",

    // Biological Evidence
    "Blood": "Biological",
    "Saliva": "Biological",
    "Semen": "Biological",
    "Hair": "Biological",
    "Skin Cells": "Biological",
    "Touch DNA": "Biological",
    "Tissue": "Biological",
    "Bone": "Biological",

    // Trace Evidence
    "Fiber": "Trace",
    "Glass Fragments": "Trace",
    "Soil": "Trace",
    "Gunshot Residue": "Trace",
    "GSR": "Trace",
    "Pollen": "Trace",

    // Impression Evidence
    "Fingerprint": "Impression",
    "Latent Fingerprint": "Impression",
    "Patent Fingerprint": "Impression",
    "Plastic Fingerprint": "Impression",
    "Footprint": "Impression",
    "Shoe Print": "Impression",
    "Tire Track": "Impression",
    "Bite Mark": "Impression",
    "Tool Mark": "Impression",

    // Digital Evidence
    "Mobile Phone": "Digital",
    "Phone Data": "Digital",
    "Call Log": "Digital",
    "SMS": "Digital",
    "Email": "Digital",
    "GPS Location": "Digital",
    "Computer File": "Digital",
    "Social Media Activity": "Digital",
    "CCTV Recording": "Digital",

    // Document Evidence
    "Note": "Document",
    "Contract": "Document",
    "Receipt": "Document",
    "Passport": "Document",
    "ID Document": "Document",
    "Handwritten Letter": "Document",
    "Forged Document": "Document",

    // Chemical Evidence
    "Drug": "Chemical",
    "Narcotic": "Chemical",
    "Poison": "Chemical",
    "Accelerant": "Chemical",
    "Explosive Residue": "Chemical",
    "Toxic Substance": "Chemical",

    // Ballistics Evidence
    "Bullet": "Ballistics",
    "Cartridge Case": "Ballistics",
    "Shell Casing": "Ballistics",
    "Firearm": "Ballistics",
    "Trajectory Marking": "Ballistics",

    // Environmental Evidence
    "Plant Material": "Environmental",
    "Leaf": "Environmental",
    "Water Sample": "Environmental",
    "Weather Condition": "Environmental",
    "Animal Trace": "Environmental",
    "Scene Layout Characteristic": "Environmental"
  };

  const clueCategories = [
    "Ballistics",
    "Environmental",
    "Object",
    "Biological",
    "Chemical",
    "Trace",
    "Document",
    "Digital",
    "Impression",
    "Other"
  ];

  const clueTypeOptions = [
    ...clueCategories,
    ...Object.keys(clueSubcategoryToCategoryMap)
  ];

  const dropdownOptions = clueTypeOptions.map((opt) => ({
    label: opt,
    value: opt
  }));

  const onTypeChange = (value) => {
    if (clueSubcategoryToCategoryMap[value]) {
      setNewClue({
        ...newClue,
        type: value,
        category: clueSubcategoryToCategoryMap[value]
      });
    } else {
      setNewClue({
        ...newClue,
        type: "Other",
        category: value
      });
    }
  };

  // ---------------- Table Templates ----------------

  const editTemplate = (rowData) => (
    <Button
      icon="pi pi-pencil"
      className="p-button-text"
      onClick={() => openEditDialog(rowData)}
    />
  );

  const deleteTemplate = (rowData) => (
    <Button
      icon="pi pi-trash"
      className="p-button-danger p-button-text"
      onClick={() => removeClue(rowData)}
    />
  );

  // ---------------- Render ----------------

  return (
    <>
      <Button
        label="Add Clue"
        icon="pi pi-plus"
        className="mb-3"
        onClick={openCreateDialog}
      />

      <DataTable
        value={clues}
        paginator
        rows={10}
        loading={loading}
        dataKey="clueId"
      >
        <Column field="clueId" header="ID" style={{ width: "80px" }} />
        <Column field="type" header="Type" />
        <Column field="category" header="Category" />
        <Column field="pickerId" header="Picker" />
        <Column field="clueDesc" header="Description" />
        <Column field="coordinates" header="Coordinates" />
        <Column body={editTemplate} style={{ width: "4rem" }} />
        <Column body={deleteTemplate} style={{ width: "4rem" }} />
      </DataTable>

      {/* Create / Edit Dialog */}
      <Dialog
        header={dialogMode === "create" ? "Add New Clue" : "Edit Clue"}
        visible={dialogVisible}
        style={{ width: "450px" }}
        onHide={() => setDialogVisible(false)}
      >
        <div className="p-fluid">

          <label>Type / Category</label>
          <Dropdown
            value={
              newClue.type !== "Other"
                ? newClue.type
                : newClue.category
            }
            options={dropdownOptions}
            onChange={(e) => onTypeChange(e.value)}
            placeholder="Select or search"
            filter
          />

          <label>Picker</label>
          <UserSelector
            assignerStatus="admin"
            value={selectedUserId}
            onChange={setSelectedUserId}
          />

          <label>Description</label>
          <InputText
            value={newClue.clueDesc}
            onChange={(e) =>
              setNewClue({ ...newClue, clueDesc: e.target.value })
            }
          />

          <label>Coordinates</label>
          <InputText
            value={newClue.coordinates}
            onChange={(e) =>
              setNewClue({ ...newClue, coordinates: e.target.value })
            }
          />
        </div>

        <div className="flex justify-content-end mt-3">
          <Button
            label="Save"
            icon="pi pi-check"
            onClick={saveClue}
          />
        </div>
      </Dialog>
    </>
  );
}

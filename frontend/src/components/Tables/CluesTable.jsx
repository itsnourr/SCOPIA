import { useEffect, useState } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Button } from "primereact/button";
import { InputText } from "primereact/inputtext";
import { Dialog } from "primereact/dialog";

import {
  getAllClues,
  createClue,
  updateClue,
  deleteClue
} from "../../services/clueService";

export default function CluesTable() {
  const [clues, setClues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogVisible, setDialogVisible] = useState(false);
  const [newClue, setNewClue] = useState(emptyClue());

  useEffect(() => {
    loadClues();
  }, []);

  function emptyClue() {
    return {
      type: "",
      pickerId: "",
      clueDesc: "",
      coordinates: "",
      annotationLink: ""
    };
  }

  const loadClues = async () => {
    setLoading(true);
    const res = await getAllClues();
    setClues(res.data);
    setLoading(false);
  };

  // ---------------- CRUD ----------------

  const saveNewClue = async () => {
    await createClue(newClue);
    setDialogVisible(false);
    setNewClue(emptyClue());
    loadClues();
  };

  const onRowEditComplete = async (e) => {
    const { newData } = e;
    await updateClue(newData.id, newData);
    loadClues();
  };

  const removeClue = async (rowData) => {
    await deleteClue(rowData.id);
    loadClues();
  };

  // ---------------- Editors ----------------

  const textEditor = (options) => (
    <InputText
      value={options.value}
      onChange={(e) => options.editorCallback(e.target.value)}
    />
  );

  const deleteTemplate = (rowData) => (
    <Button
      icon="pi pi-trash"
      className="p-button-danger p-button-text"
      onClick={() => removeClue(rowData)}
    />
  );

  return (
    <>
      <Button
        label="Add Clue"
        icon="pi pi-plus"
        className="mb-3"
        onClick={() => setDialogVisible(true)}
      />

      <DataTable
        value={clues}
        paginator
        rows={10}
        loading={loading}
        editMode="row"
        dataKey="id"
        onRowEditComplete={onRowEditComplete}
      >
        <Column field="id" header="ID" style={{ width: "80px" }} />
        <Column field="type" header="Type" editor={textEditor} />
        <Column field="pickerId" header="Picker ID" editor={textEditor} />
        <Column field="clueDesc" header="Description" editor={textEditor} />
        <Column field="coordinates" header="Coordinates" editor={textEditor} />
        <Column field="annotationLink" header="Annotation" editor={textEditor} />
        <Column rowEditor style={{ width: "8rem" }} />
        <Column body={deleteTemplate} style={{ width: "4rem" }} />
      </DataTable>

      {/* Add Clue Dialog */}
      <Dialog
        header="Add New Clue"
        visible={dialogVisible}
        style={{ width: "450px" }}
        onHide={() => setDialogVisible(false)}
      >
        <div className="p-fluid">
          <label>Type</label>
          <InputText value={newClue.type}
            onChange={(e) => setNewClue({ ...newClue, type: e.target.value })}
          />

          <label>Picker ID</label>
          <InputText value={newClue.pickerId}
            onChange={(e) => setNewClue({ ...newClue, pickerId: e.target.value })}
          />

          <label>Description</label>
          <InputText value={newClue.clueDesc}
            onChange={(e) => setNewClue({ ...newClue, clueDesc: e.target.value })}
          />

          <label>Coordinates</label>
          <InputText value={newClue.coordinates}
            onChange={(e) => setNewClue({ ...newClue, coordinates: e.target.value })}
          />

          <label>Annotation Link</label>
          <InputText value={newClue.annotationLink}
            onChange={(e) => setNewClue({ ...newClue, annotationLink: e.target.value })}
          />
        </div>

        <div className="flex justify-content-end mt-3">
          <Button label="Save" icon="pi pi-check" onClick={saveNewClue} />
        </div>
      </Dialog>
    </>
  );
}

import { useEffect, useState } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Button } from "primereact/button";
import { InputText } from "primereact/inputtext";
import { Dialog } from "primereact/dialog";
import "./CluesTable.css";

import {
  getAllSuspects,
  createSuspect,
  updateSuspect,
  deleteSuspect
} from "../../services/suspectService";

export default function SuspectsTable() {

  // ---------------- State ----------------

  const emptySuspect = () => ({
    suspectId: null,
    full_name: "",
    alias: "",
    date_of_birth: "",
    nationality: ""
  });

  const [suspects, setSuspects] = useState([]);
  const [loading, setLoading] = useState(false);

  const [dialogVisible, setDialogVisible] = useState(false);
  const [dialogMode, setDialogMode] = useState("create"); // create | edit
  const [newSuspect, setNewSuspect] = useState(emptySuspect());

  // ---------------- Effects ----------------

  useEffect(() => {
    loadSuspects();
  }, []);

  const loadSuspects = async () => {
    setLoading(true);
    const res = await getAllSuspects();
    setSuspects(res.data);
    setLoading(false);
  };

  // ---------------- CRUD ----------------

  const openCreateDialog = () => {
    setDialogMode("create");
    setNewSuspect(emptySuspect());
    setDialogVisible(true);
  };

  const openEditDialog = (rowData) => {
    setDialogMode("edit");
    setNewSuspect(rowData);
    setDialogVisible(true);
  };

  const saveSuspect = async () => {
    if (dialogMode === "create") {
      const res = await createSuspect(newSuspect);
      setSuspects((prev) => [...prev, res.data]);
    } else {
      await updateSuspect(newSuspect.suspectId, newSuspect);
      setSuspects((prev) =>
        prev.map((s) =>
          s.suspectId === newSuspect.suspectId ? newSuspect : s
        )
      );
    }

    setDialogVisible(false);
    setNewSuspect(emptySuspect());
  };

  const removeSuspect = async (rowData) => {
    await deleteSuspect(rowData.suspectId);
    setSuspects((prev) =>
      prev.filter((s) => s.suspectId !== rowData.suspectId)
    );
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
      onClick={() => removeSuspect(rowData)}
    />
  );

  // ---------------- Render ----------------

  return (
    <>
      <div className="clue-table-container">
        <DataTable
          value={suspects}
          paginator
          rows={5}
          loading={loading}
          dataKey="suspectId"
          style={{ width: "900px"}}
        >
          <Column field="suspectId" header="ID" style={{ width: "40px" }} />
          <Column field="full_name" header="Full Name" />
          <Column field="alias" header="Alias" />
          <Column field="date_of_birth" header="Date of Birth" />
          <Column field="nationality" header="Nationality" />
          <Column body={editTemplate} style={{ width: "4rem" }} />
          <Column body={deleteTemplate} style={{ width: "4rem" }} />
        </DataTable>
      </div>

      <Button
        label="Add Suspect"
        icon="pi pi-plus"
        className="mb-3 p-white-button"
        style={{ marginTop: "12px" }}
        onClick={openCreateDialog}
      />

      {/* Create / Edit Dialog */}
      <Dialog
        header={dialogMode === "create" ? "Add New Suspect" : "Edit Suspect"}
        visible={dialogVisible}
        style={{ width: "450px" }}
        onHide={() => setDialogVisible(false)}
        closable={false}
        dismissableMask={true}
      >
        <div className="p-fluid clue-form">

          <label>Full Name</label>
          <InputText
            value={newSuspect.full_name}
            onChange={(e) =>
              setNewSuspect({ ...newSuspect, full_name: e.target.value })
            }
          />

          <label>Alias</label>
          <InputText
            value={newSuspect.alias}
            onChange={(e) =>
              setNewSuspect({ ...newSuspect, alias: e.target.value })
            }
          />

          <label>Date of Birth</label>
          <InputText
            type="date"
            value={newSuspect.date_of_birth}
            onChange={(e) =>
              setNewSuspect({ ...newSuspect, date_of_birth: e.target.value })
            }
          />

          <label>Nationality</label>
          <InputText
            value={newSuspect.nationality}
            onChange={(e) =>
              setNewSuspect({ ...newSuspect, nationality: e.target.value })
            }
          />
        </div>

        <div className="flex justify-content-end mt-3" style={{ marginTop: "12px" }}>
          <Button
            label="Save"
            icon="pi pi-check"
            onClick={saveSuspect}
            style={{ color: "white" }}
          />
        </div>
      </Dialog>
    </>
  );
}
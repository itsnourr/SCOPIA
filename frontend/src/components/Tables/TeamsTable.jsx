import { useEffect, useState } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Tag } from "primereact/tag";

import UserSelector from "../Selectors/UserSelector";

import {
  getAllTeams,
  getTeamByCaseId,
  addMemberToTeam,
  removeMemberFromTeam
} from "../../services/TeamService";

import {
  getAllActiveCases
} from "../../services/CaseService";

import "../../App.css"

export default function TeamsTable() {

  // ---------------- State ----------------

  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);

  const [dialogVisible, setDialogVisible] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [teamMembers, setTeamMembers] = useState([]);

  const [selectedUserId, setSelectedUserId] = useState(null);

  // ---------------- Effects ----------------

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
  setLoading(true);

  const [casesRes, teamsRes] = await Promise.all([
    getAllActiveCases(),
    getAllTeams()
  ]);

  const cases = casesRes.data;
  const teams = teamsRes.data;

  // Map caseId → team
  const teamMap = new Map(
    teams.map((t) => [t.caseId, t.userIds])
  );

  // Ensure ALL cases exist, even with empty teams
  const merged = cases.map((c) => ({
    caseId: c.caseId,
    userIds: teamMap.get(c.caseId) || []
  }));

  setTeams(merged);
  setLoading(false);
};


  // ---------------- Team Dialog ----------------

  const openTeamDialog = async (rowData) => {
    setSelectedCaseId(rowData.caseId);

    const res = await getTeamByCaseId(rowData.caseId);
    setTeamMembers(res.data.userIds);

    setSelectedUserId(null);
    setDialogVisible(true);
  };

  const closeDialog = () => {
    setDialogVisible(false);
    setSelectedCaseId(null);
    setTeamMembers([]);
  };

  // ---------------- Member Actions ----------------

  const addMember = async () => {
    if (!selectedUserId) return;

    await addMemberToTeam(selectedCaseId, selectedUserId);

    setTeamMembers((prev) =>
      prev.includes(selectedUserId)
        ? prev
        : [...prev, selectedUserId]
    );

    setSelectedUserId(null);
  };

  const removeMember = async (userId) => {
    await removeMemberFromTeam(selectedCaseId, userId);

    setTeamMembers((prev) =>
      prev.filter((id) => id !== userId)
    );
  };

  // ---------------- Templates ----------------

  const membersTemplate = (rowData) => (
    <span>{rowData.userIds.length}</span>
  );

  const manageTemplate = (rowData) => (
    <Button
      icon="pi pi-users"
      className="p-button-text"
      onClick={() => openTeamDialog(rowData)}
    />
  );

  const memberTagTemplate = (userId) => (
    <Tag
      key={userId}
      value={`User ${userId}`}
      className="mr-2 mb-2"
      icon="pi pi-user"
      onClick={() => removeMember(userId)}
      style={{ cursor: "pointer", marginRight: "8px", marginTop: "8px" }} 
    />
  );

  // ---------------- Render ----------------

  return (
    <>
      <DataTable
        value={teams}
        paginator
        rows={10}
        loading={loading}
        dataKey="caseId"
      >
        <Column field="caseId" header="Case ID" />
        <Column
          header="Members"
          body={membersTemplate}
          style={{ width: "120px" }}
        />
        <Column
          body={manageTemplate}
          header="Manage"
          style={{ width: "120px" }}
        />
      </DataTable>

      {/* Team Management Dialog */}
      <Dialog
        header={`Manage Team – Case ${selectedCaseId}`}
        visible={dialogVisible}
        style={{ width: "450px" }}
        onHide={closeDialog}
        closable={false} 
        dismissableMask={true}
      >
        <div className="p-fluid">
          <div style={{marginBottom:"8px", fontWeight:"bold"}}>
            <label>Add Member</label>
          </div>

          <div className="flex gap-2">
            <UserSelector
              assignerStatus="admin"
              value={selectedUserId}
              onChange={setSelectedUserId}
            />
    
              <Button
              icon="pi pi-plus"
              onClick={addMember}
              />
          </div>

          <div style={{marginTop:"12px", fontWeight:"bold"}}>
            <label className="mt-3" >Current Members</label>
          </div>

          <div className="flex flex-wrap mt-2" style={{ marginBottom: "12px"}}>
            {teamMembers.length === 0 && (
              <small className="text-gray-400">
                No members assigned
              </small>
            )}

            {teamMembers.map((userId) =>
              memberTagTemplate(userId)
            )}
          </div>

          <small className="text-gray-500 mt-2 block" style={{ fontStyle: "italic"}}>
            *Click a member to remove them from the team
          </small>
        </div>
      </Dialog>
    </>
  );
}

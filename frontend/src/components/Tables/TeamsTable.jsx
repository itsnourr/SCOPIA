import { useEffect, useState } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Tag } from "primereact/tag";

import UserSelector from "../Selectors/UserSelector";
import "./CluesTable.css";

import {
  getAllTeams,
  getTeamByCaseId,
  addMemberToTeam,
  removeMemberFromTeam
} from "../../services/teamService";

import {
  getAllCases, getCaseKeyById
} from "../../services/caseService";

import "../../App.css"
import { mapUserIdToUsernameByBulk } from "../../services/userService";

export default function TeamsTable() {

  // ---------------- State ----------------

  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(false);

  const [dialogVisible, setDialogVisible] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [caseMap, setCaseMap] = useState({});
  const [teamMembers, setTeamMembers] = useState([]);
  const [usernames, setUsernames] = useState({});

  const [selectedUserId, setSelectedUserId] = useState(null);

  // ---------------- Effects ----------------

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setLoading(true);

    const [casesRes, teamsRes] = await Promise.all([
      getAllCases(),
      getAllTeams()
    ]);
    // let's add console logs for debugging
    const cases = casesRes;
    const teams = teamsRes.data;
    console.log("Fetched cases:", cases);
    console.log("Fetched teams:", teams);

    // Map caseId → caseKey
    const caseMap = {};
    cases.forEach((c) => {
      caseMap[c.caseId] = c.caseKey || c.caseId;
    });
    setCaseMap(caseMap);
    console.log("CASE MAP:", caseMap);

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

  const caseTemplate = (rowData) => {
    return caseMap[rowData.caseId] || rowData.caseId;
  };

  // ---------------- Team Dialog ----------------

  const openTeamDialog = async (rowData) => {
    
    setSelectedCaseId(rowData.caseId);

    const res = await getTeamByCaseId(rowData.caseId);
    setTeamMembers(res.data.userIds);
    const usernamesRes = await mapUserIdToUsernameByBulk(res.data.userIds);
    setUsernames(usernamesRes);
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
      value={usernames[userId] || "Loading..."}
      className="mr-2 mb-2"
      icon="pi pi-user"
      onClick={() => removeMember(userId)}
      style={{ cursor: "pointer", marginRight: "8px", marginTop: "8px" }} 
    />
  );

  // ---------------- Render ----------------

  return (
    <>
    <div className="clue-table-container">
      <DataTable
        key={JSON.stringify(caseMap)}   
        value={teams}
        paginator
        rows={10}
        loading={loading}
        dataKey="caseId"
      >
        <Column header="Case" body={caseTemplate} style={{ width: "120px" }}/>
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
    </div>
      {/* Team Management Dialog */}
      <Dialog
        header={`Manage Team`}
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

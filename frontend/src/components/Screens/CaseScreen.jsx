import React from "react";
import { useEffect } from "react";

import { getCaseById, updateCaseDetails } from "../../services/caseService";
import { getTeamByCaseId } from "../../services/teamService";
import { mapUserIdToUsernameByBulk } from "../../services/userService";

export default function CaseScreen() {

  const [currentCaseid, setCurrentCaseId] = React.useState(-1);
  const [caseData, setCaseData] = React.useState(null);
  const [teamMembers, setTeamMembers] = React.useState([]);
  const [isEditing, setIsEditing] = React.useState(false);
  const [formData, setFormData] = React.useState({});

  const labelStyle = {
    color: "#9ca3af",
    fontSize: "14px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "4px",
  };

  const valueStyle = {
    fontSize: "16px",
    fontWeight: "500",
    color: "#f3f4f6",
  };

  const refreshCase = async () => {
    try {
      const data = await getCaseById(currentCaseid);
      setCaseData(data);
      setFormData({
        location: data.location || "",
        coordinates: data.coordinates || "",
        reportDate: data.reportDate || "",
        crimeTime: data.crimeTime || ""
      });
    } catch (error) {
      console.error("Error refreshing case:", error);
    }
  };

  const handleSave = async () => {
    try {
      const payload = {
        location: formData.location,
        coordinates: formData.coordinates,
        reportDate: formData.reportDate
          ? `${formData.reportDate}T00:00:00`
          : null,
        crimeTime: formData.crimeTime
          ? `1970-01-01T${formData.crimeTime}:00`
          : null
      };

      await updateCaseDetails(currentCaseid, payload);

      setIsEditing(false);
      await refreshCase();

    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    // read caseid from route, we are at /case/4 might contain /info at the end
    const pathParts = window.location.pathname.split("/");
    const caseId = pathParts[pathParts.length - 1] === "info" ? pathParts[pathParts.length - 2] : pathParts[pathParts.length - 1];
    setCurrentCaseId(caseId);

    const fetchCaseData = async () => {
      try {
        const data = await getCaseById(caseId);
        setCaseData(data);
        setFormData({
          location: data.location || "",
          coordinates: data.coordinates || "",
          reportDate: data.reportDate || "",
          crimeTime: data.crimeTime || ""
        });
      }
      catch (error) {
        console.error("Error fetching case data:", error);
      }
    };

    const fetchTeamMembers = async () => {
      try {
        const teamData = await getTeamByCaseId(caseId);
        const userIds = teamData.data.userIds;
        const idToUsernameMap = await mapUserIdToUsernameByBulk(userIds);
        const usernames = userIds.map(id => idToUsernameMap[id] || `User ${id}`);
        setTeamMembers(usernames);
      }
      catch (error) {
        console.error("Error fetching team members:", error);
      }
    };

    fetchCaseData();
    fetchTeamMembers();
  }, []);

  return (
    <div style={{ padding: "40px", color: "#f3f4f6" }}>
      <h1 style={{ fontSize: "32px", fontWeight: "600", marginBottom: "20px", marginTop: "-40px", textAlign: "start" }}>
        Case Info
      </h1>

      {/* Main Card */}
      <div
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "16px",
          padding: "30px",
          boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
          backdropFilter: "blur(6px)",
          width: "700px",
        }}
      >
        {/* Description */}
        <div style={{ marginBottom: "30px" }}>
          <div style={{...labelStyle, textAlign: "start"}}>Description</div>
          <div style={{ ...valueStyle, lineHeight: "1.6", maxWidth: "800px", textAlign: "start" }}>
            {caseData?.description}
          </div>
        </div>

        {/* Status */}
        

        {/* Metadata Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: "25px",
            marginBottom: "30px",
          }}
        >
          <div>
            <div style={labelStyle}>Identifier</div>
            <div style={valueStyle}>{caseData?.caseKey}</div>
          </div>

          <div style={{ marginTop: "-6px" }}>
          <div style={labelStyle}>Status</div>
          <span
            style={{
              display: "inline-block",
              padding: "6px 14px",
              borderRadius: "20px",
              fontSize: "14px",
              fontWeight: "600",
              background: "rgba(34,197,94,0.15)",
              color: "#22c55e",
              border: "1px solid rgba(34,197,94,0.3)",
            }}
          >
            {caseData?.status}
          </span>
        </div>
          <div>
            <div style={labelStyle}>Location</div>

            {isEditing ? (
              <input
                value={formData.location}
                onChange={(e) =>
                  setFormData({ ...formData, location: e.target.value })
                }
              />
            ) : (
              <div style={valueStyle}>{caseData?.location}</div>
            )}
          </div>

          <div>
            <div style={labelStyle}>Coordinates</div>

            {isEditing ? (
              <input
                value={formData.coordinates}
                onChange={(e) =>
                  setFormData({ ...formData, coordinates: e.target.value })
                }
              />
            ) : (
              <div style={valueStyle}>
                {caseData?.coordinates ? `(${caseData.coordinates})` : "—"}
              </div>
            )}
          </div>

          <div>
            <div style={labelStyle}>Report Date</div>

            {isEditing ? (
              <input
                type="date"
                value={formData.reportDate?.split("T")[0] || ""}
                onChange={(e) =>
                  setFormData({ ...formData, reportDate: e.target.value })
                }
              />
            ) : (
              <div style={valueStyle}>
                {caseData?.reportDate?.split("T")[0]}
              </div>
            )}
          </div>

          <div>
            <div style={labelStyle}>Crime Time</div>

            {isEditing ? (
              <input
                type="time"
                value={formData.crimeTime?.split("T")[1]?.slice(0, 5) || ""}
                onChange={(e) =>
                  setFormData({ ...formData, crimeTime: e.target.value })
                }
              />
            ) : (
              <div style={valueStyle}>
                {caseData?.crimeTime?.split("T")[1]?.split(".")[0]}
              </div>
            )}
          </div>

        </div>

        {!isEditing && (
          <button onClick={() => setIsEditing(true)}>Edit</button>
        )}

        {isEditing && (
          <button onClick={handleSave}>Save</button>
        )}

        {/* Team Members */}
        <div>
          <div style={{ ...labelStyle, marginBottom: "12px", textAlign: "start", marginTop: "10px" }}>
            Team Members Assigned
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "10px"}}>
            {teamMembers.map((member, index) => (
              <div
                key={index}
                style={{
                  padding: "8px 14px",
                  borderRadius: "12px",
                  background: "rgba(59,130,246,0.1)",
                  border: "1px solid rgba(59,130,246,0.25)",
                  fontSize: "14px",
                  fontWeight: "500",
                }}
              >
                {member.split(" ").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
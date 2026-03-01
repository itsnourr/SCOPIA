import React from "react";

export default function CaseScreen() {
  const caseData = {
    description:
      "Burglary reported at a residential property. Forced entry through rear door. Multiple electronic items missing. There's a lot more details that are yet to be uncovered during investigation time, but for now, and by the looks of it, it defintely looks way more suspicious than it actually should be, according to our expert team.",
    status: "Open",
    caseKey: "BYB-201",
    location: "Blat, Byblos",
    coordinates: {
      lat: 40.7128,
      lng: -74.006,
    },
    reportDate: "2026-02-20",
    crimeTime: "2026-02-19 23:45",
    teamMembers: ["Nour Rajeh", "Sami Trad", "Cezar El Khatib"],
  };

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
        }}
      >
        {/* Description */}
        <div style={{ marginBottom: "30px" }}>
          <div style={{...labelStyle, textAlign: "start"}}>Description</div>
          <div style={{ ...valueStyle, lineHeight: "1.6", maxWidth: "800px", textAlign: "start" }}>
            {caseData.description}
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
            <div style={valueStyle}>{caseData.caseKey}</div>
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
            {caseData.status}
          </span>
        </div>

          <div>
            <div style={labelStyle}>Location</div>
            <div style={valueStyle}>{caseData.location}</div>
          </div>

          <div>
            <div style={labelStyle}>Coordinates</div>
            <div style={valueStyle}>
              {caseData.coordinates.lat}, {caseData.coordinates.lng}
            </div>
          </div>

          <div>
            <div style={labelStyle}>Report Date</div>
            <div style={valueStyle}>{caseData.reportDate}</div>
          </div>

          <div>
            <div style={labelStyle}>Crime Time</div>
            <div style={valueStyle}>{caseData.crimeTime}</div>
          </div>
        </div>

        {/* Team Members */}
        <div>
          <div style={{ ...labelStyle, marginBottom: "12px", textAlign: "start", marginTop: "10px" }}>
            Team Members Assigned
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "10px"}}>
            {caseData.teamMembers.map((member, index) => (
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
                {member}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
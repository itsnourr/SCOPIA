import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { runColmap } from "../../services/colmapService";

export default function StudioScreen() {
  const { caseKey } = useParams();   
  const [status, setStatus] = useState("");

  const handleRunColmap = async () => {
    if (!caseKey) {
      setStatus("Missing case key in URL");
      return;
    }

    setStatus("Running Colmap...");
    try {
      const response = await runColmap(caseKey); // <-- pass dynamically
      setStatus(response.data);
    } catch (error) {
      setStatus(
        error.response?.data || "Error running Colmap"
      );
    }
  };

  return (
    <div>
      <div>3D Studio</div>

      <div style={{ marginBottom: "10px" }}>
        Case: <strong>{caseKey}</strong>
      </div>

      <button onClick={handleRunColmap}>
        Run Colmap
      </button>

      {status && (
        <pre style={{ marginTop: "10px" }}>
          {status}
        </pre>
      )}
    </div>
  );
}

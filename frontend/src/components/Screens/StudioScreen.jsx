import React, { useState } from "react";
import { runColmap } from "../../services/colmapService";

export default function StudioScreen() {
  const [status, setStatus] = useState("");

  const handleRunColmap = async () => {
    setStatus("Running Colmap...");
    try {
      const response = await runColmap();
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

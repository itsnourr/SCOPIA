import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { runColmap } from "../../services/colmapService";

export default function PipelineScreen() {
  const [status, setStatus] = useState("");
  const [currentCaseId, setCurrentCaseId] = useState(null);
  const mountRef = useRef(null);
 
  const { caseId } = useParams();

  useEffect(() => {
      // read caseid from route, we are at /2/pipeline 
      const pathParts = window.location.pathname.split("/");
      const caseId = pathParts[pathParts.length - 2];
      setCurrentCaseId(caseId);
  }, []);

  const handleRunColmap = async () => {
    if (!currentCaseId) {
      setStatus("Missing case ID in URL");
      return;
    }

    setStatus("Running Colmap...");
    try {
      const response = await runColmap(currentCaseId);
      setStatus(response.data);
    } catch (error) {
      setStatus(error.response?.data || "Error running Colmap");
    }
  };

  return (
    <div>
      <h1 style={{ paddingBottom: "0px", marginBottom: "0px", color: "white" }}>Pipeline</h1>

      <button onClick={handleRunColmap} style={{ marginTop: "50px"}}>
        Run Colmap
      </button>

      <button style={{ marginLeft: "10px"}}>
        Terminate
      </button>

      {status && (
        <pre style={{ marginTop: "40px", color: "white" }}>
          {status}
        </pre>
      )}
    </div>
  );
}
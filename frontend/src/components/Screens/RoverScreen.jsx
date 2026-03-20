import { useState } from "react";
import { addRoverCluesByBulk } from "../../services/clueService";

export default function RoverScreen() {
  const [status, setStatus] = useState("");
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) return;

    if (
      selectedFile.type !== "application/json" &&
      !selectedFile.name.endsWith(".json")
    ) {
      setStatus("❌ Please upload a valid JSON file");
      return;
    }

    setFile(selectedFile);
    setStatus(`Selected file: ${selectedFile.name}`);
  };

  const handleRoverData = async () => {
    if (!file) {
      setStatus("❌ No file selected");
      return;
    }

    const pathParts = window.location.pathname.split("/");
    const caseId = pathParts[pathParts.length - 2];

    try {
      const text = await file.text();

      let jsonData;
      try {
        jsonData = JSON.parse(text); 
      } catch (err) {
        setStatus("❌ Invalid JSON format");
        return;
      }

      console.log("Extracted JSON:", jsonData);

      await addRoverCluesByBulk(caseId, jsonData);

      setStatus("✅ JSON processed successfully");
    } catch (error) {
      console.error(error);
      setStatus("❌ Error reading file");
    }
  };

  return (
    <div>
      <h1 style={{ color: "white" }}>Rover Data</h1>
        <h3 style={{ color: "white" }}>Upload clues-detected.json</h3>

      <input
        type="file"
        accept=".json,application/json"
        onChange={handleFileChange}
        style={{ marginTop: "20px", color: "white" }}
      />

      <button onClick={handleRoverData} style={{ marginTop: "20px" }}>
        Upload Rover Data
      </button>

      {status && (
        <pre style={{ marginTop: "40px", color: "white" }}>
          {status}
        </pre>
      )}
    </div>
  );
}
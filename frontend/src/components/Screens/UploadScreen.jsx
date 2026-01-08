import React, { useState } from "react";
import { RadioButton } from "primereact/radiobutton";
import { Dropdown } from "primereact/dropdown";
import { InputText } from "primereact/inputtext";
import { Button } from "primereact/button";
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';

export default function UploadScreen() {
  const [existingCase, setExistingCase] = useState(null); // 'yes' or 'no'
  const [selectedCase, setSelectedCase] = useState(null);
  const [newCaseName, setNewCaseName] = useState("");

  // Hardcoded case options
  const caseOptions = [
    { label: "Burglary at Riverside", value: "Burglary at Riverside" },
    { label: "Warehouse Arson", value: "Warehouse Arson" },
    { label: "Highway Hit & Run", value: "Highway Hit & Run" }
  ];

  const handleSubmit = () => {
    if (existingCase === "yes") {
      console.log("Selected existing case:", selectedCase);
    } else if (existingCase === "no") {
      console.log("New case name:", newCaseName);
    }
    // Logic to handle submission will go here later
    // navigate back to /cases
  };

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-3xl font-semibold mb-4">Upload Case Files</h1>

      {/* Radio buttons */}
      <div className="mb-4">
        <label className="mr-4">
          <RadioButton
            inputId="existingYes"
            name="existingCase"
            value="yes"
            onChange={(e) => setExistingCase(e.value)}
            checked={existingCase === "yes"}
          />
          <span className="ml-2">Existing case</span>
        </label>

        <label>
          <RadioButton
            inputId="existingNo"
            name="existingCase"
            value="no"
            onChange={(e) => setExistingCase(e.value)}
            checked={existingCase === "no"}
          />
          <span className="ml-2">New case</span>
        </label>
      </div>

      {/* Conditional input */}
      {existingCase === "yes" && (
        <Dropdown
          value={selectedCase}
          options={caseOptions}
          onChange={(e) => setSelectedCase(e.value)}
          placeholder="Select a case"
          className="w-full mb-4"
        />
      )}

      {existingCase === "no" && (
        <div className="mb-4">
          <InputText
            value={newCaseName}
            onChange={(e) => setNewCaseName(e.target.value)}
            placeholder="Enter new case name"
            className="w-full"
          />
        </div>
      )}

      {/* Submit button */}
      <Button
        label="Submit"
        onClick={handleSubmit}
        disabled={
          (existingCase === "yes" && !selectedCase) ||
          (existingCase === "no" && !newCaseName)
        }
      />
    </div>
  );
}

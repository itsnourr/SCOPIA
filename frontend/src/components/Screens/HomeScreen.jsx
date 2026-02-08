import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "primereact/card";
import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
import { InputTextarea } from "primereact/inputtextarea";
import './HomeScreen.css';

import { getAllCases, createCase } from "../../services/CaseService";

export default function HomeScreen() {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [caseKey, setCaseKey] = useState('');
  const [caseName, setCaseName] = useState('');
  const [caseDescription, setCaseDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [createSuccess, setCreateSuccess] = useState(false);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
  try {
    setLoading(true);

    const data = await getAllCases();
    console.log("API Response:", data);

    const casesWithTitles = data.map((caseItem, index) => {
      const caseId =
        caseItem.caseid ||
        caseItem.caseId ||
        caseItem.id ||
        caseItem.ID;

      return {
        ...caseItem,
        title:
          caseItem.caseName ||
          caseItem.title ||
          `Case ${caseId || index + 1}`,
      };
    });

    setCases(casesWithTitles);
    setError(null);
  } catch (err) {
    console.error("Error fetching cases:", err);
    setError(err.message || "Failed to load cases");
  } finally {
    setLoading(false);
  }
};


  const handleCreateCase = async () => {
  if (!caseName.trim()) {
    setCreateError("Case name is required");
    return;
  }

  try {
    setCreating(true);
    setCreateError(null);
    setCreateSuccess(false);

    const result = await createCase({
      caseName,
      description: caseDescription || "",
    });

    console.log("Case created successfully:", result);

    setCreateSuccess(true);

    // Reset form
    setCaseName("");
    setCaseDescription("");
    setShowCreateDialog(false);

    // Refresh list
    await fetchCases();

    setTimeout(() => setCreateSuccess(false), 3000);
  } catch (err) {
    console.error("Error creating case:", err);
    setCreateError(err.message || "Failed to create case");
  } finally {
    setCreating(false);
  }
};


  const handleOpenCreateDialog = () => {
    setCaseName('');
    setCaseDescription('');
    setCreateError(null);
    setCreateSuccess(false);
    setShowCreateDialog(true);
  };

  return (
    <div className="p-4">
      <h1 className="text-3xl mb-4 font-semibold">Cases</h1>

      {/* Create New Case Button */}
      <div className="mb-4">
        <button
          onClick={handleOpenCreateDialog}
          className="p-button p-component p-button-primary"
        >
          Create New Case
        </button>
        {createSuccess && (
          <p className="text-green-500 mt-2">Case created successfully!</p>
        )}
        {createError && (
          <p className="text-red-500 mt-2">Error: {createError}</p>
        )}
      </div>

      {/* Create Case Dialog */}
      <Dialog
        header="Create New Case"
        visible={showCreateDialog}
        style={{ width: '50vw' }}
        onHide={() => setShowCreateDialog(false)}
        footer={
          <div>
            <button
              onClick={() => setShowCreateDialog(false)}
              className="p-button p-component p-button-secondary"
              disabled={creating}
            >
              Cancel
            </button>
            <button
              onClick={handleCreateCase}
              className="p-button p-component p-button-primary ml-2"
              disabled={creating || !caseName.trim()}
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        }
      >
        <div className="mb-3">
          <label htmlFor="caseKey" className="block mb-2">
            Case Key *
          </label>
          <InputText
            id="caseKey"
            value={caseId}
            onChange={(e) => setCaseKey(e.target.value)}
            placeholder="e.g. GHI-003"
            className="w-full"
          />
        </div>

        <div className="p-fluid">
          <div className="mb-3">
            <label htmlFor="caseName" className="block mb-2">Case Name *</label>
            <InputText
              id="caseName"
              value={caseName}
              onChange={(e) => setCaseName(e.target.value)}
              placeholder="Enter case name"
              className="w-full"
            />
          </div>
          <div className="mb-3">
            <label htmlFor="caseDescription" className="block mb-2">Description</label>
            <InputTextarea
              id="caseDescription"
              value={caseDescription}
              onChange={(e) => setCaseDescription(e.target.value)}
              placeholder="Enter case description (optional)"
              rows={4}
              className="w-full"
            />
          </div>
        </div>
      </Dialog>

      {/* Loading State */}
      {loading && <p>Loading cases...</p>}

      {/* Error State */}
      {error && <p className="text-red-500">Error loading cases: {error}</p>}

      {/* Cases Grid */}
      {!loading && !error && (
        <div className="cases-grid">
          {cases.length === 0 ? (
            <p>No cases found.</p>
          ) : (
            cases.map(caseItem => {
              // Try multiple possible field names
              const caseId = caseItem.caseid || caseItem.caseId || caseItem.id || caseItem.ID;
              console.log('Navigating with caseId:', caseId, 'Full caseItem:', caseItem); // Debug
              return (
                <div
                  key={caseId}
                  className="case-item"
                  onClick={() => {
                    if (caseId) {
                      navigate(`/cases/${caseId}`);
                    } else {
                      console.error('No case ID found for case:', caseItem);
                    }
                  }}
                >
                  <Card
                    title={caseItem.title}
                    subTitle={caseItem.description}
                    className="cursor-pointer shadow-2 border-round-xl"
                  />
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

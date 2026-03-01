import React from "react";

export default function CatalogScreen() {
  const sections = [
    {
      title: "About Scopia",
      content:
        "Scopia is a digital forensics platform designed to help investigators collect, analyze, and visualize digital evidence. The system centralizes investigation data, maintains evidence integrity, and provides analytical dashboards to support forensic workflows."
    },
    {
      title: "Key Capabilities",
      items: [
        "Centralized case management",
        "Evidence cataloging and metadata indexing",
        "Timeline reconstruction of events",
        "Interactive investigation dashboards",
        "Searchable evidence repository"
      ]
    },
    {
      title: "Investigation Workflow",
      items: [
        "Evidence ingestion and metadata extraction",
        "Case assignment and investigator collaboration",
        "Automated analysis pipelines",
        "Visualization through dashboards and reports",
        "Exportable forensic reports"
      ]
    },
    {
      title: "Supported Evidence Types",
      items: [
        "Log files and system traces",
        "Network traffic captures",
        "Disk images and file systems",
        "Application activity records",
        "User-generated digital artifacts"
      ]
    },
    {
      title: "Security & Evidence Integrity",
      content:
        "Scopia enforces strict evidence integrity through cryptographic hashing, audit logs, and role-based access control. Every action performed within a case is tracked to preserve the forensic chain of custody."
    },
    {
      title: "Technical Information",
      items: [
        "Backend: Containerized microservices",
        "Database: Structured evidence metadata storage",
        "Visualization: Grafana dashboards",
        "Deployment: Cloud-based infrastructure",
        "API-based architecture for extensibility"
      ]
    }
  ];

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "auto" }}>
      <h1  className="screen-title">User Catalog</h1>

      {sections.map((section, index) => (
        <div
          key={index}
          style={{
            border: "1px solid #ddd",
            borderRadius: "8px",
            padding: "1.5rem",
            marginTop: "1.5rem",
            color: "white",
            // align to the left
            textAlign: "left",
          }}
        >
          <h2>{section.title}</h2>

          {section.content && <p>{section.content}</p>}

          {section.items && (
            <ul>
              {section.items.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}
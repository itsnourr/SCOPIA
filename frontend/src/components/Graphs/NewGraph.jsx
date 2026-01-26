// src/components/Graphtools/NewGraph.jsx
import React, { useMemo, useCallback, useEffect } from "react";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import "reactflow/dist/style.css";

/**
 * ==============================
 * Dummy DB-like data
 * ==============================
 */

const suspects = [
  { suspect_id: 1, name: "Suspect A" },
  { suspect_id: 2, name: "Suspect B" },
];

const clues = [{ clue_id: 100, label: "Clue X" }];

const nodesTable = [
  { node_id: 10, node_type: "SUSPECT", node_reference: 1 },
  { node_id: 11, node_type: "SUSPECT", node_reference: 2 },
  { node_id: 12, node_type: "CLUE", node_reference: 100 },
];

const linksTable = [
  { link_id: 1000, node_id_from: 10, node_id_to: 11, link_desc: "threatened", is_bidirectional: false },
  { link_id: 1002, node_id_from: 10, node_id_to: 11, link_desc: "siblings", is_bidirectional: true },
  { link_id: 1003, node_id_from: 10, node_id_to: 12, link_desc: "threw", is_bidirectional: false },
];

/**
 * ==============================
 * Lookup maps
 * ==============================
 */

const suspectById = Object.fromEntries(suspects.map(s => [s.suspect_id, s]));
const clueById = Object.fromEntries(clues.map(c => [c.clue_id, c]));

function resolveNodeLabel(node) {
  let label = "Unknown";

  if (node.node_type === "SUSPECT") {
    label = suspectById[node.node_reference]?.name ?? "Unknown Suspect";
  }

  if (node.node_type === "CLUE") {
    label = clueById[node.node_reference]?.label ?? "Unknown Clue";
  }

  console.log("🔎 resolveNodeLabel", node, "→", label);
  return label;
}

/**
 * ==============================
 * Component
 * ==============================
 */

export default function NewGraph() {

  /** -------- LOG RAW TABLES -------- */
  useEffect(() => {
    console.group("📦 RAW DB TABLES");
    console.log("suspects:", suspects);
    console.log("clues:", clues);
    console.log("nodesTable:", nodesTable);
    console.log("linksTable:", linksTable);
    console.groupEnd();
  }, []);

  /** -------- BUILD NODES -------- */
  const rfNodes = useMemo(() => {
    console.group("🧱 BUILDING RF NODES");

    const nodes = nodesTable.map((n, index) => {
      const node = {
        id: String(n.node_id),
        draggable: true,
        data: {
          label: resolveNodeLabel(n),
          nodeType: n.node_type,
        },
        position: {
          x: 100 + index * 220,
          y: n.node_type === "CLUE" ? 300 : 100,
        },
        style: {
          padding: 10,
          borderRadius: 8,
          border: "1px solid #999",
          background: n.node_type === "SUSPECT" ? "#2f2f2f" : "#444",
          color: "#fff",
          minWidth: 120,
          textAlign: "center",
          cursor: "grab"
        },
      };

      console.log("🟦 RF Node:", node);
      return node;
    });

    console.log("✅ Final RF Nodes:", nodes);
    console.groupEnd();
    return nodes;
  }, []);

  /** -------- BUILD EDGES -------- */
  const rfEdges = useMemo(() => {
    console.group("🔗 BUILDING RF EDGES");

    const edges = [];

    linksTable.forEach((l) => {
      const baseEdge = {
        source: String(l.node_id_from),
        target: String(l.node_id_to),
        label: l.link_desc,
        style: { strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed },
      };

      if (l.is_bidirectional) {
        const edge = {
          ...baseEdge,
          id: `link-${l.link_id}-bi`,
          markerStart: { type: MarkerType.ArrowClosed },
        };
        console.log("↔ Bidirectional Edge:", edge);
        edges.push(edge);
      } else {
        const edge = {
          ...baseEdge,
          id: `link-${l.link_id}`,
        };
        console.log("→ Edge:", edge);
        edges.push(edge);
      }
    });

    console.log("✅ Final RF Edges:", edges);
    console.groupEnd();
    return edges;
  }, []);

  /** -------- CLICK DEBUG -------- */
  const onNodeClick = useCallback((_, node) => {
    console.log("🖱️ NODE CLICKED:", node);
  }, []);

  const onEdgeClick = useCallback((_, edge) => {
    console.log("🖱️ EDGE CLICKED:", edge);
  }, []);

  /** -------- RENDER -------- */
  console.log("🎨 Rendering ReactFlow");

  return (
    <div style={{ width: "1000px", height: "1000px" }}>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        fitView
        nodesDraggable
        panOnScroll
        zoomOnPinch
        drag
      >
        <Background gap={16} color="#555" />
        <Controls />
      </ReactFlow>
    </div>
  );
}

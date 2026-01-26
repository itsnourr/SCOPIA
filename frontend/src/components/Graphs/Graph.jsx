import React, { useMemo, useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

/**
 * ==============================
 * Dummy data – mimics DB tables
 * ==============================
 */

// --- suspects table (dummy)
const suspects = [
  { suspect_id: 1, name: "Suspect A" },
  { suspect_id: 2, name: "Suspect B" },
];

// --- clues table (dummy)
const clues = [
  { clue_id: 100, label: "Clue X" },
];

// --- nodes table (polymorphic reference)
const nodesTable = [
  {
    node_id: 10,
    node_type: "SUSPECT",
    node_reference: 1, // suspect_id
  },
  {
    node_id: 11,
    node_type: "SUSPECT",
    node_reference: 2,
  },
  {
    node_id: 12,
    node_type: "CLUE",
    node_reference: 100, // clue_id
  },
];

// --- links table
const linksTable = [
  {
    link_id: 1000,
    node_id_from: 10,
    node_id_to: 11,
    link_desc: "threatened",
    is_bidirectional: false,
  },
  {
    link_id: 1001,
    node_id_from: 11,
    node_id_to: 10,
    link_desc: "blackmailed",
    is_bidirectional: false,
  },
  {
    link_id: 1002,
    node_id_from: 10,
    node_id_to: 11,
    link_desc: "siblings",
    is_bidirectional: true,
  },
  {
    link_id: 1003,
    node_id_from: 10,
    node_id_to: 12,
    link_desc: "threw",
    is_bidirectional: false,
  },
];

/**
 * ==============================
 * Helper lookups (DB-like joins)
 * ==============================
 */

const suspectById = Object.fromEntries(
  suspects.map((s) => [s.suspect_id, s])
);

const clueById = Object.fromEntries(clues.map((c) => [c.clue_id, c]));

function resolveNodeLabel(node) {
  if (node.node_type === "SUSPECT") {
    return suspectById[node.node_reference]?.name ?? "Unknown Suspect";
  }
  if (node.node_type === "CLUE") {
    return clueById[node.node_reference]?.label ?? "Unknown Clue";
  }
  return "Unknown";
}

/**
 * ==============================
 * React Flow Component
 * ==============================
 */

export default function Graph() {
  /**
   * Convert DB-like nodes → ReactFlow nodes
   */
  const rfNodes = useMemo(() => {
    return nodesTable.map((n, index) => ({
      id: String(n.node_id),
      data: {
        label: resolveNodeLabel(n),
        nodeType: n.node_type,
      },
      position: {
        x: 150 + index * 220,
        y: n.node_type === "CLUE" ? 300 : 100,
      },
      style: {
        padding: 10,
        borderRadius: 8,
        border: "1px solid #999",
        background:
          n.node_type === "SUSPECT" ? "#2f2f2f" : "#444",
        color: "#fff",
        minWidth: 120,
        textAlign: "center",
      },
    }));
  }, []);

  /**
   * Convert DB-like links → ReactFlow edges
   */
  const rfEdges = useMemo(() => {
    const edges = [];

    linksTable.forEach((l) => {
      const baseEdge = {
        id: `link-${l.link_id}`,
        source: String(l.node_id_from),
        target: String(l.node_id_to),
        label: l.link_desc || "",
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
        style: {
          strokeWidth: 2,
        },
      };

      if (l.is_bidirectional) {
        // Represent bidirectional link visually as two arrows
        edges.push({
          ...baseEdge,
          id: `link-${l.link_id}-a`,
          markerStart: {
            type: MarkerType.ArrowClosed,
          },
        });
      } else {
        edges.push(baseEdge);
      }
    });

    return edges;
  }, []);

  const onNodeClick = useCallback((_, node) => {
    console.log("Node clicked:", node);
  }, []);

  const onEdgeClick = useCallback((_, edge) => {
    console.log("Edge clicked:", edge);
  }, []);

  return (
    <div style={{ width: "100%", height: "600px", background: "#1e1e1e" }}>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        fitView
      >
        <Background gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
}

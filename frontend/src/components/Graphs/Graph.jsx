import {
  useMemo,
  useCallback,
  useEffect,
  useState,
} from "react";
import ReactFlow, {
  Background,
  Controls,
  Panel,
  addEdge,
  MarkerType,
  applyNodeChanges,
  applyEdgeChanges,
} from "reactflow";
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

const suspectById = Object.fromEntries(
  suspects.map((s) => [s.suspect_id, s])
);
const clueById = Object.fromEntries(
  clues.map((c) => [c.clue_id, c])
);

/**
 * ==============================
 * Helpers
 * ==============================
 */

function resolveNodeLabel(node) {
  if (node.node_type === "SUSPECT") {
    return suspectById[node.node_reference]?.name ?? "Unknown Suspect";
  }
  if (node.node_type === "CLUE") {
    return clueById[node.node_reference]?.label ?? "Unknown Clue";
  }
  return "Unknown";
}

function createStyledEdge(base) {
  return {
    ...base,
    type: "smoothstep",
    pathOptions: { offset: 30 },
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2 },
    data: { directionState: 0 },
    labelStyle: {
      fill: "#fff",
      fontSize: 12,
      transform: "translateY(-10px)",
    },
    labelBgStyle: {
      fill: "#1e1e1e",
      fillOpacity: 0.85,
    },
    labelBgPadding: [6, 4],
  };
}

/**
 * ==============================
 * Component
 * ==============================
 */

export default function Graph() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);
  const [isEditingEdgeLabel, setIsEditingEdgeLabel] = useState(false);

  const [selectedSuspectId, setSelectedSuspectId] = useState("");
  const [selectedClueId, setSelectedClueId] = useState("");

  const [existsGraph, setExistsGraph] = useState(false);

  /**
   * ==============================
   * Keyboard handling
   * ==============================
   */

  const cycleEdgeDirection = (edge) => {
    const next = ((edge.data?.directionState ?? 0) + 1) % 3;

    if (next === 0) {
      return {
        ...edge,
        markerStart: undefined,
        markerEnd: { type: MarkerType.ArrowClosed },
        data: { directionState: 0 },
      };
    }

    if (next === 1) {
      return {
        ...edge,
        markerStart: { type: MarkerType.ArrowClosed },
        markerEnd: { type: MarkerType.ArrowClosed },
        data: { directionState: 1 },
      };
    }

    return {
      ...edge,
      source: edge.target,
      target: edge.source,
      markerStart: undefined,
      markerEnd: { type: MarkerType.ArrowClosed },
      data: { directionState: 2 },
    };
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (isEditingEdgeLabel) return;

      if (e.key === "Delete") {
        if (selectedEdgeId) {
          setEdges((eds) => eds.filter((e) => e.id !== selectedEdgeId));
          setSelectedEdgeId(null);
        }

        if (selectedNodeId) {
          setEdges((eds) =>
            eds.filter(
              (e) =>
                e.source !== selectedNodeId &&
                e.target !== selectedNodeId
            )
          );
          setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
          setSelectedNodeId(null);
        }
      }

      if (e.shiftKey && e.key.toLowerCase() === "r" && selectedEdgeId) {
        e.preventDefault();
        e.stopPropagation();
        setEdges((eds) =>
          eds.map((edge) =>
            edge.id === selectedEdgeId
              ? cycleEdgeDirection(edge)
              : edge
          )
        );
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedEdgeId, selectedNodeId, isEditingEdgeLabel]);

  /**
   * ==============================
   * Node creation
   * ==============================
   */

  const addNode = (type, referenceId, label) => {
    const id = `node-${Date.now()}`;
    const isSuspect = type === "SUSPECT";

    setNodes((nds) => [
      ...nds,
      {
        id,
        position: { x: 200, y: 200 },
        draggable: true,
        data: {
          node_type: type,
          node_reference: referenceId,
          label: (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 6,
              }}
            >
              <i
                className={`pi ${
                  isSuspect ? "pi-user" : "pi-search"
                }`}
                style={{
                  fontSize: 18,
                  color: isSuspect ? "#e74c3c" : "#f1c40f",
                }}
              />
              <div>{label}</div>
            </div>
          ),
        },
        style: {
          padding: "10px 12px 12px",
          borderRadius: 10,
          border: `2px solid ${isSuspect ? "#e74c3c" : "#f1c40f"}`,
          background: isSuspect ? "#2b1d1d" : "#2a2617",
          color: "#fff",
          minWidth: 140,
          textAlign: "center",
          boxShadow: "0 4px 12px rgba(0,0,0,0.35)",
        },
      },
    ]);
  };

  /**
   * ==============================
   * ReactFlow handlers
   * ==============================
   */

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback((params) => {
    const id = `link-${Date.now()}`;
    setEdges((eds) =>
      addEdge(
        createStyledEdge({
          ...params,
          id,
          label: "",
        }),
        eds
      )
    );
    setSelectedEdgeId(id);
    setIsEditingEdgeLabel(true);
  }, []);

  /**
   * ==============================
   * Render
   * ==============================
   */

  return (
    <div style={{ width: "1000px", height: "500px" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={(_, n) => setSelectedNodeId(n.id)}
        onEdgeClick={(_, e) => setSelectedEdgeId(e.id)}
        onPaneClick={() => {
          setSelectedNodeId(null);
          setSelectedEdgeId(null);
        }}
        fitView
      >
        <Background gap={16} color="#555" />
        <Controls />

        {/* Floating panel */}
        <Panel position="top-left">
          <div
            style={{
              background: "#1f1f1f",
              padding: 12,
              borderRadius: 8,
              width: 160,
              color: "#fff",
              boxShadow: "0 8px 20px rgba(0,0,0,0.45)",
            }}
          >
            {/* <div style={{ fontWeight: 600, marginBottom: 8 }}>
              Add node
            </div> */}

            <select
              value={selectedSuspectId}
              onChange={(e) => setSelectedSuspectId(e.target.value)}
              style={{ width: "100%", marginBottom: 6, backgroundColor: "#e74c3c", border: 0, borderRadius: 6 }}
            >
              <option value="">Select suspect</option>
              {suspects.map((s) => (
                <option key={s.suspect_id} value={s.suspect_id}>
                  {s.name}
                </option>
              ))}
            </select>

            <button
              style={{ width: "100%", marginBottom: 6, fontSize: 12, backgroundColor: "#e74c3c" }}
              onClick={() =>
                selectedSuspectId &&
                addNode(
                  "SUSPECT",
                  selectedSuspectId,
                  suspectById[selectedSuspectId].name
                )
              }
            >
              Add suspect
            </button>

            <select
              value={selectedClueId}
              onChange={(e) => setSelectedClueId(e.target.value)}
              style={{ width: "100%", marginBottom: 8, backgroundColor: "#f1c40f", border: 0, borderRadius: 6 }}
            >
              <option value="">Select clue</option>
              {clues.map((c) => (
                <option key={c.clue_id} value={c.clue_id}>
                  {c.label}
                </option>
              ))}
            </select>

            <button
              style={{ width: "100%", fontSize: 13, backgroundColor: "#f1c40f"  }}
              onClick={() =>
                selectedClueId &&
                addNode(
                  "CLUE",
                  selectedClueId,
                  clueById[selectedClueId].label
                )
              }
            >
              Add clue
            </button>

          </div>
        </Panel>
      </ReactFlow>

      {/* Inline edge editor */}
      {selectedEdgeId && (
        <div
          style={{
            position: "absolute",
            bottom: 20,
            left: 20,
            background: "#2b2b2b",
            padding: 12,
            borderRadius: 8,
            color: "#fff",
            width: 260,
          }}
        >
          <input
            value={edges.find((e) => e.id === selectedEdgeId)?.label || ""}
            onChange={(e) =>
              setEdges((eds) =>
                eds.map((edge) =>
                  edge.id === selectedEdgeId
                    ? { ...edge, label: e.target.value }
                    : edge
                )
              )
            }
            onFocus={() => setIsEditingEdgeLabel(true)}
            onBlur={() => setIsEditingEdgeLabel(false)}
            autoFocus
            placeholder="Relationship description"
            style={{ width: "100%" }}
          />
        </div>
      )}
    </div>
  );
}

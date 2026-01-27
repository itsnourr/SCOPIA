import {
  useMemo,
  useCallback,
  useEffect,
  useState,
} from "react";
import ReactFlow, {
  Background,
  Controls,
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

const suspectById = Object.fromEntries(
  suspects.map((s) => [s.suspect_id, s])
);
const clueById = Object.fromEntries(
  clues.map((c) => [c.clue_id, c])
);

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

function createStyledEdge(base) {
  return {
    ...base,
    type: "smoothstep",
    pathOptions: { offset: 30 },
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { strokeWidth: 2 },
    data: { directionIndex: 0 },
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

export default function Graph() {

  const [selectedEdgeId, setSelectedEdgeId] = useState(null);
  const [isEditingEdgeLabel, setIsEditingEdgeLabel] = useState(false);

  const cycleEdgeDirection = (edge) => {
    const nextState = ((edge.data?.directionState ?? 0) + 1) % 3;

    if (nextState === 0) {
      return {
        ...edge,
        source: edge.source,
        target: edge.target,
        markerStart: undefined,
        markerEnd: { type: MarkerType.ArrowClosed },
        data: { directionState: 0 },
      };
    }

    if (nextState === 1) {
      return {
        ...edge,
        markerStart: { type: MarkerType.ArrowClosed },
        markerEnd: { type: MarkerType.ArrowClosed },
        data: { directionState: 1 },
      };
    }

    // nextState === 2 (reverse)
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
    console.group("📦 RAW DB TABLES");
    console.log("suspects:", suspects);
    console.log("clues:", clues);
    console.log("nodesTable:", nodesTable);
    console.log("linksTable:", linksTable);
    console.groupEnd();
    
    const handleKeyDown = (e) => {
      if(isEditingEdgeLabel) return;
      if (!selectedEdgeId) return;

      if (e.key === "Delete") {
        console.log("🗑️ Deleting edge:", selectedEdgeId);

        setEdges((eds) =>
          eds.filter((edge) => edge.id !== selectedEdgeId)
        );

        setSelectedEdgeId(null);
      }

      if (e.shiftKey && e.key.toLowerCase() === "r") {
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
  }, [selectedEdgeId]);

  const initialNodes = useMemo(() => {
    console.group("🧱 BUILDING RF NODES");

    const nodes = nodesTable.map((n, index) => {
      const isSuspect = n.node_type === "SUSPECT";

      const node = {
        id: String(n.node_id),
        draggable: true,

        data: {
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
              <div>{resolveNodeLabel(n)}</div>
            </div>
          ),
          nodeType: n.node_type,
        },

        position: {
          x: 100 + index * 220,
          y: n.node_type === "CLUE" ? 300 : 100,
        },
        style: {
          padding: "10px 12px 12px",
          borderRadius: 10,
          border: `2px solid ${isSuspect ? "#e74c3c" : "#f1c40f"}`,
          background: isSuspect ? "#2b1d1d" : "#2a2617",
          color: "#fff",
          minWidth: 140,
          textAlign: "center",
          cursor: "grab",
          boxShadow: "0 4px 12px rgba(0,0,0,0.35)",
        },
      };

      console.log("🟦 RF Node:", node);
      return node;
    });

    console.log("✅ Final RF Nodes:", nodes);
    console.groupEnd();
    return nodes;
  }, []);

  const initialEdges = useMemo(() => {
    console.group("🔗 BUILDING RF EDGES");

    const edges = [];

    linksTable.forEach((l) => {
      
      const baseEdge = {
        id: `link-${l.link_id}`,
        source: String(l.node_id_from),
        target: String(l.node_id_to),

        type: "smoothstep",      
        pathOptions: { offset: 30 }, 

        label: l.link_desc,
        style: { strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed },

        labelStyle: {
          fill: "#fff",
          fontSize: 12,
        },
        labelBgStyle: {
          fill: "#1e1e1e",
          fillOpacity: 0.85,
        },
        labelBgPadding: [6, 4],
      };


      if (l.is_bidirectional) {
        const edge = {
          ...baseEdge,
          id: `link-${l.link_id}-bi`,
          markerStart: { type: MarkerType.ArrowClosed },
        };
        console.log("↔ Bidirectional Edge:", edge);
        edges.push(
          createStyledEdge({
            id: `link-${l.link_id}`,
            source: String(l.node_id_from),
            target: String(l.node_id_to),
            label: l.link_desc,
          })
        );
      } else {
        const edge = {
          ...baseEdge,
          id: `link-${l.link_id}`,
        };
        console.log("→ Edge:", edge);
        edges.push(
          createStyledEdge({
            id: `link-${l.link_id}`,
            source: String(l.node_id_from),
            target: String(l.node_id_to),
            label: l.link_desc,
          })
        );
      }
    });

    console.log("✅ Final RF Edges:", edges);
    console.groupEnd();
    return edges;
  }, []);

  /** -------- CONTROLLED STATE -------- */
  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState(initialEdges);

  /** -------- CHANGE HANDLERS -------- */
  const onNodesChange = useCallback((changes) => {
    console.log("🟨 Node changes:", changes);
    setNodes((nds) => applyNodeChanges(changes, nds));
  }, []);

  const onEdgesChange = useCallback((changes) => {
    setEdges((eds) => applyEdgeChanges(changes, eds));
  }, []);

  const onConnect = useCallback((params) => {
    const newEdgeId = `link-${Date.now()}`;

    const newEdge = createStyledEdge({
      ...params,
      id: newEdgeId,
      label: "", // start empty, user will type in inline editor
    });

    setEdges((eds) => addEdge(newEdge, eds));
    setSelectedEdgeId(newEdgeId);
    setIsEditingEdgeLabel(true); // auto-focus inline editor
  }, []);

  /** -------- CLICK HANDLERS -------- */
  const onNodeClick = useCallback((_, node) => {
    console.log("🖱️ NODE CLICKED:", node);
  }, []);

  const onEdgeClick = useCallback((_, edge) => {
    console.log("🖱️ EDGE SELECTED:", edge.id);
    setSelectedEdgeId(edge.id);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedEdgeId(null);
  }, []);

  /** -------- RENDER -------- */
  console.log("🎨 Rendering ReactFlow");

  return (
    <div style={{ width: "1000px", height: "1000px" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        fitView
        panOnScroll
        zoomOnPinch
      >
        <Background gap={16} color="#555" />
        <Controls />
      </ReactFlow>

      {/* Inline Text Editor */}
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
          <div style={{ fontSize: 12, opacity: 0.7 }}>Edit link</div>

          <input
            type="text"
            value={edges.find(e => e.id === selectedEdgeId)?.label || ""}
            onChange={(e) => {
              const value = e.target.value;
              setEdges((eds) =>
                eds.map((edge) =>
                  edge.id === selectedEdgeId
                    ? { ...edge, label: value }
                    : edge
                )
              );
            }}
            onFocus={() => setIsEditingEdgeLabel(true)}
            onBlur={() => setIsEditingEdgeLabel(false)}
            style={{
              width: "100%",
              marginTop: 6,
              padding: 6,
              borderRadius: 4,
              border: "none",
              outline: "none",
            }}
            placeholder="Relationship description"
            autoFocus
          />
        </div>
      )}

    </div>
  );
}

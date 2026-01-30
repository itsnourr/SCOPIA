import { Handle, Position } from "reactflow";

export default function FourPortNode({ data }) {
  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {/* Handles */}
      <Handle type="target" position={Position.Top} id="top" />
      <Handle type="source" position={Position.Bottom} id="bottom" />
      <Handle type="source" position={Position.Right} id="right" />
      <Handle type="target" position={Position.Left} id="left" />

      {/* Existing label (UNCHANGED) */}
      {data.label}
    </div>
  );
}

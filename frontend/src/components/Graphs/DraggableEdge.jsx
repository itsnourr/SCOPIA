import { getBezierPath, useReactFlow } from "reactflow";

export default function DraggableEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  data,
  markerEnd,
}) {
  const { setEdges } = useReactFlow();

  const cx =
    data?.controlX ?? (sourceX + targetX) / 2;
  const cy =
    data?.controlY ?? (sourceY + targetY) / 2;

  const [path] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourceControlX: cx,
    sourceControlY: cy,
    targetControlX: cx,
    targetControlY: cy,
  });

  const onDrag = (e) => {
    e.stopPropagation();
    setEdges((eds) =>
      eds.map((edge) =>
        edge.id === id
          ? {
              ...edge,
              data: {
                ...edge.data,
                controlX: e.clientX,
                controlY: e.clientY,
              },
            }
          : edge
      )
    );
  };

  return (
    <>
      <path d={path} fill="none" stroke="#aaa" strokeWidth={2} markerEnd={markerEnd} />

      {/* control handle */}
      <circle
        cx={cx}
        cy={cy}
        r={6}
        fill="#ff7675"
        style={{ cursor: "move" }}
        onMouseDown={(e) => {
          e.preventDefault();
          window.addEventListener("mousemove", onDrag);
          window.addEventListener(
            "mouseup",
            () => {
              window.removeEventListener("mousemove", onDrag);
            },
            { once: true }
          );
        }}
      />
    </>
  );
}

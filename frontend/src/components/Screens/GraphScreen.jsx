import React, { useState, useEffect } from "react";
import ReactFlow, { ReactFlowProvider } from "reactflow";
import Graph from "../Graphs/Graph";

export default function GraphScreen() {

  return (
    <div style={{ width: "100%", height: "100%"}}>
    <ReactFlowProvider>
        <Graph />
      </ReactFlowProvider>
    </div>
  );
}
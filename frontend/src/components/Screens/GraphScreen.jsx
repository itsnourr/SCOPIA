import React, { useState, useEffect } from "react";
import ReactFlow, { ReactFlowProvider } from "reactflow";
import Graph from "../Graphs/Graph";

export default function GraphScreen() {

  return (
    <div>
            <h1 className="screen-title" style={{ paddingBottom: "0px", marginBottom: "0px" }}>Graph</h1>
      
    <ReactFlowProvider>
        <Graph />
      </ReactFlowProvider>
    </div>
  );
}
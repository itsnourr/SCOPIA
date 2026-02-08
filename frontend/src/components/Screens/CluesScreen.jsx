import React, { useState, useEffect } from "react";

import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import CluesTable from "../Tables/CluesTable";

export default function CluesScreen() {

  return (
    <div>
      <h1 className="screen-title">Clues</h1>
      <CluesTable />
    </div>
  );
}
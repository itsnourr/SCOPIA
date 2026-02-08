import { Outlet } from "react-router-dom";
import CaseSideBar from "../Bars/CaseSideBar.jsx";

export default function CaseLayout() {
  return (
    <>
      <CaseSideBar />
      <div
        style={{
          marginLeft: "220px",  
          padding: "1rem",
          minHeight: "100vh",
        }}
      >
        <Outlet />
      </div>
    </>
  );
}

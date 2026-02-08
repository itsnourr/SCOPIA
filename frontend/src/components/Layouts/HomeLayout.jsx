import { Outlet } from "react-router-dom";
import HomeSideBar from "../Bars/HomeSideBar.jsx";

export default function HomeLayout() {
  return (
    <>
      <HomeSideBar />
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

import { Menu } from "primereact/menu";
import { Button } from "primereact/button";
import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import classNames from "classnames";
import "./sidebar.css"; 


export default function CaseSidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (path) => location.pathname.endsWith(path);

  const itemTemplate = (item) => {
    const active = isActive(item.path);

    return (
      <div
        className={classNames(
          "p-menuitem-link",
          { "active-item": active }
        )}
        onClick={item.command}
        title={collapsed ? item.label : undefined}
        style={{
          justifyContent: collapsed ? "center" : "flex-start",
        }}
      >
        <span className={classNames("p-menuitem-icon", item.icon)} />
        {!collapsed && (
          <span className="p-menuitem-text">{item.label}</span>
        )}
      </div>
    );
  };

  const items = [
    {
      label: "Info",
      icon: "pi pi-info-circle",
      path: "info",
      command: () => navigate("info"),
      template: itemTemplate,
    },
    {
      label: "Clues",
      icon: "pi pi-search",
      path: "clues",
      command: () => navigate("clues"),
      template: itemTemplate,
    },
    {
      label: "Gallery",
      icon: "pi pi-images",
      path: "gallery",
      command: () => navigate("gallery"),
      template: itemTemplate,
    },
    {
      label: "3D Studio",
      icon: "pi pi-box",
      path: "studio",
      command: () => navigate("studio"),
      template: itemTemplate,
    },
    {
      label: "Graph",
      icon: "pi pi-sitemap",
      path: "graph",
      command: () => navigate("graph"),
      template: itemTemplate,
    },
    { separator: true },
    {
      label: "Back",
      icon: "pi pi-arrow-left",
      command: () => navigate("/home/cases"),
      template: itemTemplate,
    },
  ];

  return (
    <div
      className={classNames(
        "sidebar",
        collapsed ? "collapsed" : "expanded"
      )}
    >
      {/* Collapse button */}
      <Button
        icon={collapsed ? "pi pi-angle-right" : "pi pi-angle-left"}
        className="p-button-text"
        onClick={() => setCollapsed(!collapsed)}
        style={{ alignSelf: collapsed ? "center" : "flex-end" }}
      />

      <Menu model={items} style={{ width: "100%" }} />
    </div>
  );
}

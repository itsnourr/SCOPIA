import { Menu } from "primereact/menu";
import { Button } from "primereact/button";
import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import classNames from "classnames";
import { logout } from "../../services/UserService";
import "./sidebar.css";

export default function HomeSidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  const itemTemplate = (item) => {
    const active = isActive(item.path);

    return (
      <div
        className={classNames("p-menuitem-link", { "active-item": active })}
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
      label: "Cases",
      icon: "pi pi-briefcase",
      path: "cases",
      command: () => navigate("cases"),
      template: itemTemplate,
    },
    {
      label: "Archive",
      icon: "pi pi-folder",
      path: "archive",
      command: () => navigate("archive"),
      template: itemTemplate,
    },
    {
      label: "Catalog",
      icon: "pi pi-database",
      path: "catalog",
      command: () => navigate("catalog"),
      template: itemTemplate,
    },
    {
      label: "AI Assistant",
      icon: "pi pi-comments",
      path: "ai",
      command: () => navigate("ai"),
      template: itemTemplate,
    },
    { separator: true },
    {
      label: "Settings",
      icon: "pi pi-cog",
      path: "settings",
      command: () => navigate("settings"),
      template: itemTemplate,
    },
    {
      label: "Profile",
      icon: "pi pi-user",
      path: "profile",
      command: () => navigate("profile"),
      template: itemTemplate,
    },
    {
      label: "Logout",
      icon: "pi pi-sign-out",
      command: logout(),
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
      {/* Collapse toggle */}
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

import React, { useEffect, useState } from "react";
import {
  getCurrentUsername,
  validatePassword,
  changePassword,
  logout
} from "../../services/userService";

export default function SettingsPage() {
  const [username, setUsername] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const user = getCurrentUsername();
    setUsername(user);
  }, []);

  const handleChangePassword = () => {
    setMessage("");

    const isValid = validatePassword(currentPassword);

    if (!isValid) {
      setIsError(true);
      setMessage("Current password is incorrect.");
      return;
    }

    if (newPassword.trim().length < 4) {
      setIsError(true);
      setMessage("New password must be at least 4 characters.");
      return;
    }

    changePassword(newPassword)
      .then(() => {
        setIsError(false);
        setMessage("Password changed successfully.");
        setCurrentPassword("");
        setNewPassword("");
      }
    );
  };

  const labelStyle = {
    color: "#9ca3af",
    fontSize: "14px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "6px",
  };

  const inputStyle = {
    width: "100%",
    padding: "12px 14px",
    borderRadius: "10px",
    border: "1px solid rgba(255,255,255,0.1)",
    background: "rgba(255,255,255,0.05)",
    color: "#f3f4f6",
    fontSize: "14px",
    outline: "none",
  };

  return (
    <div style={{ padding: "40px", color: "#f3f4f6" }}>
      
      <div
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "16px",
          padding: "30px",
          boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
          backdropFilter: "blur(6px)",
          width: "300px",
          maxWidth: "600px",
        }}
      >
        {/* Username */}
        {/* <div style={{ marginBottom: "30px" }}>
          <div style={labelStyle}>Username</div>
          <div
            style={{
              fontSize: "16px",
              fontWeight: "500",
              color: "#f3f4f6",
            }}
          >
            {username}
          </div>
        </div> */}

        {/* Current Password */}
        <div style={{ marginBottom: "20px" }}>
          <div style={labelStyle}>Current Password</div>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            style={inputStyle}
          />
        </div>

        {/* New Password */}
        <div style={{ marginBottom: "25px" }}>
          <div style={labelStyle}>New Password</div>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            style={inputStyle}
          />
        </div>

        {/* Button */}
        <button
          onClick={handleChangePassword}
          style={{
            padding: "12px 20px",
            borderRadius: "12px",
            background: "rgba(59,130,246,0.15)",
            border: "1px solid rgba(59,130,246,0.35)",
            color: "#3b82f6",
            fontWeight: "600",
            fontSize: "14px",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
        >
          Change Password
        </button>
        <br />
        {/* <button
          onClick={logout}
          style={{
            padding: "12px 20px",
            borderRadius: "12px",
            background: "rgba(239,68,68,0.12)",
            border: "1px solid rgba(239,68,68,0.4)",
            color: "#ef4444",
            fontWeight: "600",
            fontSize: "14px",
            cursor: "pointer",
            transition: "all 0.2s ease",
            marginTop: "15px",
          }}
        >
          Logout
        </button> */}

        {/* Message */}
        {message && (
          <div
            style={{
              marginTop: "20px",
              padding: "10px 14px",
              borderRadius: "10px",
              fontSize: "14px",
              background: isError
                ? "rgba(239,68,68,0.1)"
                : "rgba(34,197,94,0.1)",
              border: isError
                ? "1px solid rgba(239,68,68,0.3)"
                : "1px solid rgba(34,197,94,0.3)",
              color: isError ? "#ef4444" : "#22c55e",
            }}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
}
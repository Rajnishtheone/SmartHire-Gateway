import React from "react";
import { logout, getCurrentUser } from "../services/auth";

const NavBar = ({ onLogout }) => {
  const user = getCurrentUser();
  const roleLabel = user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : "";

  const handleLogout = () => {
    logout();
    onLogout?.();
  };

  return (
    <header
      style={{
        background: "#111827",
        color: "white",
        padding: "1rem 2rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <h1 style={{ margin: 0, fontSize: "1.25rem" }}>SmartHire Gateway</h1>
      {user && (
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontWeight: 600 }}>{user.name || user.email}</div>
            <div style={{ fontSize: "0.8rem", opacity: 0.8 }}>{roleLabel}</div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              background: "#f59e0b",
              color: "#111827",
              border: "none",
              padding: "0.5rem 1rem",
              borderRadius: "0.5rem",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
};

export default NavBar;

import React from "react";

const StatCard = ({ label, value, trend }) => (
  <div className="card">
    <h3 style={{ fontSize: "0.9rem", textTransform: "uppercase", color: "#6b7280" }}>{label}</h3>
    <p style={{ fontSize: "2rem", margin: "0.5rem 0" }}>{value}</p>
    {trend && <span style={{ color: trend.startsWith("+") ? "#10b981" : "#ef4444" }}>{trend}</span>}
  </div>
);

export default StatCard;

import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { getCurrentUser, logout } from "../services/auth";
import { createRecruiter, deleteRecruiter, listRecruiters } from "../services/admin";
import StatCard from "../components/StatCard";

const Dashboard = () => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [recruiters, setRecruiters] = useState([]);
  const [recruiterForm, setRecruiterForm] = useState({ email: "", password: "", name: "" });
  const [recruiterError, setRecruiterError] = useState(null);
  const [recruiterListLoading, setRecruiterListLoading] = useState(false);
  const [recruiterSaving, setRecruiterSaving] = useState(false);
  const navigate = useNavigate();

  const user = useMemo(() => getCurrentUser(), []);
  const isAdmin = user?.role === "admin";

  useEffect(() => {
    refreshCandidates();
    if (isAdmin) {
      refreshRecruiters();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  const refreshCandidates = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get("/candidates");
      setRecords(response.data.items);
    } catch (err) {
      if (err.response && err.response.status === 401) {
        logout();
        navigate("/login");
      } else if (err.response && err.response.status === 403) {
        setError("You do not have access to view candidates.");
      } else {
        setError("Failed to load candidates.");
      }
    } finally {
      setLoading(false);
    }
  };

  const refreshRecruiters = async () => {
    if (!isAdmin) {
      return;
    }
    setRecruiterListLoading(true);
    setRecruiterError(null);
    try {
      const response = await listRecruiters();
      setRecruiters(response.items);
    } catch (err) {
      setRecruiterError("Failed to load recruiter accounts.");
    } finally {
      setRecruiterListLoading(false);
    }
  };

  const handleManualTrigger = async () => {
    setTriggering(true);
    try {
      await api.post("/whatsapp/manual-ingest", {
        body: "Manual ingest trigger via dashboard.",
        attachments: [],
      });
      await refreshCandidates();
    } catch (err) {
      setError("Manual ingest failed.");
    } finally {
      setTriggering(false);
    }
  };

  const handleCreateRecruiter = async (event) => {
    event.preventDefault();
    setRecruiterError(null);
    setRecruiterSaving(true);
    try {
      await createRecruiter(recruiterForm);
      setRecruiterForm({ email: "", password: "", name: "" });
      refreshRecruiters();
    } catch (err) {
      const message = err.response?.data?.detail || "Unable to create recruiter.";
      setRecruiterError(message);
    } finally {
      setRecruiterSaving(false);
    }
  };

  const handleRemoveRecruiter = async (recruiter) => {
    const { email, name } = recruiter;
    if (!window.confirm(`Remove recruiter ${name || email}?`)) {
      return;
    }
    try {
      await deleteRecruiter(email);
      refreshRecruiters();
    } catch (err) {
      const message = err.response?.data?.detail || "Unable to remove recruiter.";
      setRecruiterError(message);
    }
  };

  const averageConfidence = records.length
    ? `${Math.round(
        (records.reduce((sum, item) => sum + (item.confidence || 0), 0) / records.length) * 100,
      )}%`
    : "N/A";

  return (
    <div className="content">
      <div style={{ marginBottom: "2rem" }}>
        <h2 style={{ marginBottom: "0.5rem" }}>
          {isAdmin ? "Admin Console" : "Recruiter Console"} - {user?.name || user?.email}
        </h2>
        <p style={{ color: "#6b7280" }}>
          Monitor incoming resumes, configure recruiter access, and keep your team synchronized.
        </p>
        <button
          onClick={handleManualTrigger}
          disabled={triggering}
          style={{
            background: "#2563eb",
            color: "#ffffff",
            border: "none",
            padding: "0.65rem 1.2rem",
            borderRadius: "0.75rem",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {triggering ? "Triggering..." : "Trigger Demo Ingest"}
        </button>
        <button
          onClick={refreshCandidates}
          style={{
            marginLeft: "1rem",
            background: "transparent",
            color: "#2563eb",
            border: "1px solid #2563eb",
            padding: "0.65rem 1.2rem",
            borderRadius: "0.75rem",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-3" style={{ marginBottom: "2rem" }}>
        <StatCard label="Total Resumes (recent)" value={records.length} trend="+5 this week" />
        <StatCard label="Average Confidence" value={averageConfidence} trend="" />
        <StatCard label="Auto Replies Sent" value="Enabled" trend="+100% response rate" />
      </div>

      <div className="card" style={{ marginBottom: "2rem" }}>
        <h3 style={{ marginTop: 0 }}>Recent Candidates</h3>
        {loading && <p>Loading candidates...</p>}
        {error && <p style={{ color: "#ef4444" }}>{error}</p>}
        {!loading && !error && records.length === 0 && <p>No candidates ingested yet.</p>}
        {!loading && !error && records.length > 0 && (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #e5e7eb" }}>
                <th style={{ padding: "0.5rem" }}>Name</th>
                <th style={{ padding: "0.5rem" }}>Email</th>
                <th style={{ padding: "0.5rem" }}>Phone</th>
                <th style={{ padding: "0.5rem" }}>Skills</th>
                <th style={{ padding: "0.5rem" }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record, index) => (
                <tr key={index} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "0.5rem" }}>{record.full_name || "Unknown"}</td>
                  <td style={{ padding: "0.5rem" }}>{record.email || "-"}</td>
                  <td style={{ padding: "0.5rem" }}>{record.phone || "-"}</td>
                  <td style={{ padding: "0.5rem" }}>{record.skills?.length ? record.skills.join(", ") : "-"}</td>
                  <td style={{ padding: "0.5rem" }}>
                    {record.confidence ? `${Math.round(record.confidence * 100)}%` : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {isAdmin && (
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ marginTop: 0 }}>Recruiter Accounts</h3>
          </div>
          {recruiterError && <p style={{ color: "#ef4444" }}>{recruiterError}</p>}
          <form
            onSubmit={handleCreateRecruiter}
            style={{ marginBottom: "1.5rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}
          >
            <input
              type="text"
              placeholder="Recruiter name"
              value={recruiterForm.name}
              onChange={(event) => setRecruiterForm((prev) => ({ ...prev, name: event.target.value }))}
              required
              style={{
                flex: "1 1 200px",
                padding: "0.75rem",
                borderRadius: "0.75rem",
                border: "1px solid #d1d5db",
              }}
            />
            <input
              type="email"
              placeholder="Recruiter email"
              value={recruiterForm.email}
              onChange={(event) => setRecruiterForm((prev) => ({ ...prev, email: event.target.value }))}
              required
              style={{
                flex: "1 1 240px",
                padding: "0.75rem",
                borderRadius: "0.75rem",
                border: "1px solid #d1d5db",
              }}
            />
            <input
              type="password"
              placeholder="Temporary password"
              value={recruiterForm.password}
              onChange={(event) => setRecruiterForm((prev) => ({ ...prev, password: event.target.value }))}
              required
              minLength={6}
              style={{
                flex: "1 1 200px",
                padding: "0.75rem",
                borderRadius: "0.75rem",
                border: "1px solid #d1d5db",
              }}
            />
            <button
              type="submit"
              style={{
                padding: "0.75rem 1.5rem",
                borderRadius: "0.75rem",
                border: "none",
                background: "#10b981",
                color: "#ffffff",
                fontWeight: 600,
                cursor: "pointer",
              }}
              disabled={recruiterSaving}
            >
              {recruiterSaving ? "Saving..." : "Add Recruiter"}
            </button>
          </form>

          {recruiterListLoading ? (
            <p>Loading recruiters...</p>
          ) : recruiters.length === 0 ? (
            <p>No active recruiters yet.</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid #e5e7eb" }}>
                  <th style={{ padding: "0.5rem" }}>Name</th>
                  <th style={{ padding: "0.5rem" }}>Email</th>
                  <th style={{ padding: "0.5rem" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recruiters.map((recruiter) => (
                  <tr key={recruiter.email} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "0.5rem" }}>{recruiter.name || "-"}</td>
                    <td style={{ padding: "0.5rem" }}>{recruiter.email}</td>
                    <td style={{ padding: "0.5rem" }}>
                      <button
                        onClick={() => handleRemoveRecruiter(recruiter)}
                        style={{
                          background: "#ef4444",
                          color: "#ffffff",
                          border: "none",
                          padding: "0.5rem 1rem",
                          borderRadius: "0.6rem",
                          cursor: "pointer",
                        }}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;


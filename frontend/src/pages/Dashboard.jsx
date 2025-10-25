import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import { getCurrentUser, logout } from "../services/auth";
import { createRecruiter, deleteRecruiter, listRecruiters } from "../services/admin";
import StatCard from "../components/StatCard";
import {
  fetchCandidateBoard,
  updateCandidateStatus,
  deleteCandidate as removeCandidate,
  deleteCandidatesByStatus,
} from "../services/candidates";

const Dashboard = () => {
  const [board, setBoard] = useState({
    new: [],
    approved: [],
    interview: [],
    selected: [],
    rejected: [],
  });
  const [boardLoading, setBoardLoading] = useState(true);
  const [boardError, setBoardError] = useState(null);
  const [activeStatus, setActiveStatus] = useState("new");
  const [actionCandidateId, setActionCandidateId] = useState(null);
  const [bulkProcessing, setBulkProcessing] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [recruiters, setRecruiters] = useState([]);
  const [recruiterForm, setRecruiterForm] = useState({ email: "", password: "", name: "" });
  const [recruiterError, setRecruiterError] = useState(null);
  const [recruiterListLoading, setRecruiterListLoading] = useState(false);
  const [recruiterSaving, setRecruiterSaving] = useState(false);
  const navigate = useNavigate();

  const user = useMemo(() => getCurrentUser(), []);
  const isAdmin = user?.role === "admin";
  const statusOrder = useMemo(() => ["new", "approved", "interview", "selected", "rejected"], []);
  const STATUS_LABELS = {
    new: "New",
    approved: "Approved",
    interview: "Interview",
    selected: "Selected",
    rejected: "Rejected",
  };
  const statusStyles = {
    new: "#3b82f6",
    approved: "#10b981",
    interview: "#6366f1",
    selected: "#f59e0b",
    rejected: "#ef4444",
  };
  const statusTransitions = {
    new: [
      { label: "Approve", target: "approved" },
      { label: "Send to Interview", target: "interview" },
      { label: "Reject", target: "rejected" },
    ],
    approved: [
      { label: "Move to Interview", target: "interview" },
      { label: "Move to Selected", target: "selected" },
      { label: "Move to Rejected", target: "rejected" },
    ],
    interview: [
      { label: "Move to Selected", target: "selected" },
      { label: "Move to Approved", target: "approved" },
      { label: "Move to Rejected", target: "rejected" },
    ],
    selected: [
      { label: "Move to Approved", target: "approved" },
      { label: "Move to Interview", target: "interview" },
      { label: "Move to Rejected", target: "rejected" },
    ],
    rejected: [
      { label: "Move to Approved", target: "approved" },
      { label: "Move to Interview", target: "interview" },
    ],
  };

  useEffect(() => {
    refreshBoard();
    if (isAdmin) {
      refreshRecruiters();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  const refreshBoard = async () => {
    setBoardLoading(true);
    setBoardError(null);
    try {
      const data = await fetchCandidateBoard();
      setBoard({
        new: data.new || [],
        approved: data.approved || [],
        interview: data.interview || [],
        selected: data.selected || [],
        rejected: data.rejected || [],
      });
    } catch (err) {
      if (err.response && err.response.status === 401) {
        logout();
        navigate("/login");
      } else if (err.response && err.response.status === 403) {
        setBoardError("You do not have access to view candidates.");
      } else {
        setBoardError("Failed to load candidates.");
      }
    } finally {
      setBoardLoading(false);
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
      await refreshBoard();
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

  const allCandidates = useMemo(
    () => statusOrder.flatMap((status) => board[status] || []),
    [board, statusOrder],
  );
  const statusCounts = useMemo(() => {
    const counts = {};
    statusOrder.forEach((status) => {
      counts[status] = board[status]?.length || 0;
    });
    return counts;
  }, [board, statusOrder]);

  const formatDateTime = (value) => {
    try {
      return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(value));
    } catch (err) {
      return value;
    }
  };

  const handleStatusChange = async (candidateId, targetStatus) => {
    setActionCandidateId(candidateId);
    setBoardError(null);
    try {
      await updateCandidateStatus(candidateId, targetStatus);
      await refreshBoard();
    } catch (err) {
      if (err.response && err.response.status === 401) {
        logout();
        navigate("/login");
      } else {
        const message = err.response?.data?.detail || "Unable to update candidate status.";
        setBoardError(message);
      }
    } finally {
      setActionCandidateId(null);
    }
  };

  const handleDeleteCandidate = async (candidate) => {
    if (
      !window.confirm(
        `Delete ${candidate.full_name || "this candidate"}? This will remove them from the current pipeline view.`,
      )
    ) {
      return;
    }
    setActionCandidateId(candidate.candidate_id);
    setBoardError(null);
    try {
      await removeCandidate(candidate.candidate_id);
      await refreshBoard();
    } catch (err) {
      if (err.response && err.response.status === 401) {
        logout();
        navigate("/login");
      } else {
        const message = err.response?.data?.detail || "Unable to delete candidate.";
        setBoardError(message);
      }
    } finally {
      setActionCandidateId(null);
    }
  };

  const handleBulkDeleteRejected = async () => {
    if (!window.confirm("Delete all rejected candidates from this view? This action cannot be undone.")) {
      return;
    }
    setBulkProcessing(true);
    setBoardError(null);
    try {
      await deleteCandidatesByStatus("rejected");
      await refreshBoard();
    } catch (err) {
      if (err.response && err.response.status === 401) {
        logout();
        navigate("/login");
      } else {
        const message = err.response?.data?.detail || "Unable to delete rejected candidates.";
        setBoardError(message);
      }
    } finally {
      setBulkProcessing(false);
    }
  };

  const renderCandidateActions = (candidate, statusKey) => {
    const transitions = statusTransitions[statusKey] || [];
    return (
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
        {transitions.map((transition) => (
          <button
            key={`${candidate.candidate_id}-${transition.target}`}
            onClick={() => handleStatusChange(candidate.candidate_id, transition.target)}
            disabled={actionCandidateId === candidate.candidate_id}
            style={{
              padding: "0.5rem 0.9rem",
              borderRadius: "0.6rem",
              border: "none",
              background: statusStyles[transition.target] || "#4b5563",
              color: "#ffffff",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            {transition.label}
          </button>
        ))}
        <button
          onClick={() => handleDeleteCandidate(candidate)}
          disabled={actionCandidateId === candidate.candidate_id}
          style={{
            padding: "0.5rem 0.9rem",
            borderRadius: "0.6rem",
            border: "none",
            background: "#ef4444",
            color: "#ffffff",
            cursor: "pointer",
            fontSize: "0.85rem",
          }}
        >
          Delete
        </button>
      </div>
    );
  };

  const renderCandidateTable = (statusKey) => {
    const candidates = board[statusKey] || [];
    if (boardLoading) {
      return <p>Loading candidates...</p>;
    }
    if (!candidates.length) {
      return <p>No candidates in this stage yet.</p>;
    }
    return (
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid #e5e7eb" }}>
              <th style={{ padding: "0.75rem" }}>Name</th>
              <th style={{ padding: "0.75rem" }}>Email</th>
              <th style={{ padding: "0.75rem" }}>Phone</th>
              <th style={{ padding: "0.75rem" }}>Skills</th>
              <th style={{ padding: "0.75rem" }}>Confidence</th>
              <th style={{ padding: "0.75rem" }}>Source</th>
              <th style={{ padding: "0.75rem" }}>Received</th>
              <th style={{ padding: "0.75rem" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate) => (
              <tr key={candidate.candidate_id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                <td style={{ padding: "0.75rem" }}>
                  <div style={{ fontWeight: 600 }}>{candidate.full_name || "Unknown"}</div>
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>
                    Stage: {STATUS_LABELS[candidate.status] || candidate.status}
                  </div>
                </td>
                <td style={{ padding: "0.75rem" }}>{candidate.email || "-"}</td>
                <td style={{ padding: "0.75rem" }}>{candidate.phone || "-"}</td>
                <td style={{ padding: "0.75rem" }}>
                  {candidate.skills?.length ? candidate.skills.join(", ") : "-"}
                </td>
                <td style={{ padding: "0.75rem" }}>
                  {candidate.confidence != null ? `${Math.round(candidate.confidence * 100)}%` : "N/A"}
                </td>
                <td style={{ padding: "0.75rem" }}>{candidate.source}</td>
                <td style={{ padding: "0.75rem" }}>{formatDateTime(candidate.received_at)}</td>
                <td style={{ padding: "0.75rem" }}>{renderCandidateActions(candidate, statusKey)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };
  const averageConfidence = allCandidates.length
    ? `${Math.round(
        (allCandidates.reduce((sum, item) => sum + (item.confidence || 0), 0) / allCandidates.length) * 100,
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
          onClick={refreshBoard}
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
        <StatCard label="Total Candidates" value={allCandidates.length} trend="" />
        <StatCard label="Average Confidence" value={averageConfidence} trend="" />
        <StatCard label="New Leads" value={statusCounts.new || 0} trend="" />
      </div>

      <div className="card" style={{ marginBottom: "2rem" }}>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "1rem",
          }}
        >
          <h3 style={{ margin: 0 }}>Talent Pipeline</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {statusOrder.map((status) => (
              <button
                key={status}
                onClick={() => setActiveStatus(status)}
                style={{
                  padding: "0.5rem 1rem",
                  borderRadius: "999px",
                  border: "1px solid",
                  borderColor: activeStatus === status ? statusStyles[status] : "#d1d5db",
                  background: activeStatus === status ? statusStyles[status] : "transparent",
                  color: activeStatus === status ? "#ffffff" : "#374151",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                {STATUS_LABELS[status]} ({statusCounts[status] || 0})
              </button>
            ))}
          </div>
        </div>
        {boardError && <p style={{ color: "#ef4444", marginTop: "1rem" }}>{boardError}</p>}
        <div style={{ marginTop: "1.5rem" }}>{renderCandidateTable(activeStatus)}</div>
        {activeStatus === "rejected" && statusCounts.rejected > 0 && (
          <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
            <button
              onClick={handleBulkDeleteRejected}
              disabled={bulkProcessing}
              style={{
                padding: "0.65rem 1.2rem",
                borderRadius: "0.75rem",
                border: "none",
                background: "#ef4444",
                color: "#ffffff",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {bulkProcessing ? "Deleting..." : "Delete All Rejected"}
            </button>
          </div>
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


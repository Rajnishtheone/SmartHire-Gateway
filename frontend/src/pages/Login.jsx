import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/auth";

const Login = ({ onLogin }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("recruiter@example.com");
  const [password, setPassword] = useState("recruiter123");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      onLogin?.();
      navigate("/");
    } catch (err) {
      setError("Login failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #111827 0%, #1f2937 45%, #0f172a 100%)",
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="card"
        style={{ width: "360px", backdropFilter: "blur(10px)" }}
      >
        <h2 style={{ marginTop: 0 }}>Recruiter Login</h2>
        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          Email
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            required
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "0.75rem",
              border: "1px solid #d1d5db",
              marginTop: "0.25rem",
            }}
          />
        </label>
        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          Password
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            required
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "0.75rem",
              border: "1px solid #d1d5db",
              marginTop: "0.25rem",
            }}
          />
        </label>
        {error && <p style={{ color: "#ef4444" }}>{error}</p>}
        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "0.75rem",
            borderRadius: "0.75rem",
            border: "none",
            cursor: "pointer",
            background: "#f59e0b",
            color: "#111827",
            fontWeight: 600,
            marginTop: "1rem",
          }}
        >
          {loading ? "Signing in..." : "Login"}
        </button>
      </form>
    </div>
  );
};

export default Login;

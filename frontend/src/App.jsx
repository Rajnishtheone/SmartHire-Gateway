import React, { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import NavBar from "./components/NavBar";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import { getCurrentUser } from "./services/auth";

const App = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(getCurrentUser());

  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  return (
    <div className="app-shell">
      <NavBar
        onLogout={() => {
          setUser(null);
          navigate("/login");
        }}
      />
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/login"
          element={
            <Login
              onLogin={() => {
                setUser(getCurrentUser());
                navigate("/");
              }}
            />
          }
        />
      </Routes>
    </div>
  );
};

export default App;

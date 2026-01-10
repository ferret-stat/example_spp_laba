import React, { useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

export default function Navbar() {
  const { isAuthenticated, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav style={{ padding: "10px", borderBottom: "1px solid #ccc" }}>
      <Link to="/" style={{ marginRight: "10px" }}>
        Home
      </Link>
      {!isAuthenticated() && (
        <Link to="/login" style={{ marginRight: "10px" }}>
          Login
        </Link>
      )}
      {!isAuthenticated() && (
        <Link to="/register" style={{ marginRight: "10px" }}>
          Register
        </Link>
      )}
      {isAuthenticated() && (
        <Link to="/dashboard" style={{ marginRight: "10px" }}>
          Dashboard
        </Link>
      )}
      {isAuthenticated() && (
        <Link to="/files" style={{ marginRight: "10px" }}>
          Файлы
        </Link>
      )}
      {isAuthenticated() && <button onClick={handleLogout}>Выйти</button>}
    </nav>
  );
}

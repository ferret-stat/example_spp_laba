import React, { useContext, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { getAdminMe } from "../api/files";
import "./navbar.css";

export default function Navbar() {
  const { isAuthenticated, logout, token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [isSuperuser, setIsSuperuser] = useState(false);

  const handleLogout = () => {
    logout();
    setIsSuperuser(false);
    navigate("/login");
  };

  useEffect(() => {
    if (!isAuthenticated()) {
      setIsSuperuser(false);
      return;
    }

    const load = async () => {
      try {
        const res = await getAdminMe();
        setIsSuperuser(Boolean(res?.is_superuser));
      } catch (e) {
        console.error("Ошибка проверки суперпользователя", e);
        setIsSuperuser(false);
      }
    };

    load();
  }, [token, isAuthenticated]);

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <span className="brand-dot" />
          Добро пожаловать!
        </Link>

        <div className="navbar-links">
          <Link to="/" className="nav-link">
            Главная
          </Link>
          {isAuthenticated() && (
            <Link to="/files" className="nav-link">
              Файлы
            </Link>
          )}
          {isAuthenticated() && (
            <Link to="/myfiles" className="nav-link">
              Мои файлы
            </Link>
          )}
          {isAuthenticated() && isSuperuser && (
            <Link to="/dashboard" className="nav-link">
              Дашборд
            </Link>
          )}
        </div>

        <div className="nav-actions">
          {!isAuthenticated() && (
            <Link to="/login" className="nav-link">
              Вход
            </Link>
          )}
          {!isAuthenticated() && (
            <Link to="/register" className="nav-link">
              Регистрация
            </Link>
          )}
          {isAuthenticated() && (
            <button className="nav-button" onClick={handleLogout}>
              Выход
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

import React, { useState, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./login.css";
import { AuthContext } from "../context/AuthContext";

export default function Login() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!identifier || !password) return alert("Заполните все поля");

    try {
      const response = await fetch("/api/auth/login-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Ошибка авторизации");
        return;
      }

      login(data.access_token);

      navigate("/files");
    } catch (err) {
      console.error(err);
      alert("Ошибка сервера");
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2 className="title">Вход</h2>
        <p className="subtitle">Email или номер телефона</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>Email / Телефон</label>
          <input
            type="text"
            placeholder="Введите email или телефон..."
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />

          <label>Пароль</label>
          <input
            type="password"
            placeholder="Введите ваш пароль..."
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button type="submit" className="login-btn">
            Вход
          </button>
        </form>

        <p className="bottom-text">
          Нет аккаунта? <Link to="/register">Регистрация</Link>
        </p>
      </div>
    </div>
  );
}

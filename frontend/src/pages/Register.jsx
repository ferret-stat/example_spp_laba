import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./login.css";

export default function Register() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      alert("Пароли не совпадают!");
      return;
    }

    const email = identifier.includes("@") ? identifier : null;
    const phone = !email ? identifier : null;

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, phone, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Ошибка регистрации");
        return;
      }

      alert("Регистрация успешна! Войдите в аккаунт.");
      navigate("/login");
    } catch (err) {
      console.error(err);
      alert("Ошибка сервера");
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2 className="title">Регистрация</h2>
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
            placeholder="Введите пароль..."
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <label>Повторите пароль</label>
          <input
            type="password"
            placeholder="Подтвердите пароль..."
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <button type="submit" className="login-btn">
            Зарегистрироваться
          </button>
        </form>

        <p className="bottom-text">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  );
}

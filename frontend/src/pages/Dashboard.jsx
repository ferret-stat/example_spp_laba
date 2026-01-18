import { useEffect, useMemo, useState } from "react";
import { getAdminMe, getAdminUsers, getUserStats, setUserActive } from "../api/files";
import "./dashboard.css";

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [days, setDays] = useState([]);
  const [busyUser, setBusyUser] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const me = await getAdminMe();
        const superuser = Boolean(me?.is_superuser);
        setIsSuperuser(superuser);
        if (superuser) {
          const [data, userData] = await Promise.all([
            getUserStats(),
            getAdminUsers(7),
          ]);
          setStats(data);
          setUsers(userData?.users ?? []);
          setDays(userData?.days ?? []);
        }
      } catch (e) {
        console.error("Ошибка загрузки дашборда", e);
        setError("Не удалось загрузить данные.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const dayLabels = useMemo(() => days, [days]);

  const handleToggleActive = async (user) => {
    const nextActive = !user.is_active;
    const ok = window.confirm(
      nextActive
        ? `Разблокировать ${user.email || user.phone || user.id}?`
        : `Заблокировать ${user.email || user.phone || user.id}?`
    );
    if (!ok) return;
    try {
      setBusyUser(user.id);
      await setUserActive(user.id, nextActive);
      setUsers((prev) =>
        prev.map((u) =>
          u.id === user.id ? { ...u, is_active: nextActive } : u
        )
      );
    } catch (e) {
      console.error("Ошибка смены статуса", e);
      setError("Не удалось изменить статус пользователя.");
    } finally {
      setBusyUser(null);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-card">
        <div className="dashboard-header">
          <div>
            <h2 className="dashboard-title">Дашборд</h2>
            <p className="dashboard-subtitle">
              Статистика по пользователям и доступам
            </p>
          </div>
        </div>

        {loading ? (
          <div className="state">
            <div className="skeleton-line w-60" />
            <div className="skeleton-line w-80" />
          </div>
        ) : error ? (
          <div className="state state-error">
            <div className="state-title">Что-то пошло не так</div>
            <div className="state-text">{error}</div>
          </div>
        ) : !isSuperuser ? (
          <div className="state state-error">
            <div className="state-title">Доступ запрещён</div>
            <div className="state-text">
              Этот раздел доступен только суперпользователям.
            </div>
          </div>
        ) : (
          <>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Всего пользователей</div>
                <div className="stat-value">{stats?.total_users ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Активные</div>
                <div className="stat-value">{stats?.active_users ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Неактивные</div>
                <div className="stat-value">{stats?.inactive_users ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Суперпользователи</div>
                <div className="stat-value">{stats?.superusers ?? 0}</div>
              </div>
            </div>

            <div className="users-section">
              <h3 className="section-title">Пользователи</h3>
              <div className="users-table">
                <div className="users-row users-head">
                  <div>Пользователь</div>
                  <div>Последний вход</div>
                  <div>Комментарии</div>
                  <div>Скачивания</div>
                  <div>Динамика</div>
                  <div>Статус</div>
                </div>

                {users.map((u) => {
                  const lastLogin = u.last_login
                    ? new Date(u.last_login).toLocaleString("ru-RU")
                    : "Нет данных";
                  const commentsSeries = u.comments_series ?? [];
                  const downloadsSeries = u.downloads_series ?? [];
                  return (
                    <div key={u.id} className="users-row">
                      <div className="user-cell">
                        <div className="user-main">
                          <span className="user-name">
                            {u.email || u.phone || u.id}
                          </span>
                          {u.is_superuser && (
                            <span className="user-badge">Суперюзер</span>
                          )}
                        </div>
                        <div className="user-sub">ID: {u.id}</div>
                      </div>
                      <div>{lastLogin}</div>
                      <div>{u.comments_count ?? 0}</div>
                      <div>{u.downloads_count ?? 0}</div>
                      <div className="spark-wrap">
                        <div className="spark-row">
                          <span className="spark-label">Комм.</span>
                          <div className="sparkline">
                            {commentsSeries.map((value, idx) => (
                              <span
                                key={`c-${u.id}-${idx}`}
                                className="spark-bar"
                                style={{
                                  height: `${Math.min(100, value * 10 + 10)}%`,
                                }}
                                title={`${dayLabels[idx] || ""}: ${value}`}
                              />
                            ))}
                          </div>
                        </div>
                        <div className="spark-row">
                          <span className="spark-label">Скач.</span>
                          <div className="sparkline">
                            {downloadsSeries.map((value, idx) => (
                              <span
                                key={`d-${u.id}-${idx}`}
                                className="spark-bar is-download"
                                style={{
                                  height: `${Math.min(100, value * 10 + 10)}%`,
                                }}
                                title={`${dayLabels[idx] || ""}: ${value}`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                      <div>
                        <button
                          className={`btn ${u.is_active ? "btn-ghost" : "btn-primary"}`}
                          onClick={() => handleToggleActive(u)}
                          disabled={busyUser === u.id}
                        >
                          {u.is_active ? "Заблокировать" : "Разблокировать"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

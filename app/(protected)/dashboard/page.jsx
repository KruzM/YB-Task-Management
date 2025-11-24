"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/app/lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const u = await apiFetch("/users/me");
        if (!mounted) return;
        setUser(u);

        try {
          const t = await apiFetch("/tasks");
          if (mounted) setTasks(t || []);
        } catch {
          if (mounted) setTasks([]);
        }

        setLoading(false);
      } catch (err) {
        if (mounted) {
          setError(err?.body?.detail || err.message || "Failed to load user");
          setLoading(false);
        }
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="layout-page">
      

      <div className="layout-main">
        

        <main className="page-content">
          <div className="page-container">
            <div className="page-heading">
              <h1 className="page-title">Dashboard</h1>
              <div className="page-subtitle">
                Welcome back{user ? `, ${user.full_name || user.email}` : ""}.
              </div>
            </div>

            {loading ? (
              <Card className="card-loading">Loading user...</Card>
            ) : error ? (
              <Card className="card-error">{error}</Card>
            ) : (
              <div className="dashboard-grid">
                <div>
                  <Card className="card-section">
                    <div className="section-header">
                      <div>
                        <div className="section-title">My Tasks</div>
                        <div className="section-sub">Tasks assigned to you</div>
                      </div>
                      <Button className="btn-ghost" onClick={() => window.location.reload()}>
                        Refresh
                      </Button>
                    </div>
                  </Card>
                  <Card className="card-tasks">
                    <div className="tasks-list">
                      {tasks.length === 0 ? (
                        <div className="muted-text">No tasks to show.</div>
                      ) : tasks.map((t) => (
                        <div key={t.id} className="task-row">
                          <div className="task-main">
                            <div className="task-title">{t.title}</div>
                            <div className="task-desc">{t.description}</div>
                          </div>
                          <div className="task-meta">
                            {t.status ? <span className="muted-text">{t.status}</span> : <Badge tone="muted">pending</Badge>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>

                <aside className="aside-col">
                  <Card className="card-profile">
                    <div className="profile-heading">Profile</div>
                    <div className="profile-row">
                      <div className="avatar">{user?.full_name?.[0] || user?.email?.[0] || "U"}</div>
                      <div>
                        <div className="profile-name">{user?.full_name || user?.email}</div>
                        <div className="muted-text small"> {user?.role?.name || "Member"}</div>
                      </div>
                    </div>
                    <div style={{ marginTop: 14 }}>
                      <Button className="btn-primary" onClick={async () => {
                        try { await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/logout`, { method: "POST", credentials: "include" }); } catch {}
                        localStorage.removeItem("user");
                        window.location.href = "/login";
                      }}>Logout</Button>
                    </div>
                  </Card>

                  <Card className="card-quick">
                    <div className="section-title">Quick Actions</div>
                    <div className="quick-actions">
                      <button className="quick-btn quick-create">Create Task</button>
                      <button className="quick-btn quick-upload">Upload Statement</button>
                    </div>
                  </Card>
                </aside>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
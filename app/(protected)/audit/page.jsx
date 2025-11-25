"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/app/lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    entity_type: "",
    action: "",
    skip: 0,
    limit: 50,
  });

  useEffect(() => {
    loadLogs();
  }, [filters.entity_type, filters.action]);

  async function loadLogs() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.entity_type) params.append("entity_type", filters.entity_type);
      if (filters.action) params.append("action", filters.action);
      params.append("skip", filters.skip.toString());
      params.append("limit", filters.limit.toString());

      const data = await apiFetch(`/audit?${params.toString()}`);
      setLogs(data || []);
      setError(null);
    } catch (err) {
      setError(err?.body?.detail || err.message || "Failed to load audit logs");
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getActionColor = (action) => {
    if (action.includes("created") || action.includes("login")) return "text-green-600";
    if (action.includes("deleted") || action.includes("logout")) return "text-red-600";
    if (action.includes("updated") || action.includes("changed")) return "text-blue-600";
    return "text-gray-600";
  };

  return (
    <div className="layout-page">
      <div className="layout-main">
        <main className="page-content">
          <div className="page-container">
            <div className="page-heading">
              <h1 className="page-title">Audit Logs</h1>
              <div className="page-subtitle">
                Track all system activities and user actions
              </div>
            </div>

            {/* Filters */}
            <Card className="card-section" style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <div>
                  <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#666" }}>
                    Entity Type
                  </label>
                  <select
                    value={filters.entity_type}
                    onChange={(e) => setFilters({ ...filters, entity_type: e.target.value, skip: 0 })}
                    style={{
                      padding: "6px 12px",
                      border: "1px solid #ddd",
                      borderRadius: 6,
                      fontSize: 14,
                    }}
                  >
                    <option value="">All Types</option>
                    <option value="task">Task</option>
                    <option value="client">Client</option>
                    <option value="user">User</option>
                    <option value="permission">Permission</option>
                    <option value="document">Document</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#666" }}>
                    Action
                  </label>
                  <input
                    type="text"
                    value={filters.action}
                    onChange={(e) => setFilters({ ...filters, action: e.target.value, skip: 0 })}
                    placeholder="Filter by action..."
                    style={{
                      padding: "6px 12px",
                      border: "1px solid #ddd",
                      borderRadius: 6,
                      fontSize: 14,
                      minWidth: 200,
                    }}
                  />
                </div>
                <div style={{ flex: 1 }} />
                <Button className="btn-primary" onClick={loadLogs}>
                  Refresh
                </Button>
              </div>
            </Card>

            {loading ? (
              <Card className="card-loading">Loading audit logs...</Card>
            ) : error ? (
              <Card className="card-error">{error}</Card>
            ) : (
              <Card className="card-section">
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid #eee", textAlign: "left" }}>
                        <th style={{ padding: "12px", fontSize: 12, fontWeight: 600, color: "#666" }}>Timestamp</th>
                        <th style={{ padding: "12px", fontSize: 12, fontWeight: 600, color: "#666" }}>User</th>
                        <th style={{ padding: "12px", fontSize: 12, fontWeight: 600, color: "#666" }}>Action</th>
                        <th style={{ padding: "12px", fontSize: 12, fontWeight: 600, color: "#666" }}>Entity Type</th>
                        <th style={{ padding: "12px", fontSize: 12, fontWeight: 600, color: "#666" }}>Entity ID</th>
                        <th style={{ padding: "12px", fontSize: 12, fontWeight: 600, color: "#666" }}>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.length === 0 ? (
                        <tr>
                          <td colSpan={6} style={{ padding: 24, textAlign: "center", color: "#999" }}>
                            No audit logs found
                          </td>
                        </tr>
                      ) : (
                        logs.map((log) => (
                          <tr key={log.id} style={{ borderBottom: "1px solid #f0f0f0" }}>
                            <td style={{ padding: "12px", fontSize: 13 }}>
                              {formatDate(log.timestamp)}
                            </td>
                            <td style={{ padding: "12px", fontSize: 13 }}>
                              {log.user_full_name || log.user_email || `User #${log.performed_by || "N/A"}`}
                            </td>
                            <td style={{ padding: "12px", fontSize: 13 }}>
                              <span className={getActionColor(log.action)} style={{ fontWeight: 500 }}>
                                {log.action}
                              </span>
                            </td>
                            <td style={{ padding: "12px", fontSize: 13 }}>
                              <span style={{
                                padding: "2px 8px",
                                borderRadius: 4,
                                fontSize: 11,
                                background: "#f0f0f0",
                                color: "#666",
                              }}>
                                {log.entity_type}
                              </span>
                            </td>
                            <td style={{ padding: "12px", fontSize: 13, color: "#666" }}>
                              {log.entity_id || "N/A"}
                            </td>
                            <td style={{ padding: "12px", fontSize: 12, color: "#666", maxWidth: 300 }}>
                              {log.details ? (
                                <details>
                                  <summary style={{ cursor: "pointer", color: "#0066cc" }}>
                                    View Details
                                  </summary>
                                  <pre style={{
                                    marginTop: 8,
                                    padding: 8,
                                    background: "#f9f9f9",
                                    borderRadius: 4,
                                    fontSize: 11,
                                    overflow: "auto",
                                    maxHeight: 200,
                                  }}>
                                    {JSON.stringify(log.details, null, 2)}
                                  </pre>
                                </details>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {logs.length > 0 && (
                  <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ fontSize: 13, color: "#666" }}>
                      Showing {filters.skip + 1} - {filters.skip + logs.length} of logs
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                      <Button
                        className="btn-ghost"
                        onClick={() => setFilters({ ...filters, skip: Math.max(0, filters.skip - filters.limit) })}
                        disabled={filters.skip === 0}
                      >
                        Previous
                      </Button>
                      <Button
                        className="btn-ghost"
                        onClick={() => setFilters({ ...filters, skip: filters.skip + filters.limit })}
                        disabled={logs.length < filters.limit}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}


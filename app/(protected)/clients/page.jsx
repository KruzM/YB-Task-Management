"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/app/lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Link from "next/link";

export default function ClientsPage() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [groupByStatus, setGroupByStatus] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const params = new URLSearchParams();
        if (search) params.append("search", search);
        if (statusFilter) params.append("status", statusFilter);
        const response = await apiFetch(`/clients?${params.toString()}`);
        setClients(response?.clients || []);
      } catch {
        setClients([]);
      }
      setLoading(false);
    }
    load();
  }, [search, statusFilter]);

  const groupedClients = clients.reduce((acc, client) => {
    const key = client.status || "unspecified";
    acc[key] = acc[key] || [];
    acc[key].push(client);
    return acc;
  }, {});

  return (
    <div className="page-wrapper">

      <main className="page-main">

        {/* PAGE HEADER */}
        <div className="page-header-block">
          <h1 className="page-title">Clients</h1>
          <p className="page-subtext">Manage all business clients</p>
        </div>

        {/* MAIN CARD */}
        <Card>
          <div className="flex flex-col gap-3 mb-4">
            <div className="flex flex-wrap gap-2 items-center">
              <input
                type="text"
                placeholder="Search clients or contacts"
                className="input"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <select
                className="input max-w-xs"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="onboarding">Onboarding</option>
                <option value="inactive">Inactive</option>
              </select>
              <label className="flex items-center gap-2 text-sm text-muted">
                <input
                  type="checkbox"
                  checked={groupByStatus}
                  onChange={(e) => setGroupByStatus(e.target.checked)}
                />
                Group by status
              </label>
            </div>
          </div>

          <div className="table-header">
            <div>Client Name</div>
            <div>Primary Contact</div>
            <div>Status</div>
            <div>Actions</div>
          </div>

          {loading ? (
            <div className="empty-state">Loading...</div>
          ) : clients.length === 0 ? (
            <div className="empty-state">No clients added yet.</div>
          ) : groupByStatus ? (
            Object.keys(groupedClients).map((statusKey) => (
              <div key={statusKey} className="mb-4">
                <div className="table-subheader">{statusKey}</div>
                {groupedClients[statusKey].map((client) => (
                  <div key={client.id} className="table-row">
                    <div className="row-primary">{client.name}</div>
                    <div className="row-muted">{client.primary_contact || client.primary_email}</div>
                    <div>
                      <span className="pill">{client.status || "unknown"}</span>
                    </div>
                    <div>
                      <Link href={`/clients/${client.id}`} className="btn btn-primary small-btn">
                        View
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ))
          ) : (
            clients.map((client) => (
              <div key={client.id} className="table-row">
                <div className="row-primary">{client.name}</div>
                <div className="row-muted">{client.primary_contact || client.primary_email}</div>
                <div>
                  <span className="pill">{client.status || "unknown"}</span>
                </div>
                <div>
                  <Link href={`/clients/${client.id}`} className="btn btn-primary small-btn">
                    View
                  </Link>
                </div>
              </div>
            ))
          )}
        </Card>

      </main>
    </div>
  );
}
"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/app/lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Link from "next/link";

export default function ClientsPage() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const c = await apiFetch("/clients");
        setClients(c || []);
      } catch {
        setClients([]);
      }
      setLoading(false);
    }
    load();
  }, []);

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
          <div className="table-header">
            <div>Client Name</div>
            <div>Email</div>
            <div>Actions</div>
          </div>

          {loading ? (
            <div className="empty-state">Loading...</div>
          ) : clients.length === 0 ? (
            <div className="empty-state">No clients added yet.</div>
          ) : (
            clients.map((client) => (
              <div key={client.id} className="table-row">
                <div className="row-primary">{client.name}</div>
                <div className="row-muted">{client.email}</div>
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
"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/app/lib/api";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";

const emptyContact = { name: "", email: "", phone: "", title: "" };
const emptyAccount = { name: "", account_type: "", institution: "", number_last4: "" };
const emptyGroup = { name: "", description: "" };

export default function ClientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params?.id;

  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [contactForm, setContactForm] = useState(emptyContact);
  const [accountForm, setAccountForm] = useState(emptyAccount);
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState("");
  const [groupForm, setGroupForm] = useState(emptyGroup);

  const loadClient = async () => {
    if (!clientId) return;
    try {
      const data = await apiFetch(`/clients/${clientId}`);
      setClient(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const loadGroups = async () => {
    try {
      const response = await apiFetch("/clients/groups");
      setGroups(response?.groups || []);
    } catch (err) {
      console.error(err);
      setGroups([]);
    }
  };

  useEffect(() => {
    loadClient();
    loadGroups();
  }, [clientId]);

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    try {
      const updated = await apiFetch(`/clients/${clientId}/contacts`, {
        method: "POST",
        body: JSON.stringify(contactForm),
      });
      setClient(updated);
      setContactForm(emptyContact);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAccountSubmit = async (e) => {
    e.preventDefault();
    try {
      const created = await apiFetch(`/clients/${clientId}/accounts`, {
        method: "POST",
        body: JSON.stringify(accountForm),
      });
      setAccountForm(emptyAccount);
      setClient((prev) => ({ ...prev, accounts: [...(prev?.accounts || []), created] }));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleGroupAttach = async (e) => {
    e.preventDefault();
    if (!selectedGroup) return;
    try {
      const updated = await apiFetch(`/clients/${clientId}/groups/${selectedGroup}`, { method: "POST" });
      setClient(updated);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleGroupCreate = async (e) => {
    e.preventDefault();
    try {
      const created = await apiFetch(`/clients/groups`, {
        method: "POST",
        body: JSON.stringify(groupForm),
      });
      setGroupForm(emptyGroup);
      setGroups((prev) => [...prev, created]);
      setSelectedGroup(String(created.id));
    } catch (err) {
      alert(err.message);
    }
  };

  const relatedClients = useMemo(() => {
    if (!client?.groups?.length) return [];
    const related = [];
    client.groups.forEach((membership) => {
      const members = membership.group?.members || [];
      members
        .filter((member) => member.client_id && member.client_id !== client.id)
        .forEach((member) => {
          related.push({
            groupName: membership.group.name,
            clientId: member.client_id,
          });
        });
    });
    return related;
  }, [client]);

  if (loading) return <div className="page-wrapper">Loading...</div>;
  if (!client) return <div className="page-wrapper">Client not found</div>;

  return (
    <div className="page-wrapper">
      <main className="page-main">
        <div className="page-header-block">
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={() => router.back()}>
              ← Back
            </Button>
            <div>
              <h1 className="page-title">{client.name}</h1>
              <p className="page-subtext">Status: {client.status || "unknown"}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <h3 className="card-title">Primary Details</h3>
            <div className="stack">
              <div>
                <div className="label">Primary Contact</div>
                <div className="value">{client.primary_contact || "—"}</div>
              </div>
              <div>
                <div className="label">Email</div>
                <div className="value">{client.primary_email || "—"}</div>
              </div>
              <div>
                <div className="label">Phone</div>
                <div className="value">{client.primary_phone || "—"}</div>
              </div>
              <div>
                <div className="label">Billing Frequency</div>
                <div className="value">{client.billing_frequency || "—"}</div>
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="card-title">Accounts</h3>
            <div className="stack">
              {(client.accounts || []).length === 0 ? (
                <div className="empty-state">No accounts linked</div>
              ) : (
                client.accounts.map((account) => (
                  <div key={account.id} className="table-row">
                    <div className="row-primary">{account.name}</div>
                    <div className="row-muted">{account.institution}</div>
                    <div className="pill">{account.status}</div>
                  </div>
                ))
              )}
              <form onSubmit={handleAccountSubmit} className="form-grid">
                <input
                  required
                  className="input"
                  placeholder="Account name"
                  value={accountForm.name}
                  onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Institution"
                  value={accountForm.institution}
                  onChange={(e) => setAccountForm({ ...accountForm, institution: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Type"
                  value={accountForm.account_type}
                  onChange={(e) => setAccountForm({ ...accountForm, account_type: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Last 4"
                  value={accountForm.number_last4}
                  onChange={(e) => setAccountForm({ ...accountForm, number_last4: e.target.value })}
                />
                <Button type="submit">Add Account</Button>
              </form>
            </div>
          </Card>

          <Card>
            <h3 className="card-title">Contacts</h3>
            <div className="stack">
              {(client.contacts || []).length === 0 ? (
                <div className="empty-state">No contacts linked</div>
              ) : (
                client.contacts.map((contact) => (
                  <div key={contact.id} className="table-row">
                    <div className="row-primary">{contact.name}</div>
                    <div className="row-muted">{contact.email || contact.phone}</div>
                    <div className="pill">{contact.title || "Contact"}</div>
                  </div>
                ))
              )}
              <form onSubmit={handleContactSubmit} className="form-grid">
                <input
                  required
                  className="input"
                  placeholder="Name"
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Phone"
                  value={contactForm.phone}
                  onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Title / Role"
                  value={contactForm.title}
                  onChange={(e) => setContactForm({ ...contactForm, title: e.target.value })}
                />
                <Button type="submit">Add Contact</Button>
              </form>
            </div>
          </Card>

          <Card>
            <h3 className="card-title">Related Clients (Intercompany)</h3>
            <div className="stack">
              {(client.groups || []).length === 0 ? (
                <div className="empty-state">No groups assigned</div>
              ) : (
                client.groups.map((membership) => (
                  <div key={membership.id} className="table-row">
                    <div className="row-primary">{membership.group?.name}</div>
                    <div className="row-muted">{membership.group?.description}</div>
                  </div>
                ))
              )}
              <form onSubmit={handleGroupAttach} className="form-grid">
                <select
                  className="input"
                  value={selectedGroup}
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  required
                >
                  <option value="">Select group</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name}
                    </option>
                  ))}
                </select>
                <Button type="submit">Attach to Group</Button>
              </form>
              <form onSubmit={handleGroupCreate} className="form-grid">
                <input
                  required
                  className="input"
                  placeholder="New group name"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Description"
                  value={groupForm.description}
                  onChange={(e) => setGroupForm({ ...groupForm, description: e.target.value })}
                />
                <Button type="submit">Create Group</Button>
              </form>
              {relatedClients.length > 0 && (
                <div className="table-subheader">Linked Clients</div>
              )}
              {relatedClients.map((rc, idx) => (
                <div key={`${rc.clientId}-${idx}`} className="table-row">
                  <div className="row-primary">Client #{rc.clientId}</div>
                  <div className="row-muted">Group: {rc.groupName}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}

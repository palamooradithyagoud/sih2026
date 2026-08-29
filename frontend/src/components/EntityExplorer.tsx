"use client";

import React, { useState } from "react";
import {
  User,
  PhoneCall,
  DollarSign,
  MapPin,
  Car,
  Users,
  Building2,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Search,
  Filter,
} from "lucide-react";
import {
  Person,
  CallRecord,
  Transaction,
  Location,
  Vehicle,
  Relationship,
  Organization,
  Evidence,
  VerificationStatus,
} from "@/types/investigation";
import { investigationApi } from "@/lib/investigationApi";

interface EntityExplorerProps {
  caseId: string;
  persons: Person[];
  calls: CallRecord[];
  transactions: Transaction[];
  locations: Location[];
  vehicles: Vehicle[];
  relationships: Relationship[];
  organizations: Organization[];
  evidence: Evidence[];
  onRefresh: () => void;
}

export default function EntityExplorer({
  caseId,
  persons,
  calls,
  transactions,
  locations,
  vehicles,
  relationships,
  organizations,
  evidence,
  onRefresh,
}: EntityExplorerProps) {
  const [activeTab, setActiveTab] = useState<string>("persons");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const tabs = [
    { id: "persons", label: "Persons", count: persons.length, icon: User },
    { id: "calls", label: "Calls (CDR)", count: calls.length, icon: PhoneCall },
    { id: "transactions", label: "Transactions", count: transactions.length, icon: DollarSign },
    { id: "vehicles", label: "Vehicles", count: vehicles.length, icon: Car },
    { id: "locations", label: "Locations", count: locations.length, icon: MapPin },
    { id: "relationships", label: "Relationships", count: relationships.length, icon: Users },
    { id: "organizations", label: "Organizations", count: organizations.length, icon: Building2 },
    { id: "evidence", label: "Evidence Vault", count: evidence.length, icon: FileText },
  ];

  const handleToggleVerification = async (
    recordType: string,
    recordId: string,
    currentStatus: VerificationStatus
  ) => {
    setUpdatingId(recordId);
    const newStatus: VerificationStatus =
      currentStatus === "VERIFIED" ? "UNVERIFIED" : "VERIFIED";

    try {
      await investigationApi.updateVerification(
        caseId,
        recordType,
        recordId,
        newStatus,
        "Officer ID 1024 (Insp. Adithya)"
      );
      onRefresh();
    } catch (err) {
      console.error("Verification update failed", err);
    } finally {
      setUpdatingId(null);
    }
  };

  const matchesFilter = (item: any) => {
    if (filterStatus !== "ALL" && item.verification_status !== filterStatus) {
      return false;
    }
    if (!searchTerm.trim()) return true;
    const str = JSON.stringify(item).toLowerCase();
    return str.includes(searchTerm.toLowerCase());
  };

  return (
    <div className="entity-explorer-card">
      {/* Tab Navigation */}
      <div className="explorer-tabs-row">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`explorer-tab-btn ${isActive ? "active" : ""}`}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
              <span className="tab-count-pill">{tab.count}</span>
            </button>
          );
        })}
      </div>

      {/* Filter and Search Bar */}
      <div className="explorer-filter-bar">
        <div className="search-box-inline" style={{ width: "260px" }}>
          <Search size={14} style={{ color: "var(--text-muted)" }} />
          <input
            type="text"
            placeholder={`Search ${activeTab}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input-inline"
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginLeft: "auto" }}>
          <Filter size={14} style={{ color: "var(--text-muted)" }} />
          <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Filter Status:</span>
          {["ALL", "VERIFIED", "UNDER_REVIEW", "UNVERIFIED"].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`filter-pill ${filterStatus === status ? "active" : ""}`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Table Content */}
      <div className="table-responsive-wrapper">
        {/* 1. PERSONS TABLE */}
        {activeTab === "persons" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name / Status</th>
                <th>Linked Suspect & Observation</th>
                <th>Phone Numbers</th>
                <th>Known Aliases</th>
                <th>Occupation / Address</th>
                <th>Source & Officer</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {persons.filter(matchesFilter).map((p) => (
                <tr key={p.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{p.name}</div>
                    <span className={`mini-tag ${p.status === "SUSPECT" ? "status-suspect" : p.status === "WITNESS" ? "status-verified" : ""}`}>{p.status}</span>
                  </td>
                  <td style={{ maxWidth: "260px" }}>
                    {p.connected_person_name ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                          <span style={{ fontSize: "0.75rem", color: "var(--accent-cyan)", fontWeight: 600 }}>🔗 {p.connected_person_name}</span>
                          {p.connection_type && (
                            <span className="mini-tag" style={{ fontSize: "0.65rem", background: "rgba(0, 242, 254, 0.12)", color: "#38bdf8" }}>
                              {p.connection_type}
                            </span>
                          )}
                        </div>
                        {p.connection_notes && (
                          <div style={{ fontSize: "0.725rem", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: 1.3 }}>
                            &ldquo;{p.connection_notes}&rdquo;
                          </div>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Standalone Node</span>
                    )}
                  </td>
                  <td>{p.phone_numbers.length > 0 ? p.phone_numbers.join(", ") : "-"}</td>
                  <td>{p.known_aliases.length > 0 ? p.known_aliases.join(", ") : "-"}</td>
                  <td>
                    <div>{p.occupation || "-"}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{p.address || ""}</div>
                  </td>
                  <td>
                    <div style={{ fontSize: "0.8rem" }}>{p.source}</div>
                    <div style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>{p.added_by_officer}</div>
                  </td>
                  <td>
                    <span className={`status-indicator-badge ${p.verification_status === "VERIFIED" ? "connected" : p.verification_status === "UNDER_REVIEW" ? "connecting" : "disconnected"}`}>
                      {p.verification_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleToggleVerification("persons", p.id, p.verification_status)}
                      disabled={updatingId === p.id}
                      className="btn-action-small"
                    >
                      {p.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 2. CALLS TABLE */}
        {activeTab === "calls" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Caller</th>
                <th>Receiver</th>
                <th>Date & Time</th>
                <th>Duration</th>
                <th>Type / Tower</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {calls.filter(matchesFilter).map((c) => (
                <tr key={c.id}>
                  <td>
                    <strong>{c.caller_name || "Unknown"}</strong>
                    <div style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)" }}>{c.caller_number}</div>
                  </td>
                  <td>
                    <strong>{c.receiver_name || "Unknown"}</strong>
                    <div style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)" }}>{c.receiver_number}</div>
                  </td>
                  <td>
                    {c.date} <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>{c.time}</span>
                  </td>
                  <td>{c.duration_seconds}s ({Math.floor(c.duration_seconds / 60)}m {c.duration_seconds % 60}s)</td>
                  <td>
                    <div>{c.call_type}</div>
                    <div style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>{c.cell_tower_id || "-"}</div>
                  </td>
                  <td>
                    <span className={`status-indicator-badge ${c.verification_status === "VERIFIED" ? "connected" : "disconnected"}`}>
                      {c.verification_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleToggleVerification("calls", c.id, c.verification_status)}
                      disabled={updatingId === c.id}
                      className="btn-action-small"
                    >
                      {c.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 3. TRANSACTIONS TABLE */}
        {activeTab === "transactions" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Sender</th>
                <th>Receiver</th>
                <th>Amount (₹)</th>
                <th>Date / Time</th>
                <th>Txn ID & Bank</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {transactions.filter(matchesFilter).map((t) => (
                <tr key={t.id}>
                  <td>
                    <strong>{t.sender_name}</strong>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t.sender_account || ""}</div>
                  </td>
                  <td>
                    <strong>{t.receiver_name}</strong>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t.receiver_account || ""}</div>
                  </td>
                  <td style={{ color: "var(--accent-amber)", fontWeight: 700 }}>
                    ₹{t.amount.toLocaleString("en-IN")}
                  </td>
                  <td>
                    {t.date} <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>{t.time}</span>
                  </td>
                  <td>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{t.transaction_id}</div>
                    <div style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>{t.bank_name} • {t.payment_type}</div>
                  </td>
                  <td>
                    <span className={`status-indicator-badge ${t.verification_status === "VERIFIED" ? "connected" : "disconnected"}`}>
                      {t.verification_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleToggleVerification("transactions", t.id, t.verification_status)}
                      disabled={updatingId === t.id}
                      className="btn-action-small"
                    >
                      {t.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 4. VEHICLES TABLE */}
        {activeTab === "vehicles" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Registration</th>
                <th>Make & Model</th>
                <th>Type / Color</th>
                <th>Owner</th>
                <th>Associated Drivers</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {vehicles.filter(matchesFilter).map((v) => (
                <tr key={v.id}>
                  <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-cyan)" }}>
                    {v.registration_number}
                  </td>
                  <td>{v.make_model}</td>
                  <td>{v.vehicle_type} • {v.color || "-"}</td>
                  <td><strong>{v.owner_name || "Unknown"}</strong></td>
                  <td>{v.associated_persons.join(", ") || "-"}</td>
                  <td>
                    <span className={`status-indicator-badge ${v.verification_status === "VERIFIED" ? "connected" : "disconnected"}`}>
                      {v.verification_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleToggleVerification("vehicles", v.id, v.verification_status)}
                      disabled={updatingId === v.id}
                      className="btn-action-small"
                    >
                      {v.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 5. LOCATIONS TABLE */}
        {activeTab === "locations" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Landmark / Name</th>
                <th>Address</th>
                <th>Coordinates</th>
                <th>Associated Persons</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {locations.filter(matchesFilter).map((l) => (
                <tr key={l.id}>
                  <td><strong>{l.name}</strong></td>
                  <td>{l.address}</td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                    {l.latitude}, {l.longitude}
                  </td>
                  <td>{l.associated_persons.join(", ") || "-"}</td>
                  <td>
                    <span className={`status-indicator-badge ${l.verification_status === "VERIFIED" ? "connected" : "disconnected"}`}>
                      {l.verification_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleToggleVerification("locations", l.id, l.verification_status)}
                      disabled={updatingId === l.id}
                      className="btn-action-small"
                    >
                      {l.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 6. RELATIONSHIPS TABLE */}
        {activeTab === "relationships" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Person A</th>
                <th>Relationship</th>
                <th>Person B</th>
                <th>Findings / Description</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {relationships.filter(matchesFilter).map((r) => {
                const isSaw = r.relationship_type === "SAW_SUSPECT" || r.relationship_type === "EYEWITNESS";
                const isInf = r.relationship_type === "INFORMANT";
                const isCo = r.relationship_type === "CO_ACCUSED" || r.relationship_type === "CO_CONSPIRATOR";
                return (
                  <tr key={r.id}>
                    <td><strong>{r.person_a}</strong></td>
                    <td>
                      <span
                        className="mini-tag"
                        style={{
                          background: isSaw
                            ? "rgba(0, 242, 254, 0.15)"
                            : isInf
                            ? "rgba(168, 85, 247, 0.15)"
                            : isCo
                            ? "rgba(239, 68, 68, 0.15)"
                            : "rgba(139, 92, 246, 0.15)",
                          color: isSaw
                            ? "#00f2fe"
                            : isInf
                            ? "#c084fc"
                            : isCo
                            ? "#f87171"
                            : "#c084fc",
                          fontWeight: 600,
                        }}
                      >
                        {r.relationship_type === "SAW_SUSPECT" ? "👁️ SAW_SUSPECT" : r.relationship_type === "INFORMANT" ? "🕵️ INFORMANT" : r.relationship_type}
                      </span>
                    </td>
                    <td><strong>{r.person_b}</strong></td>
                    <td style={{ maxWidth: "340px", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                      {r.description || "-"}
                    </td>
                    <td>
                      <span className={`status-indicator-badge ${r.verification_status === "VERIFIED" ? "connected" : "disconnected"}`}>
                        {r.verification_status}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleToggleVerification("relationships", r.id, r.verification_status)}
                        disabled={updatingId === r.id}
                        className="btn-action-small"
                      >
                        {r.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {/* 7. ORGANIZATIONS TABLE */}
        {activeTab === "organizations" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Organization Name</th>
                <th>Type</th>
                <th>Registration / CIN</th>
                <th>Key Associated Members</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {organizations.filter(matchesFilter).map((o) => (
                <tr key={o.id}>
                  <td><strong>{o.name}</strong></td>
                  <td><span className="mini-tag" style={{ background: "rgba(56, 189, 248, 0.15)", color: "var(--accent-cyan)" }}>{o.org_type}</span></td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{o.registration_number || "-"}</td>
                  <td>{o.key_persons.join(", ") || "-"}</td>
                  <td>
                    <span className={`status-indicator-badge ${o.verification_status === "VERIFIED" ? "connected" : "disconnected"}`}>
                      {o.verification_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleToggleVerification("organizations", o.id, o.verification_status)}
                      disabled={updatingId === o.id}
                      className="btn-action-small"
                    >
                      {o.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 8. EVIDENCE TABLE */}
        {activeTab === "evidence" && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Evidence Title</th>
                <th>Category</th>
                <th>File Reference</th>
                <th>Date Obtained</th>
                <th>Custody Officer</th>
                <th>Verification</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {evidence.filter(matchesFilter).map((ev) => (
                <tr key={ev.id}>
                  <td>
                    <strong>{ev.title}</strong>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{ev.description}</div>
                  </td>
                  <td><span className="mini-tag status-suspect">{ev.evidence_type}</span></td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{ev.file_name}</td>
                  <td>{ev.date_obtained}</td>
                  <td>{ev.custody_officer}</td>
                  <td>
                    <span className={`status-indicator-badge ${ev.verification_status === "VERIFIED" ? "connected" : "disconnected"}`}>
                      {ev.verification_status}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleToggleVerification("evidence", ev.id, ev.verification_status)}
                      disabled={updatingId === ev.id}
                      className="btn-action-small"
                    >
                      {ev.verification_status === "VERIFIED" ? "Mark Unverified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

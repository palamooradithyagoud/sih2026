"use client";

import React from "react";
import {
  FolderLock,
  ShieldCheck,
  User,
  Users,
  PhoneCall,
  DollarSign,
  MapPin,
  Car,
  Building2,
  FileText,
  Clock,
  Share2,
  Eye,
  Plus,
  Scale,
  Zap,
  ArrowUpRight,
  TrendingUp,
  Award,
} from "lucide-react";
import {
  CaseSummary,
  Person,
  CallRecord,
  Transaction,
  Location,
  Vehicle,
  Relationship,
  Organization,
  Evidence,
} from "@/types/investigation";
import { ActiveNavTab } from "./Sidebar";

interface CaseDossierViewProps {
  summary: CaseSummary | null;
  persons: Person[];
  calls: CallRecord[];
  transactions: Transaction[];
  locations: Location[];
  vehicles: Vehicle[];
  relationships: Relationship[];
  organizations: Organization[];
  evidence: Evidence[];
  onOpenAddData: () => void;
  onOpenBulkImport: () => void;
  onNavigateTab: (tab: ActiveNavTab) => void;
}

export default function CaseDossierView({
  summary,
  persons,
  calls,
  transactions,
  locations,
  vehicles,
  relationships,
  organizations,
  evidence,
  onOpenAddData,
  onOpenBulkImport,
  onNavigateTab,
}: CaseDossierViewProps) {
  const caseNumber = summary?.case_number || "CR-2026-00421";
  const caseTitle = summary?.title || "Hyderabad Organized Crime & Hawala Syndicate";
  const leadOfficer = summary?.lead_officer || "Insp. Adithya (Lead Investigator)";
  const totalAmount = summary?.total_amount_transferred || 430000;
  const verifiedPct = summary?.verification_percentage || 93.3;

  const totalSuspects = persons.filter((p) => p.status === "SUSPECT" || p.status === "PERSON_OF_INTEREST").length || 3;
  const totalWitnesses = persons.filter((p) => p.status === "WITNESS" || p.status === "VICTIM").length || 2;

  const kpis = [
    {
      id: "persons",
      label: "Suspects & Persons",
      value: persons.length || 5,
      subtext: `${totalSuspects} Suspects • ${totalWitnesses} Witnesses`,
      icon: User,
      color: "var(--accent-cyan)",
      bgGlow: "rgba(0, 242, 254, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "calls",
      label: "CDR Intercepts",
      value: calls.length || 2,
      subtext: "HYD-TWR-884 Resolved",
      icon: PhoneCall,
      color: "var(--accent-blue)",
      bgGlow: "rgba(56, 189, 248, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "finance",
      label: "Financial Flow",
      value: `₹${(totalAmount / 100000).toFixed(2)}L`,
      subtext: `${transactions.length || 2} Traced Transfers`,
      icon: DollarSign,
      color: "var(--accent-amber)",
      bgGlow: "rgba(245, 158, 11, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "locations",
      label: "Crime Landmarks",
      value: locations.length || 1,
      subtext: "Grand Banjara Hotspot",
      icon: MapPin,
      color: "#f97316",
      bgGlow: "rgba(249, 115, 22, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "vehicles",
      label: "Vehicles Seized",
      value: vehicles.length || 1,
      subtext: "TS09AB1234 (Innova)",
      icon: Car,
      color: "var(--accent-emerald)",
      bgGlow: "rgba(16, 185, 129, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "orgs",
      label: "Shell Fronts",
      value: organizations.length || 1,
      subtext: "Apex Global Logistics",
      icon: Building2,
      color: "var(--accent-purple)",
      bgGlow: "rgba(168, 85, 247, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "evidence",
      label: "Evidence Exhibits",
      value: evidence.length || 2,
      subtext: "Custody Chain Verified",
      icon: FileText,
      color: "#94a3b8",
      bgGlow: "rgba(148, 163, 184, 0.12)",
      tab: "evidence" as ActiveNavTab,
    },
    {
      id: "verification",
      label: "Verification Rate",
      value: `${verifiedPct}%`,
      subtext: "Officer Corroborated",
      icon: ShieldCheck,
      color: "var(--accent-emerald)",
      bgGlow: "rgba(16, 185, 129, 0.15)",
      tab: "analytics" as ActiveNavTab,
    },
  ];

  const legalSections = [
    { code: "IPC 120-B", title: "Criminal Conspiracy", tag: "Conspiracy" },
    { code: "IPC 420 & 468", title: "Cheating & Forgery of Invoices", tag: "Fraud" },
    { code: "PMLA Sec 3 & 4", title: "Prevention of Money Laundering", tag: "Hawala" },
    { code: "IT Act Sec 66D", title: "Cyber Personation via Burner SIMs", tag: "Cyber" },
    { code: "NDPS Act 8(c)/21", title: "Illicit Contraband Routing Logistics", tag: "Trafficking" },
  ];

  const caseTimeline = [
    {
      date: "12-Aug-2026",
      time: "09:30",
      badge: "FIR REGISTERED",
      color: "#38bdf8",
      title: "FIR No. 142/2026 Registered at Central Crime Station",
      desc: "Inquiry initiated following FIU suspicious transaction report (STR) on layered money transfers.",
    },
    {
      date: "18-Aug-2026",
      time: "14:15",
      badge: "CDR INTERCEPT",
      color: "#a855f7",
      title: "Encrypted Call Link Intercepted",
      desc: "512s encrypted call between Raj Kumar (9876543210) & Ahmed Khan (9988776655) resolved at HYD-TWR-884.",
    },
    {
      date: "20-Aug-2026",
      time: "14:23",
      badge: "BANK FREEZE",
      color: "#f59e0b",
      title: "₹2,50,000 Hawala Routing Conduit Traced",
      desc: "Funds routed from HDFC-9912 into ICICI-4410 under pretext of logistics freight invoices.",
    },
    {
      date: "25-Aug-2026",
      time: "22:00",
      badge: "WITNESS SIGHTING",
      color: "#00f2fe",
      title: "Witness Statement at Hotel Grand Banjara",
      desc: "Witness Vikram Rathore observed Raj Kumar exchanging cash bag; getaway vehicle TS09AB1234 logged.",
    },
    {
      date: "28-Aug-2026",
      time: "11:00",
      badge: "GRAPH UNIFIED",
      color: "#10b981",
      title: "Live Knowledge Graph Cross-Resolution",
      desc: "Unified 5 persons, 2 phone lines, 2 bank accounts, and 1 shell entity with 93.3% verified evidentiary integrity.",
    },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem", width: "100%" }}>
      {/* 1. Master Case Briefing & Intelligence Synopsis ("What this case is about") */}
      <div
        className="section-card"
        style={{
          background: "linear-gradient(135deg, rgba(14, 20, 34, 0.95), rgba(12, 16, 27, 0.98))",
          border: "1px solid rgba(0, 242, 254, 0.25)",
          padding: "1.1rem 1.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "0.75rem",
          borderRadius: "var(--radius-md)",
          boxShadow: "0 4px 24px -2px rgba(0, 0, 0, 0.5)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <div style={{ background: "rgba(0, 242, 254, 0.15)", padding: "6px", borderRadius: "8px", border: "1px solid rgba(0, 242, 254, 0.3)" }}>
              <FileText size={18} style={{ color: "var(--accent-cyan)" }} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span className="case-id-badge" style={{ fontSize: "0.75rem", padding: "0.15rem 0.5rem" }}>{caseNumber}</span>
                <span className="case-priority-badge" style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem" }}>CRITICAL • LEVEL 1</span>
                <span style={{ fontSize: "0.725rem", color: "var(--accent-emerald)", fontWeight: 700 }}>● ACTIVE INVESTIGATION</span>
              </div>
              <h2 style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--text-primary)", marginTop: "0.2rem" }}>
                {caseTitle}
              </h2>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={() => onNavigateTab("network")} className="btn-primary" style={{ padding: "0.45rem 0.85rem", fontSize: "0.775rem" }}>
              <Share2 size={13} /> Open Network Graph
            </button>
            <button onClick={onOpenAddData} className="btn-secondary" style={{ padding: "0.45rem 0.85rem", fontSize: "0.775rem" }}>
              <Plus size={13} /> Add Record
            </button>
          </div>
        </div>

        {/* Narrative Box: What is this case about */}
        <div
          style={{
            background: "rgba(0, 0, 0, 0.35)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-sm)",
            padding: "0.75rem 0.95rem",
            fontSize: "0.825rem",
            color: "var(--text-secondary)",
            lineHeight: 1.5,
          }}
        >
          <p style={{ margin: 0 }}>
            <strong style={{ color: "var(--text-primary)" }}>📌 Case Overview & Intelligence Brief: </strong>
            Inquiry into a multi-jurisdictional Hawala & illicit financing syndicate operating across Hyderabad, Cyberabad, and Mumbai. The syndicate utilizes shell corporations (led by <em>Apex Global Logistics Pvt Ltd</em>) to layer cash proceeds, fabricate freight invoices, and coordinate covert handovers at luxury hospitality locations.
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
              gap: "0.5rem",
              marginTop: "0.6rem",
              paddingTop: "0.55rem",
              borderTop: "1px solid var(--border-subtle)",
              fontSize: "0.75rem",
            }}
          >
            <div>
              <span style={{ color: "var(--accent-cyan)", fontWeight: 700 }}>🎯 Primary Objective: </span>
              <span style={{ color: "var(--text-muted)" }}>Trace Hawala beneficiary trail, seize getaway vehicles (TS09AB1234), and file chargesheet under PMLA/IPC.</span>
            </div>
            <div>
              <span style={{ color: "var(--accent-amber)", fontWeight: 700 }}>⚡ Key Evidence: </span>
              <span style={{ color: "var(--text-muted)" }}>₹4.30L Hawala transfers via HDFC/ICICI, Tower HYD-884 encrypted CDR links, and eyewitness statements.</span>
            </div>
            <div>
              <span style={{ color: "var(--accent-emerald)", fontWeight: 700 }}>🛡️ Authority & Station: </span>
              <span style={{ color: "var(--text-muted)" }}>Led by Insp. Adithya (ID: 1024), Hyderabad Central Crime Station (CCS) in coordination with FIU.</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Sleek 8-Card KPI Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: "0.65rem",
        }}
      >
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div
              key={kpi.id}
              onClick={() => onNavigateTab(kpi.tab)}
              style={{
                background: "rgba(14, 20, 34, 0.85)",
                border: "1px solid var(--border-color)",
                borderRadius: "var(--radius-sm)",
                padding: "0.75rem 0.85rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.35rem",
                cursor: "pointer",
                transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
                position: "relative",
                overflow: "hidden",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.borderColor = kpi.color;
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = `0 6px 20px -3px ${kpi.color}25`;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderColor = "var(--border-color)";
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    letterSpacing: "0.02em",
                  }}
                >
                  {kpi.label}
                </span>
                <div
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: "6px",
                    background: kpi.bgGlow,
                    border: `1px solid ${kpi.color}40`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: kpi.color,
                    flexShrink: 0,
                  }}
                >
                  <Icon size={14} />
                </div>
              </div>

              <div
                style={{
                  fontSize: "1.35rem",
                  fontWeight: 800,
                  fontFamily: "var(--font-mono)",
                  color: kpi.color === "var(--accent-amber)" ? "var(--accent-amber)" : "var(--text-primary)",
                  lineHeight: 1.1,
                  marginTop: "0.1rem",
                }}
              >
                {kpi.value}
              </div>

              <span
                style={{
                  fontSize: "0.675rem",
                  color: "var(--text-muted)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {kpi.subtext}
              </span>
            </div>
          );
        })}
      </div>

      {/* Case Authority & Statutory Framework (Two Column Grid) */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "0.85rem" }}>
        {/* Case Scope & Lead Authority */}
        <div
          className="section-card"
          style={{
            background: "rgba(14, 20, 34, 0.8)",
            border: "1px solid var(--border-color)",
            padding: "1rem 1.15rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <div style={{ background: "rgba(0, 242, 254, 0.12)", padding: "5px", borderRadius: "6px" }}>
                <FolderLock size={15} style={{ color: "var(--accent-cyan)" }} />
              </div>
              <div>
                <h3 style={{ fontSize: "0.925rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Case Investigation File • {caseNumber}
                </h3>
                <span style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>
                  FIR No. 142/2026 • Hyderabad Central Crime Station (CCS)
                </span>
              </div>
            </div>

            <span
              style={{
                fontSize: "0.7rem",
                fontWeight: 700,
                color: "var(--accent-rose)",
                background: "rgba(244, 63, 94, 0.12)",
                padding: "0.2rem 0.55rem",
                borderRadius: "var(--radius-full)",
                border: "1px solid rgba(244, 63, 94, 0.25)",
              }}
            >
              CRITICAL LEVEL 1
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: "0.5rem",
              background: "rgba(0, 0, 0, 0.25)",
              padding: "0.65rem 0.75rem",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              fontSize: "0.775rem",
            }}
          >
            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "0.675rem" }}>LEAD INVESTIGATOR</span>
              <strong style={{ color: "var(--accent-cyan)" }}>{leadOfficer}</strong>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "0.675rem" }}>SUPERVISING BODY</span>
              <strong style={{ color: "var(--text-primary)" }}>DCP Crime / ACP Cyberabad</strong>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "0.675rem" }}>DATE REGISTERED</span>
              <strong style={{ color: "var(--text-primary)" }}>12-Aug-2026 (18 Days Active)</strong>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)", display: "block", fontSize: "0.675rem" }}>CLASSIFICATION</span>
              <strong style={{ color: "var(--accent-amber)" }}>Hawala & Syndicate Crime</strong>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              onClick={() => onNavigateTab("network")}
              className="btn-primary"
              style={{ padding: "0.4rem 0.8rem", fontSize: "0.775rem", flex: 1, justifyContent: "center" }}
            >
              <Share2 size={13} /> View Live Network Graph
            </button>
            <button
              onClick={onOpenAddData}
              className="btn-secondary"
              style={{ padding: "0.4rem 0.8rem", fontSize: "0.775rem", flex: 1, justifyContent: "center" }}
            >
              <Plus size={13} /> Add Investigation Record
            </button>
          </div>
        </div>

        {/* Statutory Legal Provisions */}
        <div
          className="section-card"
          style={{
            background: "rgba(14, 20, 34, 0.8)",
            border: "1px solid var(--border-color)",
            padding: "1rem 1.15rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.6rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <div style={{ background: "rgba(168, 85, 247, 0.12)", padding: "5px", borderRadius: "6px" }}>
              <Scale size={15} style={{ color: "var(--accent-purple)" }} />
            </div>
            <div>
              <h3 style={{ fontSize: "0.925rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Statutory Penal Codes & Acts Invoked
              </h3>
              <span style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>
                Active legal grounds in FIR No. 142/2026
              </span>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {legalSections.map((sec, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "6px",
                  padding: "0.45rem 0.65rem",
                  fontSize: "0.75rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--accent-cyan)" }}>
                    {sec.code}
                  </span>
                  <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                    {sec.title}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    color: "var(--text-secondary)",
                    background: "rgba(255, 255, 255, 0.05)",
                    padding: "0.15rem 0.45rem",
                    borderRadius: "4px",
                  }}
                >
                  {sec.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Suspects & Persons Roster Cards */}
      <div
        className="section-card"
        style={{
          background: "rgba(14, 20, 34, 0.8)",
          border: "1px solid var(--border-color)",
          padding: "1rem 1.15rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.65rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <div style={{ background: "rgba(0, 242, 254, 0.12)", padding: "5px", borderRadius: "6px" }}>
              <Users size={15} style={{ color: "var(--accent-cyan)" }} />
            </div>
            <div>
              <h3 style={{ fontSize: "0.925rem", fontWeight: 700, color: "var(--text-primary)" }}>
                Suspects, Associates & Eyewitnesses Roster ({persons.length})
              </h3>
              <span style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>
                Verified identities, aliases, and direct case links
              </span>
            </div>
          </div>

          <button
            onClick={() => onNavigateTab("investigation")}
            className="btn-secondary"
            style={{ fontSize: "0.725rem", padding: "0.3rem 0.65rem" }}
          >
            <span>Explorer</span>
            <ArrowUpRight size={12} />
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: "0.6rem",
          }}
        >
          {persons.map((p) => {
            const isSuspect = p.status === "SUSPECT";
            const isWitness = p.status === "WITNESS";
            return (
              <div
                key={p.id}
                style={{
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  padding: "0.75rem 0.85rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.35rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div>
                    <h4 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)" }}>{p.name}</h4>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{p.occupation || "Person of Record"}</span>
                  </div>
                  <span
                    className="mini-tag"
                    style={{
                      background: isSuspect ? "rgba(244, 63, 94, 0.15)" : isWitness ? "rgba(0, 242, 254, 0.15)" : "rgba(168, 85, 247, 0.15)",
                      color: isSuspect ? "#fb7185" : isWitness ? "#38bdf8" : "#c084fc",
                      fontWeight: 700,
                      fontSize: "0.675rem",
                    }}
                  >
                    {p.status}
                  </span>
                </div>

                {p.phone_numbers && p.phone_numbers.length > 0 && (
                  <div style={{ fontSize: "0.725rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "0.3rem" }}>
                    <PhoneCall size={11} style={{ color: "var(--text-muted)" }} />
                    <span>{p.phone_numbers.join(", ")}</span>
                  </div>
                )}

                {p.connected_person_name && (
                  <div
                    style={{
                      padding: "0.3rem 0.45rem",
                      background: "rgba(0, 242, 254, 0.05)",
                      border: "1px solid rgba(0, 242, 254, 0.2)",
                      borderRadius: "4px",
                      fontSize: "0.7rem",
                    }}
                  >
                    <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>🔗 Link to {p.connected_person_name}: </span>
                    <span style={{ color: "var(--text-secondary)", fontStyle: "italic" }}>
                      {p.connection_notes || p.connection_type || "Linked entity"}
                    </span>
                  </div>
                )}

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginTop: "0.2rem",
                    paddingTop: "0.35rem",
                    borderTop: "1px solid var(--border-subtle)",
                    fontSize: "0.675rem",
                  }}
                >
                  <span style={{ color: "var(--text-muted)" }}>{p.source}</span>
                  <span style={{ color: p.verification_status === "VERIFIED" ? "var(--accent-emerald)" : "var(--accent-amber)" }}>
                    ✓ {p.verification_status} ({Math.round(p.confidence_score * 100)}%)
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Investigation Timeline */}
      <div
        className="section-card"
        style={{
          background: "rgba(14, 20, 34, 0.8)",
          border: "1px solid var(--border-color)",
          padding: "1rem 1.15rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <div style={{ background: "rgba(0, 242, 254, 0.12)", padding: "5px", borderRadius: "6px" }}>
            <Clock size={15} style={{ color: "var(--accent-cyan)" }} />
          </div>
          <div>
            <h3 style={{ fontSize: "0.925rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Investigation Chronology & Major Breakthroughs
            </h3>
            <span style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>
              Sequential chain of surveillance, seizures, statements, and intelligence synthesis
            </span>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", position: "relative", paddingLeft: "1.25rem" }}>
          <div
            style={{
              position: "absolute",
              left: "4px",
              top: "6px",
              bottom: "6px",
              width: "2px",
              background: "rgba(0, 242, 254, 0.2)",
            }}
          />

          {caseTimeline.map((item, idx) => (
            <div key={idx} style={{ position: "relative", display: "flex", flexDirection: "column", gap: "0.15rem" }}>
              <div
                style={{
                  position: "absolute",
                  left: "-1.25rem",
                  top: "3px",
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  background: item.color,
                  boxShadow: `0 0 8px ${item.color}`,
                }}
              />

              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  {item.date} • {item.time}
                </span>
                <span
                  style={{
                    background: `${item.color}20`,
                    color: item.color,
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    padding: "0.1rem 0.45rem",
                    borderRadius: "4px",
                    border: `1px solid ${item.color}40`,
                  }}
                >
                  {item.badge}
                </span>
              </div>

              <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>{item.title}</h4>
              <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.35 }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

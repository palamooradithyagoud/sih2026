"use client";

import React, { useMemo } from "react";
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

// Helper to determine accurate investigation classification based on actual case details
function getCaseClassification(
  title: string,
  desc: string,
  persons: Person[],
  txns: Transaction[],
  calls: CallRecord[]
): string {
  const text = `${title} ${desc}`.toLowerCase();
  if (
    text.includes("pocso") ||
    text.includes("sexual") ||
    text.includes("minor") ||
    text.includes("child") ||
    text.includes("rape") ||
    text.includes("assault")
  ) {
    return "POCSO & Heinous Offences";
  }
  if (
    text.includes("murder") ||
    text.includes("homicide") ||
    text.includes("encounter") ||
    text.includes("death") ||
    text.includes("dead body") ||
    text.includes("killed")
  ) {
    return "Homicide & Special Squad";
  }
  if (
    text.includes("hawala") ||
    text.includes("laundering") ||
    text.includes("pmla") ||
    text.includes("shell") ||
    text.includes("illicit financing") ||
    txns.length > 0
  ) {
    return "Financial Fraud & Economic Offences";
  }
  if (
    text.includes("cyber") ||
    text.includes("phishing") ||
    text.includes("loan app") ||
    text.includes("telegram") ||
    text.includes("otp") ||
    text.includes("it act") ||
    calls.length > 0
  ) {
    return "Cyber Syndicate & Telecom Intercept";
  }
  if (
    text.includes("ndps") ||
    text.includes("narcotic") ||
    text.includes("drug") ||
    text.includes("contraband") ||
    text.includes("smuggling")
  ) {
    return "Narcotics & Contraband Control";
  }
  return "Special Criminal Investigation";
}

// Helper to extract or generate relevant legal codes based on actual uploaded case data
function getDynamicLegalSections(
  title: string,
  desc: string,
  classification: string,
  evidence: Evidence[]
) {
  const combined = `${title} ${desc} ${evidence
    .map((e) => `${e.title} ${e.description}`)
    .join(" ")}`;
  const extracted: { code: string; title: string; tag: string }[] = [];

  // Match POCSO citations
  if (/pocso/i.test(combined)) {
    const pocsoMatch = combined.match(
      /pocso\s*(?:act)?\s*(?:sec(?:tion)?s?\.?\s*)?([0-9\s,&/and]+)/i
    );
    const secs = pocsoMatch ? pocsoMatch[1].trim() : "4, 8, 12";
    extracted.push({
      code: `POCSO Sec ${secs}`,
      title: "Protection of Children from Sexual Offences Act",
      tag: "POCSO",
    });
  }

  // Match IPC / BNS citations
  const ipcMatches = combined.match(
    /(?:IPC|BNS|Indian Penal Code)\s*(?:Sec(?:tion)?s?\.?\s*)?([0-9\s,&/\-+A-Za-z]+)/gi
  );
  if (ipcMatches) {
    ipcMatches.slice(0, 2).forEach((match) => {
      const cleanMatch = match.replace(/Indian Penal Code/i, "IPC").trim();
      let secTitle = "Statutory Penal Code Offence";
      let tag = "Penal Code";
      if (/376|64/i.test(cleanMatch)) {
        secTitle = "Sexual Assault & Heinous Offences";
        tag = "Heinous";
      } else if (/420|468|471/i.test(cleanMatch)) {
        secTitle = "Cheating, Forgery & Fraud";
        tag = "Fraud";
      } else if (/120-?B/i.test(cleanMatch)) {
        secTitle = "Criminal Conspiracy";
        tag = "Conspiracy";
      } else if (/302|103/i.test(cleanMatch)) {
        secTitle = "Punishment for Murder";
        tag = "Homicide";
      } else if (/384|386|506/i.test(cleanMatch)) {
        secTitle = "Extortion & Criminal Intimidation";
        tag = "Intimidation";
      }
      extracted.push({ code: cleanMatch, title: secTitle, tag });
    });
  }

  // Match IT Act
  if (/it\s*act|66[a-z]?/i.test(combined)) {
    const itMatch = combined.match(
      /IT\s*Act\s*(?:Sec(?:tion)?s?\.?\s*)?([68][0-9A-Z\s,&/]+)/i
    );
    extracted.push({
      code: itMatch ? itMatch[0] : "IT Act Sec 66D",
      title: "Cyber Identity Theft & Electronic Fraud",
      tag: "Cyber",
    });
  }

  // Match PMLA / NDPS
  if (/pmla/i.test(combined)) {
    extracted.push({
      code: "PMLA Sec 3 & 4",
      title: "Prevention of Money Laundering Act",
      tag: "PMLA",
    });
  }
  if (/ndps/i.test(combined)) {
    extracted.push({
      code: "NDPS Act Sec 20/22",
      title: "Narcotic Drugs & Psychotropic Substances",
      tag: "NDPS",
    });
  }

  if (extracted.length > 0) {
    const unique = [];
    const seen = new Set();
    for (const item of extracted) {
      if (!seen.has(item.code)) {
        seen.add(item.code);
        unique.push(item);
      }
    }
    return unique.slice(0, 4);
  }

  // Contextual fallback based on detected case classification
  if (classification.includes("POCSO")) {
    return [
      {
        code: "POCSO Act Sec 4 & 8",
        title: "Aggravated Sexual Assault on Minor",
        tag: "POCSO",
      },
      {
        code: "IPC Sec 376 / BNS 64",
        title: "Sexual Offences & Heinous Assault",
        tag: "Heinous",
      },
      {
        code: "IPC Sec 506",
        title: "Criminal Intimidation & Threat",
        tag: "Intimidation",
      },
    ];
  }
  if (classification.includes("Financial")) {
    return [
      { code: "IPC 120-B", title: "Criminal Conspiracy", tag: "Conspiracy" },
      { code: "IPC 420 & 468", title: "Cheating & Forgery", tag: "Fraud" },
      {
        code: "IT Act Sec 66D",
        title: "Cyber Personation & Electronic Records",
        tag: "Cyber",
      },
    ];
  }
  if (classification.includes("Homicide")) {
    return [
      {
        code: "IPC Sec 302 / BNS 103",
        title: "Punishment for Murder",
        tag: "Homicide",
      },
      { code: "IPC Sec 120-B", title: "Criminal Conspiracy", tag: "Conspiracy" },
      {
        code: "Arms Act Sec 25/27",
        title: "Prohibited Arms & Weaponry",
        tag: "Arms Act",
      },
    ];
  }
  if (classification.includes("Cyber")) {
    return [
      {
        code: "IT Act Sec 66C & 66D",
        title: "Identity Theft & Personation",
        tag: "Cyber",
      },
      { code: "IPC 420", title: "Cheating & Dishonesty", tag: "Fraud" },
      { code: "IPC 120-B", title: "Criminal Conspiracy", tag: "Conspiracy" },
    ];
  }

  return [
    { code: "IPC 120-B", title: "Criminal Conspiracy", tag: "Conspiracy" },
    { code: "IPC 420", title: "Cheating & Inducement", tag: "Penal Code" },
    {
      code: "CrPC Sec 154",
      title: "First Information Report Proceedings",
      tag: "Statutory",
    },
  ];
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
  const caseNumber = summary?.case_number || "NO CASE ACTIVE";
  const caseTitle = summary?.title || "Investigation Docket";
  const leadOfficer = summary?.lead_officer || "Investigating Officer";
  const stationName = summary?.station || "Crime Investigation Branch";
  const priorityText = summary?.priority || "CRITICAL";
  const totalAmount = summary?.total_amount_transferred ?? 0;
  const verifiedPct = summary?.verification_percentage ?? 0;

  const totalSuspects = persons.filter(
    (p) => p.status === "SUSPECT" || p.status === "PERSON_OF_INTEREST"
  ).length;
  const totalWitnesses = persons.filter(
    (p) => p.status === "WITNESS" || p.status === "VICTIM"
  ).length;

  const caseClassification = useMemo(
    () =>
      getCaseClassification(
        caseTitle,
        summary?.description || "",
        persons,
        transactions,
        calls
      ),
    [caseTitle, summary?.description, persons, transactions, calls]
  );

  const legalSections = useMemo(
    () =>
      getDynamicLegalSections(
        caseTitle,
        summary?.description || "",
        caseClassification,
        evidence
      ),
    [caseTitle, summary?.description, caseClassification, evidence]
  );

  // Dynamic Case Overview & Intelligence Brief (Strictly reflecting actual uploaded data)
  const overviewText = useMemo(() => {
    if (
      summary?.description &&
      summary.description.trim().length > 15 &&
      !summary.description.includes("AI-Assisted Investigation from document ingestion")
    ) {
      return summary.description;
    }

    const parts: string[] = [];
    const suspectList = persons.filter(
      (p) => p.status === "SUSPECT" || p.status === "PERSON_OF_INTEREST"
    );
    const witnessList = persons.filter(
      (p) => p.status === "WITNESS" || p.status === "VICTIM"
    );

    if (suspectList.length > 0) {
      const names = suspectList
        .map((p) => p.name)
        .slice(0, 3)
        .join(", ");
      parts.push(
        `Investigation focused on named individual(s) including ${names}${
          suspectList.length > 3 ? ` and ${suspectList.length - 3} others` : ""
        }.`
      );
    }
    if (witnessList.length > 0) {
      parts.push(
        `Corroborated by recorded statements from ${witnessList.length} witness(es) / victim(s).`
      );
    }
    if (locations.length > 0) {
      const locs = locations
        .map((l) => l.name)
        .slice(0, 2)
        .join(" and ");
      parts.push(`Key crime scenes and landmark sightings mapped at ${locs}.`);
    }
    if (transactions.length > 0) {
      parts.push(
        `Financial trail totaling ₹${(totalAmount / 100000).toFixed(
          2
        )}L traced across ${transactions.length} transfer record(s).`
      );
    }
    if (calls.length > 0) {
      parts.push(
        `Telecom CDR intelligence resolved across ${calls.length} intercepted call log(s).`
      );
    }
    if (evidence.length > 0) {
      parts.push(
        `${evidence.length} documentary and physical exhibits registered in custody.`
      );
    }

    if (parts.length > 0) {
      return parts.join(" ");
    }

    return `Active investigation file registered under reference ${caseNumber}. Ingest case documents or record entities to generate the real-time intelligence synopsis.`;
  }, [
    summary?.description,
    persons,
    locations,
    transactions,
    calls,
    evidence,
    totalAmount,
    caseNumber,
  ]);

  // Dynamic Primary Objective based on uploaded entities
  const primaryObjectiveText = useMemo(() => {
    const suspectList = persons.filter(
      (p) => p.status === "SUSPECT" || p.status === "PERSON_OF_INTEREST"
    );
    const suspectNames = suspectList
      .map((p) => p.name)
      .slice(0, 2)
      .join(" & ");

    if (suspectList.length > 0 && totalAmount > 0) {
      return `Apprehend primary suspect(s) (${suspectNames}), freeze ₹${(
        totalAmount / 100000
      ).toFixed(2)}L in traced illicit funds, and file statutory chargesheet.`;
    }
    if (suspectList.length > 0 && vehicles.length > 0) {
      const vPlates = vehicles
        .map((v) => v.registration_number)
        .slice(0, 2)
        .join(", ");
      return `Trace and interrogate primary suspect(s) (${suspectNames}), impound vehicle(s) (${vPlates}), and submit final investigation report.`;
    }
    if (suspectList.length > 0) {
      return `Establish verifiable evidentiary timeline, interrogate primary suspect(s) (${suspectNames}), and submit chargesheet under statutory provisions.`;
    }
    if (totalAmount > 0) {
      return `Trace illicit financial beneficiary accounts totaling ₹${(
        totalAmount / 100000
      ).toFixed(2)}L and freeze associated bank assets.`;
    }
    if (calls.length > 0) {
      return `Corroborate CDR tower geo-intercepts, establish accomplice call chains, and identify lead conspirators.`;
    }
    if (evidence.length > 0) {
      return `Secure evidentiary custody chain for ${evidence.length} exhibit(s) and corroborate statements under law.`;
    }
    return `Corroborate investigative leads, establish entity relationships, and compile verified court dossier.`;
  }, [persons, totalAmount, vehicles, calls, evidence]);

  // Dynamic Key Evidence Summary based on uploaded evidence
  const keyEvidenceText = useMemo(() => {
    const evidencePoints: string[] = [];

    if (totalAmount > 0) {
      const banks = Array.from(
        new Set(transactions.map((t) => t.bank_name).filter(Boolean))
      )
        .slice(0, 2)
        .join("/");
      evidencePoints.push(
        `₹${(totalAmount / 100000).toFixed(2)}L financial flow${
          banks ? ` via ${banks}` : ""
        }`
      );
    }
    if (calls.length > 0) {
      const towers = Array.from(
        new Set(calls.map((c) => c.cell_tower_id).filter(Boolean))
      );
      evidencePoints.push(
        `${calls.length} CDR logs${
          towers.length > 0 ? ` (${towers.slice(0, 2).join(", ")})` : ""
        }`
      );
    }
    if (evidence.length > 0) {
      evidencePoints.push(
        `${evidence.length} exhibit(s) [${evidence
          .map((e) => e.title)
          .slice(0, 2)
          .join(", ")}]`
      );
    }
    if (vehicles.length > 0) {
      evidencePoints.push(
        `${vehicles.length} vehicle(s) [${vehicles
          .map((v) => v.registration_number)
          .slice(0, 2)
          .join(", ")}]`
      );
    }
    const witnessCount = persons.filter(
      (p) => p.status === "WITNESS" || p.status === "VICTIM"
    ).length;
    if (witnessCount > 0) {
      evidencePoints.push(`${witnessCount} witness/victim statement(s)`);
    }
    if (locations.length > 0) {
      evidencePoints.push(`${locations.length} landmark sighting(s)`);
    }

    if (evidencePoints.length > 0) {
      return evidencePoints.join(" • ");
    }
    return "Pending physical or digital exhibit logging. Corroborate witness statements or upload documentary logs.";
  }, [totalAmount, transactions, calls, evidence, vehicles, persons, locations]);

  // Dynamic Authority Text
  const authorityText = useMemo(() => {
    return `Led by ${leadOfficer}, ${stationName} in coordination with Jurisdictional Special Investigation Unit.`;
  }, [leadOfficer, stationName]);

  const registeredDate = useMemo(() => {
    if (!summary?.created_at) return "Active Investigation";
    try {
      return new Date(summary.created_at).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return "Active Investigation";
    }
  }, [summary?.created_at]);

  const supervisingBody = useMemo(() => {
    if (!stationName) return "DCP Crime / ACP Division";
    const cleanZone = stationName
      .replace(/Police Station|PS|Commissionerate/gi, "")
      .trim();
    return `DCP Crime / ACP ${cleanZone || "Jurisdiction"}`;
  }, [stationName]);

  const kpis = [
    {
      id: "persons",
      label: "Suspects & Persons",
      value: persons.length,
      subtext: `${totalSuspects} Suspects • ${totalWitnesses} Witnesses`,
      icon: User,
      color: "var(--accent-cyan)",
      bgGlow: "rgba(0, 242, 254, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "calls",
      label: "CDR Intercepts",
      value: calls.length,
      subtext: calls.length > 0 ? "Tower Geo-Resolved" : "No Intercepts",
      icon: PhoneCall,
      color: "var(--accent-blue)",
      bgGlow: "rgba(56, 189, 248, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "finance",
      label: "Financial Flow",
      value: totalAmount > 0 ? `₹${(totalAmount / 100000).toFixed(2)}L` : "₹0",
      subtext: `${transactions.length} Traced Transfers`,
      icon: DollarSign,
      color: "var(--accent-amber)",
      bgGlow: "rgba(245, 158, 11, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "locations",
      label: "Crime Landmarks",
      value: locations.length,
      subtext:
        locations.length > 0
          ? `${locations.length} Spots Identified`
          : "No Locations",
      icon: MapPin,
      color: "#f97316",
      bgGlow: "rgba(249, 115, 22, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "vehicles",
      label: "Vehicles Seized",
      value: vehicles.length,
      subtext:
        vehicles.length > 0
          ? `${vehicles.length} Vehicles Tracked`
          : "No Vehicles",
      icon: Car,
      color: "var(--accent-emerald)",
      bgGlow: "rgba(160, 185, 129, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "orgs",
      label: "Shell Fronts",
      value: organizations.length,
      subtext:
        organizations.length > 0
          ? `${organizations.length} Entities Registered`
          : "No Entities",
      icon: Building2,
      color: "var(--accent-purple)",
      bgGlow: "rgba(168, 85, 247, 0.12)",
      tab: "investigation" as ActiveNavTab,
    },
    {
      id: "evidence",
      label: "Evidence Exhibits",
      value: evidence.length,
      subtext:
        evidence.length > 0 ? "Custody Chain Verified" : "No Exhibits",
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

  const caseTimeline = [
    ...evidence.map((e) => ({
      date: e.date_obtained || "Seized Date",
      time: "09:00",
      badge: "EVIDENCE EXHIBIT",
      color: "#38bdf8",
      title: e.title,
      desc: e.description,
    })),
    ...transactions.map((t) => ({
      date: t.date || "Txn Date",
      time: t.time || "12:00",
      badge: "FUND TRANSFER",
      color: "#f59e0b",
      title: `₹${t.amount.toLocaleString("en-IN")} via ${t.payment_type}`,
      desc: `Transfer from ${t.sender_name} to ${t.receiver_name} (${
        t.bank_name || "Bank"
      }).`,
    })),
    ...calls.map((c) => ({
      date: c.date || "Call Date",
      time: c.time || "12:00",
      badge: "CDR INTERCEPT",
      color: "#a855f7",
      title: `Call: ${c.caller_name || c.caller_number} → ${
        c.receiver_name || c.receiver_number
      }`,
      desc: `${c.duration_seconds}s call intercepted at ${
        c.cell_tower_id || "Cell Tower"
      }.`,
    })),
    ...locations.map((l) => ({
      date: l.date || "Visit Date",
      time: l.time || "12:00",
      badge: "LOCATION SIGHTING",
      color: "#00f2fe",
      title: `Sighting at ${l.name}`,
      desc: `${l.address || "Crime scene"} linked to ${(
        l.associated_persons || []
      ).join(", ")}.`,
    })),
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        width: "100%",
      }}
    >
      {/* 1. Master Case Briefing & Intelligence Synopsis (Dynamic to Uploaded Data) */}
      <div
        className="section-card"
        style={{
          background:
            "linear-gradient(135deg, rgba(14, 20, 34, 0.95), rgba(12, 16, 27, 0.98))",
          border: "1px solid rgba(0, 242, 254, 0.25)",
          padding: "1.1rem 1.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "0.75rem",
          borderRadius: "var(--radius-md)",
          boxShadow: "0 4px 24px -2px rgba(0, 0, 0, 0.5)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <div
              style={{
                background: "rgba(0, 242, 254, 0.15)",
                padding: "6px",
                borderRadius: "8px",
                border: "1px solid rgba(0, 242, 254, 0.3)",
              }}
            >
              <FileText size={18} style={{ color: "var(--accent-cyan)" }} />
            </div>
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  flexWrap: "wrap",
                }}
              >
                <span
                  className="case-id-badge"
                  style={{ fontSize: "0.75rem", padding: "0.15rem 0.5rem" }}
                >
                  {caseNumber}
                </span>
                <span
                  className="case-priority-badge"
                  style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem" }}
                >
                  {priorityText} • LEVEL 1
                </span>
                <span
                  style={{
                    fontSize: "0.725rem",
                    color: "var(--accent-emerald)",
                    fontWeight: 700,
                  }}
                >
                  ● ACTIVE INVESTIGATION
                </span>
              </div>
              <h2
                style={{
                  fontSize: "1.15rem",
                  fontWeight: 800,
                  color: "var(--text-primary)",
                  marginTop: "0.2rem",
                }}
              >
                {caseTitle}
              </h2>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              onClick={() => onNavigateTab("network")}
              className="btn-primary"
              style={{ padding: "0.45rem 0.85rem", fontSize: "0.775rem" }}
            >
              <Share2 size={13} /> Open Network Graph
            </button>
            <button
              onClick={onOpenAddData}
              className="btn-secondary"
              style={{ padding: "0.45rem 0.85rem", fontSize: "0.775rem" }}
            >
              <Plus size={13} /> Add Record
            </button>
          </div>
        </div>

        {/* Dynamic Narrative Box: What this specific case is about */}
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
            <strong style={{ color: "var(--text-primary)" }}>
              📌 Case Overview & Intelligence Brief:{" "}
            </strong>
            <span>{overviewText}</span>
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
              <span style={{ color: "var(--accent-cyan)", fontWeight: 700 }}>
                🎯 Primary Objective:{" "}
              </span>
              <span style={{ color: "var(--text-muted)" }}>
                {primaryObjectiveText}
              </span>
            </div>
            <div>
              <span style={{ color: "var(--accent-amber)", fontWeight: 700 }}>
                ⚡ Key Evidence:{" "}
              </span>
              <span style={{ color: "var(--text-muted)" }}>
                {keyEvidenceText}
              </span>
            </div>
            <div>
              <span style={{ color: "var(--accent-emerald)", fontWeight: 700 }}>
                🛡️ Authority & Station:{" "}
              </span>
              <span style={{ color: "var(--text-muted)" }}>
                {authorityText}
              </span>
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
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
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
                  color:
                    kpi.color === "var(--accent-amber)"
                      ? "var(--accent-amber)"
                      : "var(--text-primary)",
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

      {/* 3. Case Authority & Statutory Framework (Two Column Grid) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "0.85rem",
        }}
      >
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
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <div
                style={{
                  background: "rgba(0, 242, 254, 0.12)",
                  padding: "5px",
                  borderRadius: "6px",
                }}
              >
                <FolderLock size={15} style={{ color: "var(--accent-cyan)" }} />
              </div>
              <div>
                <h3
                  style={{
                    fontSize: "0.925rem",
                    fontWeight: 700,
                    color: "var(--text-primary)",
                  }}
                >
                  Case Investigation File • {caseNumber}
                </h3>
                <span
                  style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}
                >
                  {caseNumber} • {stationName}
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
              {priorityText} LEVEL 1
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
              <span
                style={{
                  color: "var(--text-muted)",
                  display: "block",
                  fontSize: "0.675rem",
                }}
              >
                LEAD INVESTIGATOR
              </span>
              <strong style={{ color: "var(--accent-cyan)" }}>
                {leadOfficer}
              </strong>
            </div>
            <div>
              <span
                style={{
                  color: "var(--text-muted)",
                  display: "block",
                  fontSize: "0.675rem",
                }}
              >
                SUPERVISING BODY
              </span>
              <strong style={{ color: "var(--text-primary)" }}>
                {supervisingBody}
              </strong>
            </div>
            <div>
              <span
                style={{
                  color: "var(--text-muted)",
                  display: "block",
                  fontSize: "0.675rem",
                }}
              >
                DATE REGISTERED
              </span>
              <strong style={{ color: "var(--text-primary)" }}>
                {registeredDate}
              </strong>
            </div>
            <div>
              <span
                style={{
                  color: "var(--text-muted)",
                  display: "block",
                  fontSize: "0.675rem",
                }}
              >
                CLASSIFICATION
              </span>
              <strong style={{ color: "var(--accent-amber)" }}>
                {caseClassification}
              </strong>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              onClick={() => onNavigateTab("network")}
              className="btn-primary"
              style={{
                padding: "0.4rem 0.8rem",
                fontSize: "0.775rem",
                flex: 1,
                justifyContent: "center",
              }}
            >
              <Share2 size={13} /> View Live Network Graph
            </button>
            <button
              onClick={onOpenAddData}
              className="btn-secondary"
              style={{
                padding: "0.4rem 0.8rem",
                fontSize: "0.775rem",
                flex: 1,
                justifyContent: "center",
              }}
            >
              <Plus size={13} /> Add Investigation Record
            </button>
          </div>
        </div>

        {/* Statutory Legal Provisions (Dynamic to Case) */}
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
            <div
              style={{
                background: "rgba(168, 85, 247, 0.12)",
                padding: "5px",
                borderRadius: "6px",
              }}
            >
              <Scale size={15} style={{ color: "var(--accent-purple)" }} />
            </div>
            <div>
              <h3
                style={{
                  fontSize: "0.925rem",
                  fontWeight: 700,
                  color: "var(--text-primary)",
                }}
              >
                Statutory Penal Codes & Acts Invoked
              </h3>
              <span
                style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}
              >
                Active legal grounds in {caseNumber}
              </span>
            </div>
          </div>

          <div
            style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}
          >
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
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontWeight: 700,
                      color: "var(--accent-cyan)",
                    }}
                  >
                    {sec.code}
                  </span>
                  <span
                    style={{ color: "var(--text-primary)", fontWeight: 500 }}
                  >
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

      {/* 4. Suspects & Persons Roster Cards */}
      <div
        className="section-card"
        style={{
          background: "rgba(14, 20, 34, 0.8)",
          border: "1px solid var(--border-color)",
          padding: "1rem 1.15rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "0.65rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <div
              style={{
                background: "rgba(0, 242, 254, 0.12)",
                padding: "5px",
                borderRadius: "6px",
              }}
            >
              <Users size={15} style={{ color: "var(--accent-cyan)" }} />
            </div>
            <div>
              <h3
                style={{
                  fontSize: "0.925rem",
                  fontWeight: 700,
                  color: "var(--text-primary)",
                }}
              >
                Suspects, Associates & Eyewitnesses Roster ({persons.length})
              </h3>
              <span
                style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}
              >
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

        {persons.length === 0 ? (
          <div
            style={{
              padding: "1.5rem",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: "0.825rem",
              background: "rgba(255, 255, 255, 0.01)",
              borderRadius: "var(--radius-sm)",
              border: "1px dashed var(--border-color)",
            }}
          >
            No persons or suspects added yet. Use &ldquo;Add Record&rdquo; or Ingest
            a document docket to populate this roster.
          </div>
        ) : (
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
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <h4
                        style={{
                          fontSize: "0.875rem",
                          fontWeight: 700,
                          color: "var(--text-primary)",
                        }}
                      >
                        {p.name}
                      </h4>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        {p.occupation || "Person of Record"}
                      </span>
                    </div>
                    <span
                      className="mini-tag"
                      style={{
                        background: isSuspect
                          ? "rgba(244, 63, 94, 0.15)"
                          : isWitness
                          ? "rgba(0, 242, 254, 0.15)"
                          : "rgba(168, 85, 247, 0.15)",
                        color: isSuspect
                          ? "#fb7185"
                          : isWitness
                          ? "#38bdf8"
                          : "#c084fc",
                        fontWeight: 700,
                        fontSize: "0.675rem",
                      }}
                    >
                      {p.status}
                    </span>
                  </div>

                  {p.phone_numbers && p.phone_numbers.length > 0 && (
                    <div
                      style={{
                        fontSize: "0.725rem",
                        color: "var(--text-secondary)",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.3rem",
                      }}
                    >
                      <PhoneCall
                        size={11}
                        style={{ color: "var(--text-muted)" }}
                      />
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
                      <span
                        style={{
                          color: "var(--accent-cyan)",
                          fontWeight: 600,
                        }}
                      >
                        🔗 Link to {p.connected_person_name}:{" "}
                      </span>
                      <span
                        style={{
                          color: "var(--text-secondary)",
                          fontStyle: "italic",
                        }}
                      >
                        {p.connection_notes ||
                          p.connection_type ||
                          "Linked entity"}
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
                    <span style={{ color: "var(--text-muted)" }}>
                      {p.source || "Dossier Record"}
                    </span>
                    <span
                      style={{
                        color:
                          p.verification_status === "VERIFIED"
                            ? "var(--accent-emerald)"
                            : "var(--accent-amber)",
                      }}
                    >
                      ✓ {p.verification_status} (
                      {Math.round((p.confidence_score || 0.9) * 100)}%)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 5. Investigation Timeline */}
      <div
        className="section-card"
        style={{
          background: "rgba(14, 20, 34, 0.8)",
          border: "1px solid var(--border-color)",
          padding: "1rem 1.15rem",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "0.75rem",
          }}
        >
          <div
            style={{
              background: "rgba(0, 242, 254, 0.12)",
              padding: "5px",
              borderRadius: "6px",
            }}
          >
            <Clock size={15} style={{ color: "var(--accent-cyan)" }} />
          </div>
          <div>
            <h3
              style={{
                fontSize: "0.925rem",
                fontWeight: 700,
                color: "var(--text-primary)",
              }}
            >
              Investigation Chronology & Major Breakthroughs
            </h3>
            <span style={{ fontSize: "0.725rem", color: "var(--text-muted)" }}>
              Sequential chain of surveillance, seizures, statements, and
              intelligence synthesis
            </span>
          </div>
        </div>

        {caseTimeline.length === 0 ? (
          <div
            style={{
              padding: "1.25rem",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: "0.8rem",
              background: "rgba(255, 255, 255, 0.01)",
              borderRadius: "var(--radius-sm)",
              border: "1px dashed var(--border-color)",
            }}
          >
            Case docket registered under {caseNumber}. Exhibits, CDR intercepts,
            financial movements, and sightings will automatically sequence here as
            corroborated.
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.75rem",
              position: "relative",
              paddingLeft: "1.25rem",
            }}
          >
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
              <div
                key={idx}
                style={{
                  position: "relative",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.15rem",
                }}
              >
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

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.4rem",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: "var(--text-primary)",
                    }}
                  >
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

                <h4
                  style={{
                    fontSize: "0.85rem",
                    fontWeight: 700,
                    color: "var(--text-primary)",
                  }}
                >
                  {item.title}
                </h4>
                <p
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.35,
                  }}
                >
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

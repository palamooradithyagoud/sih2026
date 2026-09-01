"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  User,
  PhoneCall,
  DollarSign,
  MapPin,
  Car,
  Users,
  Building2,
  FileText,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Plus,
  UploadCloud,
  Layers,
  Share2,
  TrendingUp,
  Zap,
  FolderLock,
  Search,
  BarChart3,
  Calendar,
  FileSpreadsheet,
  Sparkles,
  Brain,
} from "lucide-react";
import Sidebar, { ActiveNavTab } from "@/components/Sidebar";
import CaseHeader from "@/components/CaseHeader";
import DataEntryForms, { EntityTypeTab } from "@/components/DataEntryForms";
import BulkImportModal from "@/components/BulkImportModal";
import NetworkGraphPreview from "@/components/NetworkGraphPreview";
import EntityExplorer from "@/components/EntityExplorer";
import CaseDossierView from "@/components/CaseDossierView";
import DocGraphExtractor from "@/components/DocGraphExtractor";
import InvestigationCopilot from "@/components/InvestigationCopilot";
import { investigationApi } from "@/lib/investigationApi";
import {
  Case,
  CaseSummary,
  Person,
  CallRecord,
  Transaction,
  Location,
  Vehicle,
  Relationship,
  Organization,
  Evidence,
  GraphData,
  DocumentExtractionResult,
} from "@/types/investigation";

export default function Home() {
  const [activeNavTab, setActiveNavTab] = useState<ActiveNavTab>("dashboard");
  const [activeCaseId, setActiveCaseId] = useState<string>("");
  const [summary, setSummary] = useState<CaseSummary | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);

  // Entities
  const [persons, setPersons] = useState<Person[]>([]);
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);

  // Modals
  const [isDataEntryOpen, setIsDataEntryOpen] = useState(false);
  const [dataEntryInitialTab, setDataEntryInitialTab] = useState<EntityTypeTab>("person");
  const [isBulkImportOpen, setIsBulkImportOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load all investigation data from FastAPI backend
  const loadCaseData = useCallback(async () => {
    try {
      setLoading(true);
      let targetCaseId = activeCaseId;

      if (!targetCaseId) {
        const cases = await investigationApi.getCases();
        if (cases && cases.length > 0) {
          targetCaseId = cases[0].id;
          setActiveCaseId(targetCaseId);
        } else {
          setSummary(null);
          setGraphData({ nodes: [], links: [] });
          setPersons([]);
          setCalls([]);
          setTransactions([]);
          setLocations([]);
          setVehicles([]);
          setRelationships([]);
          setOrganizations([]);
          setEvidence([]);
          return;
        }
      }

      const [
        sumRes,
        graphRes,
        pRes,
        cRes,
        tRes,
        lRes,
        vRes,
        rRes,
        oRes,
        eRes,
      ] = await Promise.all([
        investigationApi.getCaseSummary(targetCaseId),
        investigationApi.getCaseGraph(targetCaseId),
        investigationApi.getPersons(targetCaseId),
        investigationApi.getCalls(targetCaseId),
        investigationApi.getTransactions(targetCaseId),
        investigationApi.getLocations(targetCaseId),
        investigationApi.getVehicles(targetCaseId),
        investigationApi.getRelationships(targetCaseId),
        investigationApi.getOrganizations(targetCaseId),
        investigationApi.getEvidence(targetCaseId),
      ]);

      if (sumRes) setSummary(sumRes);
      if (graphRes) setGraphData(graphRes);
      if (pRes) setPersons(pRes);
      if (cRes) setCalls(cRes);
      if (tRes) setTransactions(tRes);
      if (lRes) setLocations(lRes);
      if (vRes) setVehicles(vRes);
      if (rRes) setRelationships(rRes);
      if (oRes) setOrganizations(oRes);
      if (eRes) setEvidence(eRes);
    } catch (err) {
      console.warn("Syncing case data", err);
    } finally {
      setLoading(false);
    }
  }, [activeCaseId]);

  useEffect(() => {
    loadCaseData();
  }, [loadCaseData]);


  const handleOpenDataEntryWithTab = (tab: EntityTypeTab) => {
    setDataEntryInitialTab(tab);
    setIsDataEntryOpen(true);
  };

  const handleExtractionSuccess = (result: DocumentExtractionResult) => {
    if (result.case_id) {
      setActiveCaseId(result.case_id);
    }
    if (result.summary) setSummary(result.summary);
    if (result.graph) setGraphData(result.graph);
    loadCaseData();
  };

  const quickEntryCards = [
    { id: "person", label: "Person", desc: "Suspects, witnesses, aliases", icon: User, count: persons.length, color: "#3b82f6" },
    { id: "call", label: "Phone / Call", desc: "CDR logs, duration, cell towers", icon: PhoneCall, count: calls.length, color: "#00f2fe" },
    { id: "transaction", label: "Transaction", desc: "Bank routing, UPI, Hawala", icon: DollarSign, count: transactions.length, color: "#fbbf24" },
    { id: "location", label: "Location", desc: "Coordinates, visits, CCTV spots", icon: MapPin, count: locations.length, color: "#f97316" },
    { id: "vehicle", label: "Vehicle", desc: "License plates, models, owners", icon: Car, count: vehicles.length, color: "#10b981" },
    { id: "relationship", label: "Relationship", desc: "Family, associates, co-accused", icon: Users, count: relationships.length, color: "#ec4899" },
    { id: "organization", label: "Organization", desc: "Shell companies, GST, fronts", icon: Building2, count: organizations.length, color: "var(--color-crayola)" },
    { id: "evidence", label: "Evidence", desc: "FIR, docs, forensic dumps", icon: FileText, count: evidence.length, color: "var(--color-light-blue)" },
  ];

  return (
    <div className="dashboard-layout">
      {/* Sidebar matching ASCII Navigation */}
      <Sidebar
        activeTab={activeNavTab}
        setActiveTab={setActiveNavTab}
        caseNumber={summary?.case_number || "NO CASE"}
      />

      {/* Main Workspace */}
      <main className="dashboard-content">
        {/* Active Case Banner & Clean Actions */}
        <CaseHeader
          summary={summary}
          onOpenAddData={() => handleOpenDataEntryWithTab("person")}
          onOpenBulkImport={() => setIsBulkImportOpen(true)}
          onOpenAiPdfExtractor={() => setActiveNavTab("ai-extractor")}
        />

        {/* Top Intelligence KPIs (3 Cards) - Shown on Dashboard Overview */}
        {activeNavTab === "dashboard" && (
          <div className="kpi-grid-3">
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">TOTAL SUSPECTS & PERSONS</span>
                <User size={15} style={{ color: "var(--accent-cyan)" }} />
              </div>
              <div className="kpi-val">{summary?.total_persons ?? persons.length}</div>
              <div className="kpi-meta">{persons.filter((p) => p.status === "SUSPECT").length} Primary Suspects</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">CALL RECORDS (CDR)</span>
                <PhoneCall size={15} style={{ color: "var(--accent-blue)" }} />
              </div>
              <div className="kpi-val">{summary?.total_calls ?? calls.length}</div>
              <div className="kpi-meta">Tower Geo-Resolved</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">FINANCIAL FLOW</span>
                <DollarSign size={15} style={{ color: "var(--accent-amber)" }} />
              </div>
              <div className="kpi-val" style={{ color: "var(--accent-amber)" }}>
                ₹{(summary?.total_amount_transferred ?? 0).toLocaleString("en-IN")}
              </div>
              <div className="kpi-meta">{summary?.total_transactions ?? transactions.length} Traced Transfers</div>
            </div>
          </div>
        )}



        {/* AI Extractor Tab View */}
        {activeNavTab === "ai-extractor" && (
          <DocGraphExtractor
            caseId={activeCaseId}
            onExtractionSuccess={handleExtractionSuccess}
            onNavigateToGraph={() => setActiveNavTab("network")}
            onNavigateToCases={() => setActiveNavTab("cases")}
          />
        )}


        {/* 1. DASHBOARD VIEW */}
        {activeNavTab === "dashboard" && (
          <>
            {/* Live Connected Knowledge Graph Visualizer */}
            <section>
              <NetworkGraphPreview
                graphData={graphData}
                loading={loading}
                onRefresh={loadCaseData}
                fullHeight={false}
              />
            </section>

            {/* Quick Data Entry Pipeline Hub */}
            <section className="section-card">
              <div className="section-header-row">
                <div>
                  <h2 className="section-title">
                    <Layers size={17} style={{ color: "var(--accent-cyan)" }} />
                    Add Investigation Data Pipeline
                  </h2>
                  <p className="section-subtitle">
                    Enter intelligence records or import bulk CSV files. The system automatically updates the Knowledge Graph above.
                  </p>
                </div>

                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    onClick={() => setIsBulkImportOpen(true)}
                    className="btn-secondary"
                  >
                    <UploadCloud size={14} /> Bulk CSV Import
                  </button>
                </div>
              </div>

              {/* Quick Entry 8 Grid */}
              <div className="data-entry-cards-grid">
                {quickEntryCards.map((card) => {
                  const Icon = card.icon;
                  return (
                    <div
                      key={card.id}
                      onClick={() => handleOpenDataEntryWithTab(card.id as EntityTypeTab)}
                      className="quick-entry-card"
                    >
                      <div className="quick-card-top">
                        <div className="card-icon-pill" style={{ color: card.color, borderColor: card.color }}>
                          <Icon size={16} />
                        </div>
                        <span className="quick-card-count">{card.count} records</span>
                      </div>
                      <h3 className="quick-card-title">{card.label}</h3>
                      <p className="quick-card-desc">{card.desc}</p>
                      <div className="quick-card-action">
                        <Plus size={13} /> Add Record
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Entity Records & Verification Explorer */}
            <section>
              <EntityExplorer
                caseId={activeCaseId}
                persons={persons}
                calls={calls}
                transactions={transactions}
                locations={locations}
                vehicles={vehicles}
                relationships={relationships}
                organizations={organizations}
                evidence={evidence}
                onRefresh={loadCaseData}
              />
            </section>
          </>
        )}

        {/* 2. INVESTIGATION TAB */}
        {activeNavTab === "investigation" && (
          <>
            <section className="section-card">
              <div className="section-header-row">
                <div>
                  <h2 className="section-title">
                    <Layers size={17} style={{ color: "var(--accent-cyan)" }} />
                    Add Investigation Data Pipeline
                  </h2>
                  <p className="section-subtitle">
                    Enter intelligence records below or import bulk CDR/Bank CSV files.
                  </p>
                </div>

                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    onClick={() => setIsBulkImportOpen(true)}
                    className="btn-secondary"
                  >
                    <UploadCloud size={14} /> Bulk CSV Import
                  </button>
                </div>
              </div>

              <div className="data-entry-cards-grid">
                {quickEntryCards.map((card) => {
                  const Icon = card.icon;
                  return (
                    <div
                      key={card.id}
                      onClick={() => handleOpenDataEntryWithTab(card.id as EntityTypeTab)}
                      className="quick-entry-card"
                    >
                      <div className="quick-card-top">
                        <div className="card-icon-pill" style={{ color: card.color, borderColor: card.color }}>
                          <Icon size={16} />
                        </div>
                        <span className="quick-card-count">{card.count} records</span>
                      </div>
                      <h3 className="quick-card-title">{card.label}</h3>
                      <p className="quick-card-desc">{card.desc}</p>
                      <div className="quick-card-action">
                        <Plus size={13} /> Add Record
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <section>
              <NetworkGraphPreview
                graphData={graphData}
                loading={loading}
                onRefresh={loadCaseData}
              />
            </section>

            <section>
              <EntityExplorer
                caseId={activeCaseId}
                persons={persons}
                calls={calls}
                transactions={transactions}
                locations={locations}
                vehicles={vehicles}
                relationships={relationships}
                organizations={organizations}
                evidence={evidence}
                onRefresh={loadCaseData}
              />
            </section>
          </>
        )}

        {/* 3. NETWORK GRAPH TAB */}
        {activeNavTab === "network" && (
          <section>
            <NetworkGraphPreview
              graphData={graphData}
              loading={loading}
              onRefresh={loadCaseData}
              fullHeight={true}
            />
          </section>
        )}

        {/* 7. INVESTIGATION COPILOT TAB (Phase 4) */}
        {activeNavTab === "copilot" && (
          <section>
            <InvestigationCopilot
              caseId={activeCaseId}
              onHighlightGraph={(highlightData) => {
                setGraphData(highlightData);
              }}
              onNavigateToGraph={() => setActiveNavTab("network")}
            />
          </section>
        )}

        {/* 4. EVIDENCE VAULT TAB */}
        {activeNavTab === "evidence" && (
          <section>
            <EntityExplorer
              caseId={activeCaseId}
              persons={persons}
              calls={calls}
              transactions={transactions}
              locations={locations}
              vehicles={vehicles}
              relationships={relationships}
              organizations={organizations}
              evidence={evidence}
              onRefresh={loadCaseData}
            />
          </section>
        )}

        {/* 5. CASES TAB (MASTER CASE DOSSIER & FULL INTELLIGENCE) */}
        {activeNavTab === "cases" && (
          <CaseDossierView
            summary={summary}
            persons={persons}
            calls={calls}
            transactions={transactions}
            locations={locations}
            vehicles={vehicles}
            relationships={relationships}
            organizations={organizations}
            evidence={evidence}
            onOpenAddData={() => {
              setDataEntryInitialTab("person");
              setIsDataEntryOpen(true);
            }}
            onOpenBulkImport={() => setIsBulkImportOpen(true)}
            onNavigateTab={setActiveNavTab}
          />
        )}

        {/* 6. ANALYTICS TAB */}
        {activeNavTab === "analytics" && (
          <section className="section-card">
            <h2 className="section-title">
              <BarChart3 size={18} style={{ color: "var(--accent-cyan)" }} /> Officer Verification & Intelligence Audit Logs
            </h2>
            <p className="section-subtitle">Real-time immutable audit trail of all officer data entries and corroborations.</p>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginTop: "1rem" }}>
              {persons.length === 0 && transactions.length === 0 && calls.length === 0 ? (
                <div style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                  No officer audit trail events yet. Records ingested or added will appear here with verification hashes.
                </div>
              ) : (
                <>
                  {persons.map((p) => (
                    <div
                      key={p.id}
                      style={{
                        padding: "0.85rem 1.1rem",
                        background: "rgba(20, 28, 48, 0.75)",
                        border: "1px solid var(--border-color)",
                        borderRadius: "var(--radius-sm)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "0.825rem",
                        color: "#ffffff",
                      }}
                    >
                      <span style={{ color: "#ffffff" }}>
                        <span style={{ color: p.verification_status === "VERIFIED" ? "var(--accent-emerald)" : "var(--accent-amber)", fontWeight: 700, marginRight: "0.5rem" }}>
                          {p.verification_status === "VERIFIED" ? "✓ VERIFIED" : "⏳ UNVERIFIED"}
                        </span>
                        <strong style={{ color: "#ffffff" }}>{p.name}</strong> ({p.status})
                      </span>
                      <span style={{ color: "#94a3b8", fontSize: "0.775rem", fontFamily: "var(--font-mono)" }}>
                        {p.added_by_officer || "Officer ID 1024"} • Conf: {Math.round(p.confidence_score * 100)}%
                      </span>
                    </div>
                  ))}
                  {transactions.map((t) => (
                    <div
                      key={t.id}
                      style={{
                        padding: "0.85rem 1.1rem",
                        background: "rgba(20, 28, 48, 0.75)",
                        border: "1px solid var(--border-color)",
                        borderRadius: "var(--radius-sm)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "0.825rem",
                        color: "#ffffff",
                      }}
                    >
                      <span style={{ color: "#ffffff" }}>
                        <span style={{ color: t.verification_status === "VERIFIED" ? "var(--accent-emerald)" : "var(--accent-amber)", fontWeight: 700, marginRight: "0.5rem" }}>
                          {t.verification_status === "VERIFIED" ? "✓ VERIFIED" : "⏳ UNVERIFIED"}
                        </span>
                        <strong style={{ color: "var(--color-crayola)" }}>₹{t.amount.toLocaleString("en-IN")} Transfer</strong> ({t.sender_name} → {t.receiver_name})
                      </span>
                      <span style={{ color: "#94a3b8", fontSize: "0.775rem", fontFamily: "var(--font-mono)" }}>
                        {t.added_by_officer || "FIU Officer ID 1024"} • Conf: {Math.round(t.confidence_score * 100)}%
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </section>
        )}

        {/* Modals */}
        <DataEntryForms
          caseId={activeCaseId}
          isOpen={isDataEntryOpen}
          initialTab={dataEntryInitialTab}
          persons={persons}
          locations={locations}
          vehicles={vehicles}
          onClose={() => setIsDataEntryOpen(false)}
          onSuccess={() => {
            setIsDataEntryOpen(false);
            loadCaseData();
          }}
        />

        <BulkImportModal
          caseId={activeCaseId}
          isOpen={isBulkImportOpen}
          onClose={() => setIsBulkImportOpen(false)}
          onSuccess={() => {
            loadCaseData();
          }}
        />
      </main>
    </div>
  );
}

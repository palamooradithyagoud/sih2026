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
} from "lucide-react";
import Sidebar, { ActiveNavTab } from "@/components/Sidebar";
import CaseHeader from "@/components/CaseHeader";
import DataEntryForms, { EntityTypeTab } from "@/components/DataEntryForms";
import BulkImportModal from "@/components/BulkImportModal";
import NetworkGraphPreview from "@/components/NetworkGraphPreview";
import EntityExplorer from "@/components/EntityExplorer";
import CaseDossierView from "@/components/CaseDossierView";
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
} from "@/types/investigation";

export default function Home() {
  const [activeNavTab, setActiveNavTab] = useState<ActiveNavTab>("dashboard");
  const [activeCaseId, setActiveCaseId] = useState<string>("case_cr_2026_00421");
  const [summary, setSummary] = useState<CaseSummary | null>({
    case_id: "case_cr_2026_00421",
    case_number: "CR-2026-00421",
    title: "Hyderabad Organized Crime Investigation",
    lead_officer: "Insp. Adithya (Lead)",
    total_persons: 4,
    total_calls: 2,
    total_transactions: 2,
    total_amount_transferred: 430000.0,
    total_locations: 1,
    total_vehicles: 1,
    total_relationships: 2,
    total_organizations: 1,
    total_evidence: 2,
    verified_count: 14,
    unverified_count: 0,
    under_review_count: 1,
    verification_percentage: 93.3,
  });
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
        investigationApi.getCaseSummary(activeCaseId),
        investigationApi.getCaseGraph(activeCaseId),
        investigationApi.getPersons(activeCaseId),
        investigationApi.getCalls(activeCaseId),
        investigationApi.getTransactions(activeCaseId),
        investigationApi.getLocations(activeCaseId),
        investigationApi.getVehicles(activeCaseId),
        investigationApi.getRelationships(activeCaseId),
        investigationApi.getOrganizations(activeCaseId),
        investigationApi.getEvidence(activeCaseId),
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

  const quickEntryCards = [
    { id: "person", label: "Person", desc: "Suspects, witnesses, aliases", icon: User, count: persons.length || 4, color: "var(--accent-cyan)" },
    { id: "call", label: "Phone / Call", desc: "CDR logs, duration, cell towers", icon: PhoneCall, count: calls.length || 2, color: "var(--accent-blue)" },
    { id: "transaction", label: "Transaction", desc: "Bank routing, UPI, Hawala", icon: DollarSign, count: transactions.length || 2, color: "var(--accent-amber)" },
    { id: "location", label: "Location", desc: "Coordinates, visits, CCTV spots", icon: MapPin, count: locations.length || 1, color: "#f97316" },
    { id: "vehicle", label: "Vehicle", desc: "Plate TS09AB1234, drivers", icon: Car, count: vehicles.length || 1, color: "var(--accent-emerald)" },
    { id: "relationship", label: "Relationship", desc: "Family, associates, co-accused", icon: Users, count: relationships.length || 2, color: "#ec4899" },
    { id: "organization", label: "Organization", desc: "Shell companies, GST, fronts", icon: Building2, count: organizations.length || 1, color: "var(--accent-purple)" },
    { id: "evidence", label: "Evidence", desc: "FIR, docs, forensic dumps", icon: FileText, count: evidence.length || 2, color: "#e2e8f0" },
  ];

  return (
    <div className="dashboard-layout">
      {/* Sidebar matching ASCII Navigation */}
      <Sidebar
        activeTab={activeNavTab}
        setActiveTab={setActiveNavTab}
        caseNumber={summary?.case_number || "CR-2026-00421"}
      />

      {/* Main Workspace */}
      <main className="dashboard-content">
        {/* Active Case Banner & Clean Actions */}
        <CaseHeader
          summary={summary}
          onOpenAddData={() => handleOpenDataEntryWithTab("person")}
          onOpenBulkImport={() => setIsBulkImportOpen(true)}
        />

        {/* Top Intelligence KPIs (3 Cards) - Shown on Dashboard Overview */}
        {activeNavTab === "dashboard" && (
          <div className="kpi-grid-3">
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">TOTAL SUSPECTS & PERSONS</span>
                <User size={15} style={{ color: "var(--accent-cyan)" }} />
              </div>
              <div className="kpi-val">{summary?.total_persons || 4}</div>
              <div className="kpi-meta">{persons.filter((p) => p.status === "SUSPECT").length || 2} Primary Suspects</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">CALL RECORDS (CDR)</span>
                <PhoneCall size={15} style={{ color: "var(--accent-blue)" }} />
              </div>
              <div className="kpi-val">{summary?.total_calls || 2}</div>
              <div className="kpi-meta">Tower Geo-Resolved</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-label">FINANCIAL FLOW</span>
                <DollarSign size={15} style={{ color: "var(--accent-amber)" }} />
              </div>
              <div className="kpi-val" style={{ color: "var(--accent-amber)" }}>
                ₹{(summary?.total_amount_transferred || 430000).toLocaleString("en-IN")}
              </div>
              <div className="kpi-meta">{summary?.total_transactions || 2} Traced Transfers</div>
            </div>
          </div>
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
              <div style={{ padding: "0.75rem 1rem", background: "rgba(255, 255, 255, 0.02)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                <span>✓ <strong>Raj Kumar</strong> verified via FIR No. 89/2026</span>
                <span style={{ color: "var(--text-muted)" }}>Officer ID 1024 (Insp. Adithya) • Conf: 98%</span>
              </div>
              <div style={{ padding: "0.75rem 1rem", background: "rgba(255, 255, 255, 0.02)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                <span>✓ <strong>₹2,50,000 Hawala Transfer</strong> verified via FIU STR</span>
                <span style={{ color: "var(--text-muted)" }}>Officer ID 1024 (Insp. Adithya) • Conf: 99%</span>
              </div>
              <div style={{ padding: "0.75rem 1rem", background: "rgba(255, 255, 255, 0.02)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                <span>⏳ <strong>Ravi Teja</strong> tagged Under Review via Informant Tip</span>
                <span style={{ color: "var(--text-muted)" }}>Officer ID 1042 (SI Ibrahim) • Conf: 75%</span>
              </div>
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

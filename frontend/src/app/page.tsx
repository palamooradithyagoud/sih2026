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
  ShieldCheck,
  Zap,
} from "lucide-react";
import Sidebar, { ActiveNavTab } from "@/components/Sidebar";
import CaseHeader from "@/components/CaseHeader";
import DataEntryForms, { EntityTypeTab } from "@/components/DataEntryForms";
import BulkImportModal from "@/components/BulkImportModal";
import NetworkGraphPreview from "@/components/NetworkGraphPreview";
import EntityExplorer from "@/components/EntityExplorer";
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
  const [activeNavTab, setActiveNavTab] = useState<ActiveNavTab>("investigation");
  const [activeCaseId, setActiveCaseId] = useState<string>("case_cr_2026_00421");
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
  const [loading, setLoading] = useState(true);

  // Load all investigation data
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

      setSummary(sumRes);
      setGraphData(graphRes);
      setPersons(pRes);
      setCalls(cRes);
      setTransactions(tRes);
      setLocations(lRes);
      setVehicles(vRes);
      setRelationships(rRes);
      setOrganizations(oRes);
      setEvidence(eRes);
    } catch (err) {
      console.error("Failed to fetch investigation case data", err);
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
    { id: "person", label: "Person", desc: "Suspects, witnesses, aliases", icon: User, count: persons.length, color: "var(--accent-cyan)" },
    { id: "call", label: "Phone / Call", desc: "CDR logs, duration, cell towers", icon: PhoneCall, count: calls.length, color: "var(--accent-blue)" },
    { id: "transaction", label: "Transaction", desc: "Bank routing, UPI, Hawala", icon: DollarSign, count: transactions.length, color: "var(--accent-amber)" },
    { id: "location", label: "Location", desc: "Coordinates, visits, CCTV spots", icon: MapPin, count: locations.length, color: "#f97316" },
    { id: "vehicle", label: "Vehicle", desc: "Plate TS09AB1234, drivers", icon: Car, count: vehicles.length, color: "var(--accent-emerald)" },
    { id: "relationship", label: "Relationship", desc: "Family, associates, co-accused", icon: Users, count: relationships.length, color: "#ec4899" },
    { id: "organization", label: "Organization", desc: "Shell companies, GST, fronts", icon: Building2, count: organizations.length, color: "var(--accent-purple)" },
    { id: "evidence", label: "Evidence", desc: "FIR, docs, forensic dumps", icon: FileText, count: evidence.length, color: "#e2e8f0" },
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
        {/* Active Case Banner & Integrity Tracker */}
        <CaseHeader
          summary={summary}
          onOpenAddData={() => handleOpenDataEntryWithTab("person")}
          onOpenBulkImport={() => setIsBulkImportOpen(true)}
        />

        {/* Top Intelligence KPIs */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-header">
              <span className="kpi-label">TOTAL SUSPECTS & PERSONS</span>
              <User size={16} style={{ color: "var(--accent-cyan)" }} />
            </div>
            <div className="kpi-val">{summary?.total_persons || 0}</div>
            <div className="kpi-meta">{persons.filter((p) => p.status === "SUSPECT").length} Primary Suspects</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-header">
              <span className="kpi-label">CALL RECORDS (CDR)</span>
              <PhoneCall size={16} style={{ color: "var(--accent-blue)" }} />
            </div>
            <div className="kpi-val">{summary?.total_calls || 0}</div>
            <div className="kpi-meta">Tower Geo-Resolved</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-header">
              <span className="kpi-label">FINANCIAL FLOW</span>
              <DollarSign size={16} style={{ color: "var(--accent-amber)" }} />
            </div>
            <div className="kpi-val" style={{ color: "var(--accent-amber)" }}>
              ₹{(summary?.total_amount_transferred || 0).toLocaleString("en-IN")}
            </div>
            <div className="kpi-meta">{summary?.total_transactions || 0} Traced Transfers</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-header">
              <span className="kpi-label">OFFICER VERIFIED INTEL</span>
              <ShieldCheck size={16} style={{ color: "var(--accent-emerald)" }} />
            </div>
            <div className="kpi-val" style={{ color: "var(--accent-emerald)" }}>
              {summary?.verification_percentage || 0}%
            </div>
            <div className="kpi-meta">{summary?.verified_count || 0} Corroborated Nodes</div>
          </div>
        </div>

        {/* Section 1: Data Entry Hub */}
        <section className="section-card">
          <div className="section-header-row">
            <div>
              <h2 className="section-title">
                <Layers size={18} style={{ color: "var(--accent-cyan)" }} />
                Add Investigation Data Pipeline
              </h2>
              <p className="section-subtitle">
                Enter intelligence records below or import bulk CDR/Bank CSV files. The system automatically connects data into the knowledge graph.
              </p>
            </div>

            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                onClick={() => setIsBulkImportOpen(true)}
                className="btn-secondary"
                style={{ fontSize: "0.85rem" }}
              >
                <UploadCloud size={15} /> Bulk CSV Import
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
                      <Icon size={18} />
                    </div>
                    <span className="quick-card-count">{card.count} records</span>
                  </div>
                  <h3 className="quick-card-title">{card.label}</h3>
                  <p className="quick-card-desc">{card.desc}</p>
                  <div className="quick-card-action">
                    <Plus size={14} /> Add Record
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Section 2: Live Connected Knowledge Graph Visualizer */}
        <section style={{ marginTop: "1rem" }}>
          <NetworkGraphPreview
            graphData={graphData}
            loading={loading}
            onRefresh={loadCaseData}
          />
        </section>

        {/* Section 3: Entity Records & Verification Explorer */}
        <section style={{ marginTop: "1rem" }}>
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

        {/* Modals */}
        <DataEntryForms
          caseId={activeCaseId}
          isOpen={isDataEntryOpen}
          initialTab={dataEntryInitialTab}
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

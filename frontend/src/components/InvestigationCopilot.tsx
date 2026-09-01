"use client";

import React, { useState, useRef, useCallback } from "react";
import {
  Bot,
  Send,
  Sparkles,
  Shield,
  ShieldCheck,
  AlertTriangle,
  ChevronRight,
  ArrowRight,
  Network,
  Code2,
  User,
  PhoneCall,
  DollarSign,
  MapPin,
  Car,
  Building2,
  Layers,
  Clock,
  Loader2,
  X,
  Info,
  CheckCircle2,
  Eye,
} from "lucide-react";
import { investigationApi } from "@/lib/investigationApi";
import {
  CopilotQueryResponse,
  ConnectionPathStep,
  GraphData,
} from "@/types/investigation";

// ─────────────────────────────────────────────────────────────────────────────
// Types & Constants
// ─────────────────────────────────────────────────────────────────────────────

interface InvestigationCopilotProps {
  caseId: string;
  onHighlightGraph?: (graphData: GraphData) => void;
  onNavigateToGraph?: () => void;
}

interface QueryHistoryItem {
  id: string;
  question: string;
  response: CopilotQueryResponse;
  timestamp: string;
}

const EXAMPLE_QUESTIONS = [
  { label: "Phone call network", question: "Who is connected to Raj Kumar through phone calls?", icon: PhoneCall },
  { label: "Financial flow", question: "Show all financial transactions and money flow in this case", icon: DollarSign },
  { label: "Find associates", question: "Who are the associates and co-conspirators in this case?", icon: User },
  { label: "Location connections", question: "Which locations were visited by suspects in this case?", icon: MapPin },
  { label: "Shortest path", question: "What is the shortest connection path between Raj Kumar and Ahmed Khan?", icon: Network },
  { label: "Vehicle links", question: "Which vehicles are linked to persons in this case?", icon: Car },
  { label: "Org connections", question: "Which organizations are connected to suspects in this case?", icon: Building2 },
  { label: "Entity timeline", question: "Show the investigation timeline for all events in this case", icon: Clock },
];

const INTENT_LABEL_MAP: Record<string, { label: string; color: string }> = {
  find_call_connections: { label: "Call Network", color: "#00f2fe" },
  find_associates: { label: "Associates", color: "#ec4899" },
  find_person_connections: { label: "Person Graph", color: "#3b82f6" },
  find_shared_entities: { label: "Shared Entities", color: "#8b5cf6" },
  find_vehicle_connections: { label: "Vehicles", color: "#10b981" },
  find_location_connections: { label: "Locations", color: "#f97316" },
  find_organization_connections: { label: "Organizations", color: "#6366f1" },
  find_bank_transaction_connections: { label: "Financial Flow", color: "#fbbf24" },
  find_case_connections: { label: "Cross-Case", color: "#ef4444" },
  find_shortest_verified_path: { label: "Shortest Path", color: "#14b8a6" },
  investigation_timeline: { label: "Timeline", color: "#a855f7" },
  entity_summary: { label: "Entity Summary", color: "#64748b" },
};

const CONFIDENCE_CONFIG = {
  high: { label: "HIGH CONFIDENCE", color: "#10b981", bg: "rgba(16, 185, 129, 0.12)", icon: ShieldCheck },
  medium: { label: "MEDIUM CONFIDENCE", color: "#fbbf24", bg: "rgba(251, 191, 36, 0.12)", icon: Shield },
  low: { label: "LOW CONFIDENCE", color: "#ef4444", bg: "rgba(239, 68, 68, 0.12)", icon: AlertTriangle },
};

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function ConnectionPathVisualizer({ steps }: { steps: ConnectionPathStep[] }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="copilot-path-container">
      <div className="copilot-section-label">
        <Network size={13} style={{ color: "var(--accent-cyan)" }} />
        Connection Path ({steps.length} hops)
      </div>
      <div className="copilot-path-steps">
        {steps.map((step, i) => (
          <div key={i} className="copilot-path-step">
            <div className="copilot-path-node source">
              <div className="copilot-path-node-type">{step.source_type}</div>
              <div className="copilot-path-node-name">{step.source_name}</div>
            </div>
            <div className="copilot-path-rel">
              <div className="copilot-path-rel-line" />
              <div className="copilot-path-rel-label">{step.relationship_type}</div>
              <div className="copilot-path-rel-badge" style={{
                background: step.verification_status === "VERIFIED"
                  ? "rgba(16,185,129,0.15)" : "rgba(251,191,36,0.15)",
                color: step.verification_status === "VERIFIED" ? "#10b981" : "#fbbf24",
              }}>
                {step.verification_status === "VERIFIED" ? "✓" : "⏳"}
              </div>
              <ChevronRight size={14} style={{ color: "#475569" }} />
            </div>
            {i === steps.length - 1 && (
              <div className="copilot-path-node target">
                <div className="copilot-path-node-type">{step.target_type}</div>
                <div className="copilot-path-node-name">{step.target_name}</div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function AnswerCard({
  response,
  onViewInGraph,
}: {
  response: CopilotQueryResponse;
  onViewInGraph?: () => void;
}) {
  const [showCypher, setShowCypher] = useState(false);
  const conf = CONFIDENCE_CONFIG[response.confidence] || CONFIDENCE_CONFIG.low;
  const ConfIcon = conf.icon;
  const intentMeta = INTENT_LABEL_MAP[response.query_type] || { label: response.query_type, color: "#64748b" };

  return (
    <div className="copilot-answer-card">
      {/* Header Row */}
      <div className="copilot-answer-header">
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          {/* Query type badge */}
          <span className="copilot-badge" style={{ background: `${intentMeta.color}20`, color: intentMeta.color, borderColor: `${intentMeta.color}40` }}>
            {intentMeta.label}
          </span>
          {/* Confidence badge */}
          <span className="copilot-badge" style={{ background: conf.bg, color: conf.color, borderColor: `${conf.color}40` }}>
            <ConfIcon size={11} />
            {conf.label}
          </span>
        </div>
        {/* View in Graph button */}
        {response.graph_data && onViewInGraph && (
          <button className="copilot-graph-btn" onClick={onViewInGraph}>
            <Eye size={13} />
            View in Graph
          </button>
        )}
      </div>

      {/* Ambiguity Notice */}
      {response.ambiguity_notice && (
        <div className="copilot-ambiguity-banner">
          <Info size={13} style={{ flexShrink: 0 }} />
          <span>{response.ambiguity_notice}</span>
        </div>
      )}

      {/* Grounded Answer Text */}
      <div className="copilot-answer-body">
        <div className="copilot-answer-question">
          <span className="copilot-q-label">Q</span>
          <span>{response.question}</span>
        </div>
        <div className="copilot-answer-text">{response.answer}</div>
      </div>

      {/* Evidence Sources */}
      {response.entities_found.length > 0 && (
        <div className="copilot-entities-row">
          <div className="copilot-section-label">
            <CheckCircle2 size={12} style={{ color: "var(--accent-emerald)" }} />
            Graph Evidence ({response.entities_found.length} entities)
          </div>
          <div className="copilot-entity-pills">
            {response.entities_found.slice(0, 8).map((e, i) => (
              <span key={i} className="copilot-entity-pill">{e}</span>
            ))}
            {response.entities_found.length > 8 && (
              <span className="copilot-entity-pill muted">+{response.entities_found.length - 8} more</span>
            )}
          </div>
        </div>
      )}

      {/* Relationship types traversed */}
      {response.relationships_traversed.length > 0 && (
        <div className="copilot-entities-row">
          <div className="copilot-section-label">
            <ArrowRight size={12} style={{ color: "var(--accent-cyan)" }} />
            Relationships Traversed
          </div>
          <div className="copilot-entity-pills">
            {response.relationships_traversed.map((r, i) => (
              <span key={i} className="copilot-entity-pill rel">{r}</span>
            ))}
          </div>
        </div>
      )}

      {/* Connection Path */}
      <ConnectionPathVisualizer steps={response.connection_path} />

      {/* Result count & Cypher toggle */}
      <div className="copilot-answer-footer">
        <span className="copilot-result-count">
          {response.results.length} graph record{response.results.length !== 1 ? "s" : ""} retrieved
        </span>
        <button
          className="copilot-cypher-toggle"
          onClick={() => setShowCypher((v) => !v)}
        >
          <Code2 size={12} />
          {showCypher ? "Hide" : "Show"} Query
        </button>
      </div>

      {/* Cypher Query (developer view) */}
      {showCypher && (
        <pre className="copilot-cypher-block">{response.cypher}</pre>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function InvestigationCopilot({
  caseId,
  onHighlightGraph,
  onNavigateToGraph,
}: InvestigationCopilotProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  const isReady = Boolean(caseId);

  const handleQuery = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed || trimmed.length < 5 || loading) return;
    if (!caseId) {
      setError("No active case selected. Please open a case first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await investigationApi.queryCopilot(caseId, trimmed);
      const item: QueryHistoryItem = {
        id: `q_${Date.now()}`,
        question: trimmed,
        response,
        timestamp: new Date().toLocaleTimeString(),
      };
      setHistory((prev) => [item, ...prev]);
      setQuestion("");
    } catch (err: any) {
      setError(err?.message || "Copilot query failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [caseId, loading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleQuery(question);
    }
  };

  const handleViewInGraph = (response: CopilotQueryResponse) => {
    if (response.graph_data && onHighlightGraph) {
      onHighlightGraph(response.graph_data);
    }
    if (onNavigateToGraph) {
      onNavigateToGraph();
    }
  };

  return (
    <div className="copilot-wrapper">
      {/* Header */}
      <div className="copilot-header">
        <div className="copilot-header-left">
          <div className="copilot-icon-badge">
            <Bot size={20} />
          </div>
          <div>
            <h2 className="copilot-title">Investigation Copilot</h2>
            <p className="copilot-subtitle">
              Natural-language queries grounded strictly in verified graph evidence · No AI guilt inference
            </p>
          </div>
        </div>
        <div className="copilot-security-badge">
          <ShieldCheck size={13} />
          <span>Read-Only · Case-Scoped · Zero Speculation</span>
        </div>
      </div>

      {/* Input Area */}
      <div className="copilot-input-section">
        <div className="copilot-textarea-wrapper">
          <textarea
            ref={textAreaRef}
            id="copilot-question-input"
            className="copilot-textarea"
            placeholder={
              isReady
                ? "Ask anything about this case… e.g. 'Who did Raj Kumar call before the incident?'"
                : "Select an active case to start querying…"
            }
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isReady || loading}
            rows={3}
          />
          <button
            id="copilot-submit-btn"
            className={`copilot-send-btn ${loading ? "loading" : ""}`}
            onClick={() => handleQuery(question)}
            disabled={!isReady || loading || question.trim().length < 5}
            aria-label="Submit investigation query"
          >
            {loading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
          </button>
        </div>

        {/* Quick example pills */}
        <div className="copilot-examples-row">
          <span className="copilot-examples-label">
            <Sparkles size={12} />
            Quick queries:
          </span>
          <div className="copilot-pills">
            {EXAMPLE_QUESTIONS.map((ex) => {
              const Icon = ex.icon;
              return (
                <button
                  key={ex.label}
                  className="copilot-pill"
                  onClick={() => {
                    setQuestion(ex.question);
                    textAreaRef.current?.focus();
                  }}
                  disabled={!isReady || loading}
                >
                  <Icon size={11} />
                  {ex.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="copilot-error-banner" role="alert">
          <AlertTriangle size={14} style={{ flexShrink: 0 }} />
          <span>{error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="copilot-loading">
          <div className="copilot-loading-inner">
            <Loader2 size={20} className="spin" style={{ color: "var(--accent-cyan)" }} />
            <div>
              <div className="copilot-loading-title">Analyzing graph…</div>
              <div className="copilot-loading-sub">
                Extracting intent → Building safe Cypher → Querying Neo4j → Generating grounded answer
              </div>
            </div>
          </div>
          <div className="copilot-loading-dots">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        </div>
      )}

      {/* Results History */}
      {history.length > 0 && (
        <div className="copilot-history">
          {history.map((item) => (
            <div key={item.id} className="copilot-history-item">
              <div className="copilot-history-meta">
                <Bot size={13} style={{ color: "var(--accent-cyan)" }} />
                <span className="copilot-history-time">{item.timestamp}</span>
              </div>
              <AnswerCard
                response={item.response}
                onViewInGraph={() => handleViewInGraph(item.response)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {history.length === 0 && !loading && (
        <div className="copilot-empty-state">
          <div className="copilot-empty-icon">
            <Bot size={40} style={{ color: "var(--accent-cyan)", opacity: 0.5 }} />
          </div>
          <h3 className="copilot-empty-title">Ask your first question</h3>
          <p className="copilot-empty-desc">
            Investigation Copilot converts natural language questions into safe graph queries.
            All answers are grounded strictly in verified graph evidence — no speculation.
          </p>
          <div className="copilot-empty-features">
            <div className="copilot-feature-chip">
              <Layers size={13} />12 supported intents
            </div>
            <div className="copilot-feature-chip">
              <ShieldCheck size={13} />Zero AI guilt inference
            </div>
            <div className="copilot-feature-chip">
              <Network size={13} />Graph path visualization
            </div>
            <div className="copilot-feature-chip">
              <Code2 size={13} />Explainable Cypher
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

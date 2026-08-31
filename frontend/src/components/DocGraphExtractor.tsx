"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Brain,
  Sparkles,
  UploadCloud,
  FileText,
  Zap,
  CheckCircle2,
  AlertCircle,
  Clock,
  Database,
  Share2,
  User,
  PhoneCall,
  DollarSign,
  MapPin,
  Car,
  Building2,
  Users,
  ShieldCheck,
  RefreshCw,
  Key,
  Layers,
  ChevronRight,
  ExternalLink,
  Sliders,
  Check,
  FileCode,
  FileCheck,
} from "lucide-react";
import { investigationApi } from "@/lib/investigationApi";
import {
  IntegrationStatus,
  SampleDocumentMeta,
  DocumentExtractionResult,
} from "@/types/investigation";

interface DocGraphExtractorProps {
  caseId: string;
  onExtractionSuccess: (result: DocumentExtractionResult) => void;
  onNavigateToGraph: () => void;
  onNavigateToCases?: () => void;
}

export default function DocGraphExtractor({
  caseId,
  onExtractionSuccess,
  onNavigateToGraph,
  onNavigateToCases,
}: DocGraphExtractorProps) {
  // Input Modes (PDF & File Upload is primary)
  const [inputMode, setInputMode] = useState<"upload" | "text" | "samples">("upload");

  // Integration Status
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [checkingIntegrations, setCheckingIntegrations] = useState(false);

  // Settings & Custom Keys
  const [showSettingsDrawer, setShowSettingsDrawer] = useState(false);
  const [customGroqKey, setCustomGroqKey] = useState<string>("");
  const [customSupabaseUrl, setCustomSupabaseUrl] = useState<string>("");
  const [apiKeySaved, setApiKeySaved] = useState(false);

  // Sample Documents
  const [samples, setSamples] = useState<SampleDocumentMeta[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>("fir_cyber_syndicate");

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Raw Text State
  const [rawText, setRawText] = useState<string>("");
  const [documentTitle, setDocumentTitle] = useState<string>("FIR No. 92/2026 Ingestion");
  const [documentType, setDocumentType] = useState<string>("FIR");

  // Processing & Results State
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<DocumentExtractionResult | null>(null);
  const [resultTab, setResultTab] = useState<
    "overview" | "persons" | "calls" | "transactions" | "locations" | "vehicles" | "organizations"
  >("overview");

  // Load Integration Status and Samples on Mount
  useEffect(() => {
    loadIntegrations();
    loadSamples();

    // Check localStorage for Groq key
    const savedKey = localStorage.getItem("investigation_groq_api_key");
    if (savedKey) setCustomGroqKey(savedKey);
  }, []);

  const loadIntegrations = async () => {
    try {
      setCheckingIntegrations(true);
      const res = await investigationApi.getIntegrationStatus();
      setIntegrations(res);
    } catch (e) {
      console.warn("Failed to load integrations status", e);
    } finally {
      setCheckingIntegrations(false);
    }
  };

  const loadSamples = async () => {
    try {
      const res = await investigationApi.getSampleDocuments();
      setSamples(res);
    } catch (e) {
      console.warn("Failed to load sample documents", e);
    }
  };

  const handleSaveApiKey = () => {
    if (customGroqKey.trim()) {
      localStorage.setItem("investigation_groq_api_key", customGroqKey.trim());
    } else {
      localStorage.removeItem("investigation_groq_api_key");
    }
    setApiKeySaved(true);
    setTimeout(() => setApiKeySaved(false), 2500);
  };

  // Drag & Drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // Pipeline Execution Runner
  const runExtraction = async (source: "sample" | "file" | "text") => {
    setIsProcessing(true);
    setErrorMessage(null);
    setLastResult(null);
    setProcessingStep(1);

    // Step Animation Simulation for High-End UX
    const stepTimer1 = setTimeout(() => setProcessingStep(2), 600);
    const stepTimer2 = setTimeout(() => setProcessingStep(3), 1400);
    const stepTimer3 = setTimeout(() => setProcessingStep(4), 2200);

    try {
      let result: DocumentExtractionResult;
      const activeKey = customGroqKey.trim() || undefined;

      if (source === "sample") {
        result = await investigationApi.extractSampleDocument(
          selectedSampleId,
          caseId,
          activeKey
        );
      } else if (source === "file" && selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("document_name", selectedFile.name);
        formData.append("document_type", documentType);
        formData.append("case_id", caseId);
        if (activeKey) formData.append("groq_api_key", activeKey);

        result = await investigationApi.uploadAndExtractDocument(formData);
      } else if (source === "text") {
        if (!rawText.trim()) {
          throw new Error("Please enter or paste investigative document text.");
        }
        result = await investigationApi.extractFromText({
          document_text: rawText,
          document_name: documentTitle || "Document_Transcript.txt",
          document_type: documentType,
          case_id: caseId,
          groq_api_key: activeKey,
        });
      } else {
        throw new Error("Invalid document source selected.");
      }

      setProcessingStep(4);
      setLastResult(result);
      onExtractionSuccess(result);
    } catch (err: any) {
      console.error("Extraction error", err);
      setErrorMessage(err.message || "Failed to process document with Groq AI.");
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Top Banner / Integration Health Bar */}
      <div className="section-card" style={{ padding: "1rem 1.25rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "1rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(168, 85, 247, 0.2))",
                border: "1px solid rgba(6, 182, 212, 0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--accent-cyan)",
              }}
            >
              <Brain size={24} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
                  Groq AI & Supabase Document Knowledge Graph Engine
                </h2>
                <span
                  style={{
                    fontSize: "0.65rem",
                    padding: "0.15rem 0.5rem",
                    borderRadius: "999px",
                    background: "rgba(6, 182, 212, 0.15)",
                    color: "var(--accent-cyan)",
                    border: "1px solid rgba(6, 182, 212, 0.3)",
                    fontWeight: 600,
                  }}
                >
                  Llama-3.3-70B Versatile
                </span>
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "0.2rem 0 0 0" }}>
                Automatically parses Police FIRs, Interrogations, CDRs, and Bank statements into relational entities & interactive graph topology.
              </p>
            </div>
          </div>

          {/* Integration Status Badges */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
            {/* Groq Status */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.4rem 0.75rem",
                borderRadius: "var(--radius-sm)",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-color)",
                fontSize: "0.75rem",
              }}
            >
              <Zap size={13} style={{ color: "var(--accent-amber)" }} />
              <span>Groq Cloud:</span>
              <span
                style={{
                  color: integrations?.groq?.configured || customGroqKey ? "var(--accent-emerald)" : "var(--accent-cyan)",
                  fontWeight: 600,
                }}
              >
                {integrations?.groq?.configured || customGroqKey ? "Active (70B)" : "Ready (Demo Mode)"}
              </span>
            </div>

            {/* Supabase Status */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                padding: "0.4rem 0.75rem",
                borderRadius: "var(--radius-sm)",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-color)",
                fontSize: "0.75rem",
              }}
            >
              <Database size={13} style={{ color: "var(--accent-emerald)" }} />
              <span>Supabase / Postgres:</span>
              <span
                style={{
                  color: integrations?.postgres_supabase?.connected ? "var(--accent-emerald)" : "#94a3b8",
                  fontWeight: 600,
                }}
              >
                {integrations?.postgres_supabase?.is_supabase
                  ? "Supabase Connected"
                  : integrations?.postgres_supabase?.connected
                  ? "Postgres Active"
                  : "Memory + Auto Sync"}
              </span>
            </div>

            {/* Settings Button */}
            <button
              onClick={() => setShowSettingsDrawer(!showSettingsDrawer)}
              className="btn-secondary"
              style={{ padding: "0.4rem 0.75rem", fontSize: "0.75rem" }}
            >
              <Sliders size={13} /> {showSettingsDrawer ? "Close Config" : "API & DB Keys"}
            </button>
          </div>
        </div>

        {/* Expandable Configuration Drawer */}
        {showSettingsDrawer && (
          <div
            style={{
              marginTop: "1rem",
              padding: "1rem",
              borderRadius: "var(--radius-sm)",
              background: "rgba(15, 23, 42, 0.7)",
              border: "1px solid var(--border-color)",
              display: "flex",
              flexDirection: "column",
              gap: "0.85rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                Integration Credentials & Override
              </div>
              <button
                onClick={loadIntegrations}
                disabled={checkingIntegrations}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  fontSize: "0.75rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.3rem",
                }}
              >
                <RefreshCw size={12} className={checkingIntegrations ? "spin" : ""} /> Check Status
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>
                  Groq API Key (Optional Override)
                </label>
                <input
                  type="password"
                  value={customGroqKey}
                  onChange={(e) => setCustomGroqKey(e.target.value)}
                  placeholder="gsk_... (leave blank to use backend .env key)"
                  className="form-input"
                  style={{ fontSize: "0.8rem", width: "100%" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>
                  Active LLM Model
                </label>
                <input
                  type="text"
                  value="llama-3.3-70b-versatile (Groq High-Speed Cloud)"
                  disabled
                  className="form-input"
                  style={{ fontSize: "0.8rem", width: "100%", opacity: 0.7 }}
                />
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
              <button onClick={handleSaveApiKey} className="btn-primary" style={{ padding: "0.35rem 0.85rem", fontSize: "0.75rem" }}>
                {apiKeySaved ? (
                  <>
                    <Check size={13} /> Saved in Session
                  </>
                ) : (
                  <>
                    <Key size={13} /> Save Key
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Ingestion Workbench */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(340px, 1fr) minmax(360px, 1.4fr)", gap: "1.25rem" }}>
        {/* Left Column: Document Ingestion Source Tabs */}
        <div className="section-card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Tabs Selector */}
          <div style={{ display: "flex", background: "rgba(0, 0, 0, 0.25)", padding: "0.25rem", borderRadius: "var(--radius-sm)", gap: "0.25rem" }}>
            <button
              onClick={() => setInputMode("samples")}
              style={{
                flex: 1,
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                border: "none",
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                background: inputMode === "samples" ? "var(--bg-card)" : "transparent",
                color: inputMode === "samples" ? "var(--accent-cyan)" : "var(--text-muted)",
                boxShadow: inputMode === "samples" ? "0 2px 4px rgba(0,0,0,0.3)" : "none",
              }}
            >
              <Zap size={14} /> 1-Click Samples
            </button>

            <button
              onClick={() => setInputMode("upload")}
              style={{
                flex: 1,
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                border: "none",
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                background: inputMode === "upload" ? "var(--bg-card)" : "transparent",
                color: inputMode === "upload" ? "var(--accent-cyan)" : "var(--text-muted)",
                boxShadow: inputMode === "upload" ? "0 2px 4px rgba(0,0,0,0.3)" : "none",
              }}
            >
              <UploadCloud size={14} /> Upload File
            </button>

            <button
              onClick={() => setInputMode("text")}
              style={{
                flex: 1,
                padding: "0.5rem",
                borderRadius: "var(--radius-sm)",
                border: "none",
                fontSize: "0.78rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.4rem",
                background: inputMode === "text" ? "var(--bg-card)" : "transparent",
                color: inputMode === "text" ? "var(--accent-cyan)" : "var(--text-muted)",
                boxShadow: inputMode === "text" ? "0 2px 4px rgba(0,0,0,0.3)" : "none",
              }}
            >
              <FileCode size={14} /> Raw FIR Text
            </button>
          </div>

          {/* Mode 1: Preloaded Realistic Crime Samples */}
          {inputMode === "samples" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Select a high-fidelity investigative docket to extract entities and generate the connected Knowledge Graph in 1-click:
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                {samples.map((s) => {
                  const isSelected = selectedSampleId === s.id;
                  return (
                    <div
                      key={s.id}
                      onClick={() => setSelectedSampleId(s.id)}
                      style={{
                        padding: "0.75rem 1rem",
                        borderRadius: "var(--radius-sm)",
                        border: isSelected ? "1px solid var(--accent-cyan)" : "1px solid var(--border-color)",
                        background: isSelected ? "rgba(6, 182, 212, 0.08)" : "rgba(255, 255, 255, 0.02)",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.25rem" }}>
                        <div style={{ fontSize: "0.85rem", fontWeight: 700, color: isSelected ? "var(--accent-cyan)" : "var(--text-primary)" }}>
                          {s.title}
                        </div>
                        <span
                          style={{
                            fontSize: "0.65rem",
                            padding: "0.15rem 0.4rem",
                            borderRadius: "4px",
                            background: "rgba(255, 255, 255, 0.06)",
                            color: "var(--text-muted)",
                            border: "1px solid var(--border-color)",
                          }}
                        >
                          {s.category}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginBottom: "0.4rem" }}>
                        {s.station}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontStyle: "italic", lineHeight: 1.4 }}>
                        &quot;{s.preview}&quot;
                      </div>
                    </div>
                  );
                })}
              </div>

              <button
                onClick={() => runExtraction("sample")}
                disabled={isProcessing}
                className="btn-primary"
                style={{
                  width: "100%",
                  padding: "0.75rem",
                  marginTop: "0.5rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.5rem",
                  fontSize: "0.88rem",
                  fontWeight: 700,
                }}
              >
                {isProcessing ? (
                  <>
                    <RefreshCw size={16} className="spin" /> Processing with Groq 70B...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Synthesize Knowledge Graph with Groq Llama-3.3
                  </>
                )}
              </button>
            </div>
          )}

          {/* Mode 2: File Upload (PDF, DOCX, TXT) */}
          {inputMode === "upload" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: dragActive ? "2px dashed var(--accent-cyan)" : "2px dashed var(--border-color)",
                  borderRadius: "var(--radius-sm)",
                  padding: "2rem 1.5rem",
                  textAlign: "center",
                  background: dragActive ? "rgba(6, 182, 212, 0.05)" : "rgba(0, 0, 0, 0.2)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={handleFileChange}
                  style={{ display: "none" }}
                />

                <div
                  style={{
                    width: "48px",
                    height: "48px",
                    borderRadius: "50%",
                    background: "rgba(6, 182, 212, 0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--accent-cyan)",
                  }}
                >
                  <UploadCloud size={24} />
                </div>

                <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  {selectedFile ? selectedFile.name : "Drop Investigation Document here"}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  Supports PDF, DOCX, TXT files (FIRs, Charge Sheets, Bank Exports)
                </div>

                {selectedFile && (
                  <div
                    style={{
                      fontSize: "0.72rem",
                      padding: "0.2rem 0.6rem",
                      background: "rgba(16, 185, 129, 0.15)",
                      color: "var(--accent-emerald)",
                      borderRadius: "999px",
                      marginTop: "0.25rem",
                    }}
                  >
                    File selected: {(selectedFile.size / 1024).toFixed(1)} KB
                  </div>
                )}
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>
                  Document Classification
                </label>
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  className="form-input"
                  style={{ width: "100%", fontSize: "0.8rem" }}
                >
                  <option value="FIR">First Information Report (FIR)</option>
                  <option value="Charge Sheet">Charge Sheet & Police Report</option>
                  <option value="Interrogation">Interrogation Transcript / Confession</option>
                  <option value="CDR Analysis">CDR & Telecom Geo-Spatial Log</option>
                  <option value="Bank Statement">Bank / Financial Intelligence Statement</option>
                  <option value="Witness Statement">Witness / Informant Statement</option>
                </select>
              </div>

              <button
                onClick={() => runExtraction("file")}
                disabled={isProcessing || !selectedFile}
                className="btn-primary"
                style={{
                  width: "100%",
                  padding: "0.75rem",
                  marginTop: "0.5rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.5rem",
                  fontSize: "0.88rem",
                  fontWeight: 700,
                  opacity: selectedFile ? 1 : 0.6,
                }}
              >
                {isProcessing ? (
                  <>
                    <RefreshCw size={16} className="spin" /> Parsing & Extracting with Groq...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Parse File & Build Knowledge Graph
                  </>
                )}
              </button>
            </div>
          )}

          {/* Mode 3: Raw Text Paste */}
          {inputMode === "text" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>
                  Document Reference Title
                </label>
                <input
                  type="text"
                  value={documentTitle}
                  onChange={(e) => setDocumentTitle(e.target.value)}
                  placeholder="e.g. FIR No. 118/2026 Complaint Narrative"
                  className="form-input"
                  style={{ width: "100%", fontSize: "0.8rem" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>
                  Investigation Transcript / Complaint Text
                </label>
                <textarea
                  rows={8}
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  placeholder="Paste FIR narrative, interrogation questions/answers, CDR phone logs, or transaction notes..."
                  className="form-input"
                  style={{ width: "100%", fontSize: "0.78rem", fontFamily: "monospace", resize: "vertical" }}
                />
              </div>

              <button
                onClick={() => runExtraction("text")}
                disabled={isProcessing || !rawText.trim()}
                className="btn-primary"
                style={{
                  width: "100%",
                  padding: "0.75rem",
                  marginTop: "0.5rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "0.5rem",
                  fontSize: "0.88rem",
                  fontWeight: 700,
                  opacity: rawText.trim() ? 1 : 0.6,
                }}
              >
                {isProcessing ? (
                  <>
                    <RefreshCw size={16} className="spin" /> Synthesizing Graph...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Run Groq Llama-3.3 Entity Extraction
                  </>
                )}
              </button>
            </div>
          )}

          {errorMessage && (
            <div
              style={{
                padding: "0.75rem",
                borderRadius: "var(--radius-sm)",
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.4)",
                color: "#f87171",
                fontSize: "0.78rem",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <AlertCircle size={15} />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Right Column: Live Pipeline Progress or Extracted Intelligence Result */}
        <div className="section-card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "0.95rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <Layers size={16} style={{ color: "var(--accent-cyan)" }} />
              Extracted Knowledge Graph & Intelligence Output
            </h3>
            {lastResult && (
              <span
                style={{
                  fontSize: "0.68rem",
                  padding: "0.15rem 0.5rem",
                  borderRadius: "999px",
                  background: "rgba(16, 185, 129, 0.15)",
                  color: "var(--accent-emerald)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  fontWeight: 600,
                }}
              >
                ✓ Ingested & Synced
              </span>
            )}
          </div>

          {/* Processing Visualizer Steps */}
          {isProcessing && (
            <div
              style={{
                padding: "1.5rem",
                borderRadius: "var(--radius-sm)",
                background: "rgba(0, 0, 0, 0.25)",
                border: "1px solid var(--border-color)",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <RefreshCw size={18} className="spin" style={{ color: "var(--accent-cyan)" }} />
                <span style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  Groq Cloud Llama-3.3-70B Pipeline Executing...
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                {[
                  { step: 1, label: "Document Ingestion & Text Parsing (pypdf/docx)" },
                  { step: 2, label: "Groq Llama-3.3-70B NER & Named Entity Disambiguation" },
                  { step: 3, label: "Knowledge Graph Link Topology & Relationship Resolution" },
                  { step: 4, label: "PostgreSQL / Supabase Entity Persistence & Case Store Sync" },
                ].map((s) => {
                  const isDone = processingStep > s.step;
                  const isCurrent = processingStep === s.step;
                  return (
                    <div
                      key={s.step}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.6rem",
                        fontSize: "0.78rem",
                        color: isDone ? "var(--accent-emerald)" : isCurrent ? "var(--accent-cyan)" : "var(--text-muted)",
                      }}
                    >
                      {isDone ? (
                        <CheckCircle2 size={15} style={{ color: "var(--accent-emerald)" }} />
                      ) : isCurrent ? (
                        <RefreshCw size={15} className="spin" style={{ color: "var(--accent-cyan)" }} />
                      ) : (
                        <Clock size={15} style={{ color: "var(--text-muted)" }} />
                      )}
                      <span>{s.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Results State */}
          {!isProcessing && lastResult && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {/* Case Executive Summary Card */}
              <div
                style={{
                  padding: "1rem",
                  borderRadius: "var(--radius-sm)",
                  background: "rgba(6, 182, 212, 0.05)",
                  border: "1px solid rgba(6, 182, 212, 0.2)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
                      {lastResult.case_meta?.title || lastResult.document_name}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--accent-cyan)" }}>
                      {lastResult.case_meta?.case_number || "CR-2026-AUTO"} • {lastResult.case_meta?.jurisdiction || "Hyderabad CCS"}
                    </div>
                  </div>
                  <span
                    style={{
                      fontSize: "0.65rem",
                      padding: "0.2rem 0.5rem",
                      borderRadius: "4px",
                      background: "rgba(255, 255, 255, 0.08)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    Model: {lastResult.model_used}
                  </span>
                </div>

                <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", margin: "0.2rem 0", lineHeight: 1.45 }}>
                  {lastResult.case_meta?.summary}
                </p>

                {lastResult.case_meta?.legal_sections && lastResult.case_meta.legal_sections.length > 0 && (
                  <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", marginTop: "0.2rem" }}>
                    {lastResult.case_meta.legal_sections.map((sec, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: "0.68rem",
                          padding: "0.15rem 0.45rem",
                          borderRadius: "4px",
                          background: "rgba(239, 68, 68, 0.15)",
                          color: "#fca5a5",
                          border: "1px solid rgba(239, 68, 68, 0.3)",
                        }}
                      >
                        {sec}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Entity KPI Counters */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem" }}>
                <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
                  <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Persons</div>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
                    {lastResult.added_counts.persons}
                  </div>
                </div>
                <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
                  <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Calls (CDR)</div>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-blue)" }}>
                    {lastResult.added_counts.calls}
                  </div>
                </div>
                <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
                  <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Transactions</div>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-amber)" }}>
                    {lastResult.added_counts.transactions}
                  </div>
                </div>
                <div style={{ padding: "0.6rem", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
                  <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Graph Nodes</div>
                  <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-emerald)" }}>
                    {lastResult.graph.nodes.length}
                  </div>
                </div>
              </div>

              {/* Action Jump Buttons */}
              <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}>
                <button
                  onClick={onNavigateToGraph}
                  className="btn-primary"
                  style={{
                    flex: 1,
                    padding: "0.65rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.4rem",
                    fontSize: "0.82rem",
                    fontWeight: 700,
                  }}
                >
                  <Share2 size={14} /> Open Connected Network Graph
                </button>

                {onNavigateToCases && (
                  <button
                    onClick={onNavigateToCases}
                    className="btn-secondary"
                    style={{
                      flex: 1,
                      padding: "0.65rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.4rem",
                      fontSize: "0.82rem",
                    }}
                  >
                    <FileText size={14} /> View in Case Dossier
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Empty State before Extraction */}
          {!isProcessing && !lastResult && (
            <div
              style={{
                flex: 1,
                minHeight: "260px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                border: "1px dashed var(--border-color)",
                borderRadius: "var(--radius-sm)",
                padding: "2rem",
                textAlign: "center",
                color: "var(--text-muted)",
                gap: "0.75rem",
              }}
            >
              <div
                style={{
                  width: "52px",
                  height: "52px",
                  borderRadius: "50%",
                  background: "rgba(255, 255, 255, 0.03)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-muted)",
                }}
              >
                <Share2 size={24} />
              </div>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                No Document Ingested in Current Session
              </div>
              <p style={{ fontSize: "0.78rem", maxWidth: "340px", lineHeight: 1.4 }}>
                Choose one of the 1-Click Sample Dockets on the left or upload your FIR document to trigger Groq Llama-3.3-70B Knowledge Graph synthesis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

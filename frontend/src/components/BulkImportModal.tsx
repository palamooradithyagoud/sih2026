"use client";

import React, { useState } from "react";
import {
  X,
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Table,
  Sparkles,
} from "lucide-react";
import { investigationApi } from "@/lib/investigationApi";
import { VerificationStatus, CallRecord, Transaction } from "@/types/investigation";

interface BulkImportModalProps {
  caseId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function BulkImportModal({
  caseId,
  isOpen,
  onClose,
  onSuccess,
}: BulkImportModalProps) {
  const [importType, setImportType] = useState<"calls" | "transactions">("calls");
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus>("VERIFIED");
  const [officerId, setOfficerId] = useState("Officer ID 1024 (Insp. Adithya)");
  const [csvText, setCsvText] = useState("");
  const [parsedRows, setParsedRows] = useState<any[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const sampleCallsCsv = `caller_number,caller_name,receiver_number,receiver_name,date,time,duration_seconds,call_type,cell_tower_id
9876543210,Raj Kumar,9988776655,Ahmed Khan,2026-08-25,21:42:00,512,Outgoing,HYD-TWR-884
9988776655,Ahmed Khan,9123456780,Ravi Teja,2026-08-26,09:15:00,184,Outgoing,HYD-TWR-302
9848011223,Raj Kumar (Sec),9988776655,Ahmed Khan,2026-08-26,14:20:00,320,Incoming,HYD-TWR-884
9123456780,Ravi Teja,9876543210,Raj Kumar,2026-08-26,18:45:00,95,Incoming,HYD-TWR-101`;

  const sampleTransactionsCsv = `sender_name,sender_account,receiver_name,receiver_account,amount,date,time,transaction_id,bank_name,payment_type
Raj Kumar,HDFC-9912,Ahmed Khan,ICICI-4410,250000,2026-08-20,14:23:00,TXN123456,HDFC Bank,Bank Transfer
Ahmed Khan,ICICI-4410,Ravi Teja,SBI-8821,180000,2026-08-21,10:05:00,TXN987654,ICICI Bank,UPI / IMPS
Raj Kumar,HDFC-9912,Priya Kumar,HDFC-1002,500000,2026-08-22,16:40:00,TXN554433,HDFC Bank,Bank Transfer
Ravi Teja,SBI-8821,Apex Global Logistics,AXIS-9090,120000,2026-08-23,11:10:00,TXN332211,SBI Bank,Hawala Cash`;

  const handleLoadSample = (type: "calls" | "transactions") => {
    setImportType(type);
    const content = type === "calls" ? sampleCallsCsv : sampleTransactionsCsv;
    setCsvText(content);
    parseCsvContent(content, type);
    setErrorMsg(null);
  };

  const parseCsvContent = (text: string, type: "calls" | "transactions") => {
    const lines = text.trim().split("\n");
    if (lines.length < 2) {
      setParsedRows([]);
      return;
    }

    const headers = lines[0].split(",").map((h) => h.trim());
    const rows = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const values = line.split(",").map((v) => v.trim());
      const rowObj: any = {};
      headers.forEach((h, index) => {
        rowObj[h] = values[index] || "";
      });
      rows.push(rowObj);
    }
    setParsedRows(rows);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setCsvText(text);
    parseCsvContent(text, importType);
  };

  const handleCommit = async () => {
    if (parsedRows.length === 0) {
      setErrorMsg("Please provide or load valid CSV rows to import.");
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      if (importType === "calls") {
        const payload = parsedRows.map((r) => ({
          caller_number: r.caller_number,
          caller_name: r.caller_name || undefined,
          receiver_number: r.receiver_number,
          receiver_name: r.receiver_name || undefined,
          date: r.date || "2026-08-26",
          time: r.time || "12:00:00",
          duration_seconds: Number(r.duration_seconds) || 120,
          call_type: r.call_type || "Outgoing",
          cell_tower_id: r.cell_tower_id || undefined,
          source: "Bulk CDR CSV File",
          added_by_officer: officerId,
          verification_status: verificationStatus,
          confidence_score: 0.98,
        }));
        await investigationApi.bulkImportCalls(caseId, payload);
      } else {
        const payload = parsedRows.map((r) => ({
          sender_name: r.sender_name,
          sender_account: r.sender_account || undefined,
          receiver_name: r.receiver_name,
          receiver_account: r.receiver_account || undefined,
          amount: Number(r.amount) || 50000,
          currency: "INR",
          date: r.date || "2026-08-20",
          time: r.time || "12:00:00",
          transaction_id: r.transaction_id || `TXN${Math.floor(100000 + Math.random() * 900000)}`,
          bank_name: r.bank_name || "Bank",
          payment_type: r.payment_type || "Bank Transfer",
          source: "Bulk Bank Ledger CSV File",
          added_by_officer: officerId,
          verification_status: verificationStatus,
          confidence_score: 0.99,
        }));
        await investigationApi.bulkImportTransactions(caseId, payload);
      }

      setSuccessMsg(`Successfully imported and graph-indexed ${parsedRows.length} records!`);
      onSuccess();
      setTimeout(() => {
        onClose();
      }, 1800);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Bulk import failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content-large">
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div className="card-icon-wrapper" style={{ width: 36, height: 36 }}>
              <FileSpreadsheet size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Bulk Data / CSV Importer</h2>
              <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)" }}>
                Ingest hundreds of CDR call logs or banking transaction ledgers in one click
              </p>
            </div>
          </div>
          <button onClick={onClose} className="btn-icon">
            <X size={20} />
          </button>
        </div>

        <div className="modal-form-body">
          {successMsg && (
            <div className="alert-success">
              <CheckCircle2 size={16} /> {successMsg}
            </div>
          )}
          {errorMsg && (
            <div className="alert-error">
              <AlertCircle size={16} /> {errorMsg}
            </div>
          )}

          {/* Type Selector & Sample Loaders */}
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                onClick={() => handleLoadSample("calls")}
                className={`btn-secondary ${importType === "calls" ? "active-filter" : ""}`}
              >
                <Sparkles size={14} /> CDR Call Records CSV
              </button>
              <button
                type="button"
                onClick={() => handleLoadSample("transactions")}
                className={`btn-secondary ${importType === "transactions" ? "active-filter" : ""}`}
              >
                <Sparkles size={14} /> Financial Ledgers CSV
              </button>
            </div>

            <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Default Verification:</span>
              <select
                value={verificationStatus}
                onChange={(e) => setVerificationStatus(e.target.value as VerificationStatus)}
                className="form-select"
                style={{ padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
              >
                <option value="VERIFIED">✓ Verified</option>
                <option value="UNDER_REVIEW">⏳ Under Review</option>
                <option value="UNVERIFIED">⚠ Unverified</option>
              </select>
            </div>
          </div>

          {/* Raw CSV Textarea */}
          <div className="form-group" style={{ marginTop: "1rem" }}>
            <label className="form-label">
              CSV Content (Paste raw text or edit directly)
            </label>
            <textarea
              rows={5}
              value={csvText}
              onChange={handleTextChange}
              placeholder="caller_number,caller_name,receiver_number,receiver_name,date,time,duration_seconds,call_type"
              className="form-textarea"
              style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}
            />
          </div>

          {/* Parsed Preview Table */}
          {parsedRows.length > 0 && (
            <div style={{ marginTop: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
                <Table size={16} style={{ color: "var(--accent-cyan)" }} />
                <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>
                  Parsed Records Preview ({parsedRows.length} entries ready for graph indexing)
                </span>
              </div>

              <div style={{ maxHeight: "200px", overflowY: "auto", border: "1px solid var(--border-color)", borderRadius: "var(--radius-sm)" }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      {Object.keys(parsedRows[0]).map((key) => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsedRows.map((row, idx) => (
                      <tr key={idx}>
                        {Object.values(row).map((val: any, cIdx) => (
                          <td key={cIdx}>{val || "-"}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="modal-footer" style={{ marginTop: "1.5rem" }}>
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button
              type="button"
              onClick={handleCommit}
              disabled={submitting || parsedRows.length === 0}
              className="btn-primary"
            >
              <UploadCloud size={16} />
              {submitting ? "Committing Records..." : `Import ${parsedRows.length} Records`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

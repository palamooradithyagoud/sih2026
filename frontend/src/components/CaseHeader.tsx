"use client";

import React from "react";
import {
  ShieldAlert,
  PlusCircle,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Radio,
} from "lucide-react";
import { CaseSummary } from "@/types/investigation";

interface CaseHeaderProps {
  summary: CaseSummary | null;
  onOpenAddData: () => void;
  onOpenBulkImport: () => void;
}

export default function CaseHeader({
  summary,
  onOpenAddData,
  onOpenBulkImport,
}: CaseHeaderProps) {
  const caseNumber = summary?.case_number || "CR-2026-00421";
  const caseTitle = summary?.title || "Hyderabad Organized Crime Investigation";
  const verifiedPct = summary?.verification_percentage || 0;

  return (
    <header className="case-header-card">
      <div className="case-header-main">
        <div className="case-title-area">
          <div className="case-meta-row">
            <span className="case-id-badge">CASE: {caseNumber}</span>
            <span className="case-priority-badge">
              <Radio size={12} className="pulse-dot" /> CRITICAL PRIORITY
            </span>
            <span className="case-station-badge">Hyderabad Central Crime Station</span>
          </div>
          <h1 className="case-headline">{caseTitle}</h1>
        </div>

        {/* Action Buttons */}
        <div className="case-actions-group">
          <button onClick={onOpenAddData} className="btn-primary">
            <PlusCircle size={16} />
            <span>Add Investigation Data</span>
          </button>

          <button onClick={onOpenBulkImport} className="btn-secondary">
            <UploadCloud size={16} />
            <span>Bulk CSV Import</span>
          </button>
        </div>
      </div>

      {/* Officer Verification Integrity Bar */}
      <div className="verification-strip">
        <div className="verification-metric-group">
          <div className="verification-text">
            <strong>Officer-Verified Intelligence Rate:</strong> {verifiedPct}%
          </div>
          <div className="verification-counts">
            <span className="count-verified">
              <CheckCircle2 size={13} /> {summary?.verified_count || 0} Verified
            </span>
            <span className="count-review">
              <Clock size={13} /> {summary?.under_review_count || 0} Under Review
            </span>
            <span className="count-unverified">
              <AlertTriangle size={13} /> {summary?.unverified_count || 0} Unverified
            </span>
          </div>
        </div>

        <div className="verification-progress-bg">
          <div
            className="verification-progress-fill"
            style={{ width: `${verifiedPct}%` }}
          />
        </div>
      </div>
    </header>
  );
}

"use client";

import React from "react";
import { PlusCircle, UploadCloud, ShieldAlert } from "lucide-react";
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

  return (
    <div className="minimal-top-actions-bar">
      <div className="case-title-minimal">
        <span className="case-id-badge">CASE: {caseNumber}</span>
        <span className="case-title-text">{caseTitle}</span>
      </div>

      <div className="case-actions-group">
        <button onClick={onOpenAddData} className="btn-primary">
          <PlusCircle size={16} />
          <span>Add Investigation Data</span>
        </button>

        <button onClick={onOpenBulkImport} className="btn-secondary">
          <UploadCloud size={16} />
          <span>Bulk CSV Import / Import File</span>
        </button>
      </div>
    </div>
  );
}

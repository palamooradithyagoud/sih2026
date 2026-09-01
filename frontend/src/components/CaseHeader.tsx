"use client";

import React from "react";
import { PlusCircle, UploadCloud, FileText, ShieldAlert } from "lucide-react";
import { CaseSummary } from "@/types/investigation";

interface CaseHeaderProps {
  summary: CaseSummary | null;
  onOpenAddData: () => void;
  onOpenBulkImport: () => void;
  onOpenAiPdfExtractor?: () => void;
}

export default function CaseHeader({
  summary,
  onOpenAddData,
  onOpenBulkImport,
  onOpenAiPdfExtractor,
}: CaseHeaderProps) {
  const caseNumber = summary?.case_number || "NO CASE ACTIVE";
  const caseTitle = summary?.title || "Select or Ingest an Investigation Case File";

  return (
    <div className="minimal-top-actions-bar">
      <div className="case-title-minimal">
        <span className="case-id-badge">CASE: {caseNumber}</span>
        <span className="case-title-text">{caseTitle}</span>
      </div>

      <div className="case-actions-group">
        {onOpenAiPdfExtractor && (
          <button onClick={onOpenAiPdfExtractor} className="btn-primary">
            <FileText size={16} />
            <span>Upload PDF (Groq AI)</span>
          </button>
        )}

        <button onClick={onOpenAddData} className="btn-secondary">
          <PlusCircle size={16} />
          <span>Add Record</span>
        </button>

        <button onClick={onOpenBulkImport} className="btn-secondary">
          <UploadCloud size={16} />
          <span>Bulk CSV</span>
        </button>
      </div>
    </div>
  );
}

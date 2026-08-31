"use client";

import React from "react";
import {
  LayoutDashboard,
  FolderLock,
  Search,
  FileText,
  Share2,
  BarChart3,
  ShieldCheck,
  UserCheck,
  Brain,
  Sparkles,
} from "lucide-react";

export type ActiveNavTab =
  | "dashboard"
  | "ai-extractor"
  | "cases"
  | "investigation"
  | "evidence"
  | "network"
  | "analytics";

interface SidebarProps {
  activeTab: ActiveNavTab;
  setActiveTab: (tab: ActiveNavTab) => void;
  caseNumber: string;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  caseNumber,
}: SidebarProps) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "ai-extractor", label: "AI Document Ingestion", icon: Brain, badge: "Groq 70B" },
    { id: "cases", label: "Cases", icon: FolderLock },
    { id: "investigation", label: "Investigation", icon: Search },
    { id: "evidence", label: "Evidence Vault", icon: FileText },
    { id: "network", label: "Network Graph", icon: Share2 },
    { id: "analytics", label: "Analytics & Logs", icon: BarChart3 },
  ];

  return (
    <aside className="sidebar-container">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="brand-badge-icon">
          <ShieldCheck size={22} />
        </div>
        <div>
          <h2 className="brand-title">CRIMINAL NETWORK</h2>
          <span className="brand-subtitle">ANALYSIS & INVESTIGATION</span>
        </div>
      </div>

      {/* Active Case Pill */}
      <div className="sidebar-case-card">
        <div className="case-card-label">ACTIVE CASE FILE</div>
        <div className="case-card-number">{caseNumber}</div>
        <div className="case-card-tag">{caseNumber === "NO CASE" ? "No Active Case" : "Active Investigation"}</div>
      </div>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as ActiveNavTab)}
              className={`nav-button ${isActive ? "active" : ""}`}
            >
              <Icon size={18} className="nav-icon" />
              <span style={{ flex: 1, textAlign: "left" }}>{item.label}</span>
              {item.badge && (
                <span
                  style={{
                    fontSize: "0.6rem",
                    padding: "0.1rem 0.4rem",
                    borderRadius: "999px",
                    background: "rgba(6, 182, 212, 0.15)",
                    color: "var(--accent-cyan)",
                    border: "1px solid rgba(6, 182, 212, 0.3)",
                    fontWeight: 700,
                  }}
                >
                  {item.badge}
                </span>
              )}
              {isActive && <div className="active-indicator" />}
            </button>
          );
        })}
      </nav>

      {/* Officer Credential Footer */}
      <div className="sidebar-officer-footer">
        <div className="officer-avatar">
          <UserCheck size={18} />
        </div>
        <div className="officer-info">
          <div className="officer-name">Investigator Portal</div>
          <div className="officer-role">Crime Intelligence Analysis</div>
        </div>
      </div>
    </aside>
  );
}

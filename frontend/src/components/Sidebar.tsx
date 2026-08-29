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
} from "lucide-react";

export type ActiveNavTab =
  | "dashboard"
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
        <div className="case-card-tag">Hyderabad Syndicate</div>
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
              <span>{item.label}</span>
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
          <div className="officer-name">Insp. Adithya</div>
          <div className="officer-role">ID: 1024 • Lead Investigator</div>
        </div>
      </div>
    </aside>
  );
}

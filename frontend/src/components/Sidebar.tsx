"use client";

import React, { useState } from "react";
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
  Bot,
  Sparkles,
  ArrowRight,
  ChevronDown,
  Globe,
} from "lucide-react";

export type ActiveNavTab =
  | "dashboard"
  | "ai-extractor"
  | "cases"
  | "investigation"
  | "evidence"
  | "network"
  | "analytics"
  | "copilot";

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
  const [showNotificationBanner, setShowNotificationBanner] = useState(true);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "ai-extractor", label: "AI Doc Extractor", icon: Brain, badge: "Groq AI" },
    { id: "cases", label: "Cases", icon: FolderLock },
    { id: "investigation", label: "Investigation", icon: Search },
    { id: "evidence", label: "Evidence Vault", icon: FileText },
    { id: "network", label: "Graph Studio", icon: Share2 },
    { id: "copilot", label: "Copilot", icon: Bot, badge: "AI" },
    { id: "analytics", label: "Analytics & Logs", icon: BarChart3 },
  ];

  return (
    <header className="top-navbar-wrapper">
      {/* ConnectDots Top Announcement Banner */}
      {showNotificationBanner && (
        <div className="top-announcement-banner">
          <span>
            <strong>ConnectDots Powered</strong> — Intelligence Analysis Software & Connected Criminal Knowledge Graph Engine.
          </span>
          <ArrowRight size={12} style={{ display: "inline", verticalAlign: "middle", marginLeft: 4 }} />
        </div>
      )}

      {/* Main Top Header Navigation */}
      <div className="top-header-bar">
        {/* Brand Logo & Title */}
        <div className="brand-logo-container" onClick={() => setActiveTab("dashboard")}>
          <div className="brand-badge-icon">
            <Globe size={22} />
          </div>
          <div>
            <h2 className="brand-title">ConnectDots</h2>
            <span className="brand-subtitle">Intelligence Analysis Platform</span>
          </div>
        </div>

        {/* Center Horizontal Menu Navigation Links */}
        <nav className="top-nav-menu">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as ActiveNavTab)}
                className={`top-nav-link ${isActive ? "active" : ""}`}
              >
                <Icon size={15} className="nav-icon" />
                <span>{item.label}</span>
                {item.badge && <span className="top-nav-badge">{item.badge}</span>}
              </button>
            );
          })}
        </nav>

        {/* Right Action Bar */}
        <div className="top-actions-container">
          {/* Active Case Tag */}
          <div className="top-case-tag">
            <span className="top-case-label">ACTIVE CASE:</span>
            <span className="top-case-number">{caseNumber}</span>
          </div>

          {/* ConnectDots Pill Call-To-Action Button */}
          <button className="top-demo-btn">
            <span>Explore ConnectDots</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </header>
  );
}


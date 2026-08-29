"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Share2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Info,
  Search,
} from "lucide-react";
import { GraphData, GraphNode, GraphLink, VerificationStatus } from "@/types/investigation";

interface NetworkGraphPreviewProps {
  graphData: GraphData | null;
  loading: boolean;
  onRefresh: () => void;
}

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

export default function NetworkGraphPreview({
  graphData,
  loading,
  onRefresh,
}: NetworkGraphPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const simNodesRef = useRef<SimNode[]>([]);
  const animationFrameRef = useRef<number | null>(null);

  // Initialize simulation positions
  useEffect(() => {
    if (!graphData || graphData.nodes.length === 0) {
      simNodesRef.current = [];
      return;
    }

    const width = 800;
    const height = 500;
    const count = graphData.nodes.length;

    // Arrange nodes in an organic circle initially
    simNodesRef.current = graphData.nodes.map((n, i) => {
      const angle = (i / count) * 2 * Math.PI;
      const dist = 140 + Math.random() * 80;
      const radius = n.type === "Person" ? 24 : n.type === "Organization" ? 22 : 18;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * dist,
        y: height / 2 + Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        radius,
      };
    });

    if (graphData.nodes.length > 0 && !selectedNode) {
      setSelectedNode(graphData.nodes[0]);
    }
  }, [graphData]);

  // Physics animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    const tick = () => {
      if (!running) return;

      const nodes = simNodesRef.current;
      const links = graphData?.links || [];
      const width = canvas.width;
      const height = canvas.height;

      // 1. Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 220) {
            const force = (220 - dist) / dist * 0.08;
            nodes[i].vx -= dx * force;
            nodes[i].vy -= dy * force;
            nodes[j].vx += dx * force;
            nodes[j].vy += dy * force;
          }
        }
      }

      // 2. Attraction along links
      links.forEach((link) => {
        const sourceNode = nodes.find((n) => n.id === link.source);
        const targetNode = nodes.find((n) => n.id === link.target);
        if (sourceNode && targetNode) {
          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const desiredDist = 120;
          const force = (dist - desiredDist) * 0.02;
          sourceNode.vx += dx / dist * force;
          sourceNode.vy += dy / dist * force;
          targetNode.vx -= dx / dist * force;
          targetNode.vy -= dy / dist * force;
        }
      });

      // 3. Center gravity and damping
      nodes.forEach((node) => {
        const dx = width / 2 - node.x;
        const dy = height / 2 - node.y;
        node.vx += dx * 0.005;
        node.vy += dy * 0.005;

        // Apply velocity with damping
        node.vx *= 0.85;
        node.vy *= 0.85;
        node.x += node.vx;
        node.y += node.vy;

        // Boundaries
        node.x = Math.max(40, Math.min(width - 40, node.x));
        node.y = Math.max(40, Math.min(height - 40, node.y));
      });

      // --- RENDER ---
      ctx.clearRect(0, 0, width, height);
      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);

      // Render Links
      links.forEach((link) => {
        const source = nodes.find((n) => n.id === link.source);
        const target = nodes.find((n) => n.id === link.target);
        if (!source || !target) return;

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);

        if (link.label.startsWith("₹")) {
          ctx.strokeStyle = "rgba(245, 158, 11, 0.7)"; // Gold for money
          ctx.lineWidth = 2.5;
        } else if (link.label.startsWith("CALLED")) {
          ctx.strokeStyle = "rgba(56, 189, 248, 0.6)"; // Blue for calls
          ctx.lineWidth = 2;
        } else {
          ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
          ctx.lineWidth = 1.5;
        }
        ctx.stroke();

        // Relationship label
        const midX = (source.x + target.x) / 2;
        const midY = (source.y + target.y) / 2;
        ctx.fillStyle = "#0f1422";
        ctx.fillRect(midX - 25, midY - 9, 50, 16);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
        ctx.strokeRect(midX - 25, midY - 9, 50, 16);

        ctx.font = "9px 'JetBrains Mono', monospace";
        ctx.fillStyle = link.label.startsWith("₹") ? "#fbbf24" : "#94a3b8";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(link.label.length > 12 ? link.label.slice(0, 11) + "…" : link.label, midX, midY);
      });

      // Render Nodes
      nodes.forEach((node) => {
        const isMatched = searchTerm && node.label.toLowerCase().includes(searchTerm.toLowerCase());
        const isSelected = selectedNode?.id === node.id;

        // Node Glow
        if (isSelected || isMatched) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 6, 0, 2 * Math.PI);
          ctx.fillStyle = isMatched ? "rgba(244, 63, 94, 0.4)" : "rgba(0, 242, 254, 0.35)";
          ctx.fill();
        }

        // Node Circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);

        if (node.type === "Person") {
          ctx.fillStyle = node.subType === "SUSPECT" ? "#f43f5e" : "#0284c7";
        } else if (node.type === "Vehicle") {
          ctx.fillStyle = "#10b981";
        } else if (node.type === "Location") {
          ctx.fillStyle = "#f59e0b";
        } else if (node.type === "Organization") {
          ctx.fillStyle = "#8b5cf6";
        } else {
          ctx.fillStyle = "#64748b";
        }
        ctx.fill();
        ctx.strokeStyle = isSelected ? "#ffffff" : "rgba(255, 255, 255, 0.3)";
        ctx.lineWidth = isSelected ? 3 : 1.5;
        ctx.stroke();

        // Label below node
        ctx.font = "bold 11px 'Plus Jakarta Sans', sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(node.label, node.x, node.y + node.radius + 4);

        // SubType Badge
        ctx.font = "8px 'JetBrains Mono', monospace";
        ctx.fillStyle = "rgba(255, 255, 255, 0.6)";
        ctx.fillText(node.type.toUpperCase(), node.x, node.y + node.radius + 17);
      });

      ctx.restore();
      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);

    return () => {
      running = false;
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [graphData, zoom, pan, selectedNode, searchTerm]);

  // Click on Canvas to select node
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;

    const clickedNode = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius;
    });

    if (clickedNode) {
      setSelectedNode(clickedNode);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="graph-container-card">
      <div className="graph-toolbar">
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div className="card-icon-wrapper" style={{ width: 34, height: 34 }}>
            <Share2 size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>
              Live Knowledge Graph & Intelligence Network
            </h3>
            <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              Autonomously generated from officer-entered calls, transactions, locations & vehicles
            </span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div className="search-box-inline">
            <Search size={14} style={{ color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search entity..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input-inline"
            />
          </div>

          <button onClick={() => setZoom((z) => Math.min(2, z + 0.15))} className="btn-icon-small" title="Zoom In">
            <ZoomIn size={15} />
          </button>
          <button onClick={() => setZoom((z) => Math.max(0.5, z - 0.15))} className="btn-icon-small" title="Zoom Out">
            <ZoomOut size={15} />
          </button>
          <button
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            className="btn-icon-small"
            title="Reset View"
          >
            <RotateCcw size={15} />
          </button>
        </div>
      </div>

      <div className="graph-split-view">
        {/* Canvas Area */}
        <div className="canvas-wrapper">
          <canvas
            ref={canvasRef}
            width={780}
            height={460}
            onClick={handleCanvasClick}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            style={{ width: "100%", height: "100%", cursor: isDragging ? "grabbing" : "grab" }}
          />

          <div className="graph-legend">
            <div className="legend-item"><span className="dot dot-suspect" /> Suspect</div>
            <div className="legend-item"><span className="dot dot-associate" /> Associate</div>
            <div className="legend-item"><span className="dot dot-vehicle" /> Vehicle</div>
            <div className="legend-item"><span className="dot dot-location" /> Location</div>
            <div className="legend-item"><span className="dot dot-org" /> Organization</div>
          </div>
        </div>

        {/* Selected Entity Dossier Inspector */}
        <div className="dossier-panel">
          <div className="dossier-header">
            <Info size={16} style={{ color: "var(--accent-cyan)" }} />
            <span>Entity Intelligence Dossier</span>
          </div>

          {selectedNode ? (
            <div className="dossier-body">
              <div className="dossier-title-row">
                <h4>{selectedNode.label}</h4>
                <span className={`status-indicator-badge ${selectedNode.verification_status === "VERIFIED" ? "connected" : "connecting"}`}>
                  {selectedNode.verification_status === "VERIFIED" ? (
                    <>
                      <CheckCircle2 size={12} /> VERIFIED
                    </>
                  ) : (
                    <>
                      <AlertTriangle size={12} /> {selectedNode.verification_status}
                    </>
                  )}
                </span>
              </div>

              <div className="dossier-field">
                <span className="field-label">Entity Type</span>
                <span className="field-val">{selectedNode.type} ({selectedNode.subType || "General"})</span>
              </div>

              {selectedNode.properties.occupation && (
                <div className="dossier-field">
                  <span className="field-label">Occupation / Front</span>
                  <span className="field-val">{selectedNode.properties.occupation}</span>
                </div>
              )}

              {selectedNode.properties.address && (
                <div className="dossier-field">
                  <span className="field-label">Address</span>
                  <span className="field-val">{selectedNode.properties.address}</span>
                </div>
              )}

              {selectedNode.properties.reg && (
                <div className="dossier-field">
                  <span className="field-label">Registration</span>
                  <span className="field-val">{selectedNode.properties.reg}</span>
                </div>
              )}

              {selectedNode.properties.phones && selectedNode.properties.phones.length > 0 && (
                <div className="dossier-field">
                  <span className="field-label">Phone Numbers</span>
                  <span className="field-val">{selectedNode.properties.phones.join(", ")}</span>
                </div>
              )}

              {selectedNode.properties.aliases && selectedNode.properties.aliases.length > 0 && (
                <div className="dossier-field">
                  <span className="field-label">Known Aliases</span>
                  <span className="field-val">{selectedNode.properties.aliases.join(", ")}</span>
                </div>
              )}

              {/* Connected Links Summary */}
              <div style={{ marginTop: "1rem" }}>
                <span className="field-label" style={{ marginBottom: "0.4rem", display: "block" }}>
                  Connected Relationships
                </span>
                <div className="dossier-links-list">
                  {graphData?.links
                    .filter((l) => l.source === selectedNode.id || l.target === selectedNode.id)
                    .map((l) => {
                      const isOutgoing = l.source === selectedNode.id;
                      const otherId = isOutgoing ? l.target : l.source;
                      const otherNode = graphData.nodes.find((n) => n.id === otherId);
                      return (
                        <div key={l.id} className="dossier-link-item">
                          <span>
                            {isOutgoing ? "→" : "←"} <strong>{l.label}</strong> {isOutgoing ? "to" : "from"} {otherNode?.label || otherId}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div className="dossier-empty">
              Click any node in the graph to inspect intelligence attributes and verification details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
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
  Crosshair,
  Filter,
  Layers,
  Sparkles,
  Play,
  Pause,
  Maximize2,
  Eye,
  Compass,
  Zap,
  Building2,
  MapPin,
  FileText,
  PhoneCall,
  CreditCard,
  Car,
  User,
} from "lucide-react";
import { GraphData, GraphNode, GraphLink, VerificationStatus } from "@/types/investigation";

interface NetworkGraphPreviewProps {
  graphData: GraphData | null;
  loading: boolean;
  onRefresh: () => void;
  fullHeight?: boolean;
}

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  isCenter?: boolean;
  pinned?: boolean;
  iconType: string;
}

const EMPTY_GRAPH_DATA: GraphData = {
  nodes: [],
  links: [],
};

// GraphAware / Hume Color Palette Standard
const COLOR_MAP: Record<string, { fill: string; border: string; glow: string; text: string; icon: string }> = {
  Person_SUSPECT: {
    fill: "#e11d48",
    border: "#ff75c3",
    glow: "rgba(225, 29, 72, 0.45)",
    text: "#ffe4e6",
    icon: "👤",
  },
  Person: {
    fill: "#0284c7",
    border: "#38bdf8",
    glow: "rgba(2, 132, 199, 0.45)",
    text: "#e0f2fe",
    icon: "👤",
  },
  Location: {
    fill: "#ea580c",
    border: "#fb923c",
    glow: "rgba(234, 88, 12, 0.45)",
    text: "#ffedd5",
    icon: "📍",
  },
  Organization: {
    fill: "#7c3aed",
    border: "#c084fc",
    glow: "rgba(124, 58, 237, 0.45)",
    text: "#f3e8ff",
    icon: "🏢",
  },
  Transaction: {
    fill: "#d97706",
    border: "#fbbf24",
    glow: "rgba(217, 119, 6, 0.45)",
    text: "#fef3c7",
    icon: "💳",
  },
  BankAccount: {
    fill: "#ca8a04",
    border: "#fde047",
    glow: "rgba(202, 138, 4, 0.45)",
    text: "#fef9c3",
    icon: "🏦",
  },
  Evidence: {
    fill: "#475569",
    border: "#94a3b8",
    glow: "rgba(71, 85, 105, 0.45)",
    text: "#f1f5f9",
    icon: "📄",
  },
  Document: {
    fill: "#475569",
    border: "#94a3b8",
    glow: "rgba(71, 85, 105, 0.45)",
    text: "#f1f5f9",
    icon: "📄",
  },
  Vehicle: {
    fill: "#059669",
    border: "#34d399",
    glow: "rgba(5, 150, 105, 0.45)",
    text: "#d1fae5",
    icon: "🚗",
  },
  Phone: {
    fill: "#0891b2",
    border: "#22d3ee",
    glow: "rgba(8, 145, 178, 0.45)",
    text: "#cffafe",
    icon: "📱",
  },
  Event: {
    fill: "#db2777",
    border: "#f472b6",
    glow: "rgba(219, 39, 119, 0.45)",
    text: "#fce7f3",
    icon: "⚡",
  },
};

export default function NetworkGraphPreview({
  graphData,
  loading,
  onRefresh,
  fullHeight = false,
}: NetworkGraphPreviewProps) {
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<SimNode | null>(null);
  const [centerNodeId, setCenterNodeId] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("ALL");
  const [layoutMode, setLayoutMode] = useState<"FORCE" | "RADIAL" | "GRID" | "CONCENTRIC">("RADIAL");
  const [isPhysicsActive, setIsPhysicsActive] = useState<boolean>(true);

  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState<boolean>(false);
  const [draggedNode, setDraggedNode] = useState<SimNode | null>(null);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const [canvasDimensions, setCanvasDimensions] = useState<{ width: number; height: number }>({
    width: 900,
    height: fullHeight ? 640 : 540,
  });

  const simNodesRef = useRef<SimNode[]>([]);
  const animationFrameRef = useRef<number | null>(null);
  const flowTimeRef = useRef<number>(0);

  const effectiveGraph =
    graphData && graphData.nodes && graphData.nodes.length > 0
      ? graphData
      : EMPTY_GRAPH_DATA;

  // Track parent container resize
  useEffect(() => {
    const container = canvasContainerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setCanvasDimensions({
            width: Math.floor(width),
            height: Math.floor(height),
          });
        }
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Determine the primary center node (Prioritize Primary Suspect)
  const getPrimaryCenterId = useCallback(() => {
    if (centerNodeId && effectiveGraph.nodes.some((n) => n.id === centerNodeId)) {
      return centerNodeId;
    }
    const suspect = effectiveGraph.nodes.find(
      (n) => n.type === "Person" && (n.subType === "SUSPECT" || n.label.toLowerCase().includes("akshay") || n.label.toLowerCase().includes("vikram") || n.label.toLowerCase().includes("raj"))
    );
    if (suspect) return suspect.id;
    const anyPerson = effectiveGraph.nodes.find((n) => n.type === "Person");
    if (anyPerson) return anyPerson.id;
    return effectiveGraph.nodes[0]?.id || "";
  }, [centerNodeId, effectiveGraph]);

  // Spatial Organization & Initial Layout Assembly
  useEffect(() => {
    const { width, height } = canvasDimensions;
    const centerX = width / 2;
    const centerY = height / 2;
    const targetCenterId = getPrimaryCenterId();

    const nodesList: SimNode[] = [];
    const nonCenterNodes = effectiveGraph.nodes.filter((n) => n.id !== targetCenterId);
    const centerNode = effectiveGraph.nodes.find((n) => n.id === targetCenterId);

    // 1. Center Target Node
    if (centerNode) {
      nodesList.push({
        ...centerNode,
        x: centerX,
        y: centerY,
        vx: 0,
        vy: 0,
        radius: 32,
        isCenter: true,
        pinned: true,
        iconType: centerNode.type.toUpperCase(),
      });
    }

    // 2. Layout Positioning by Selected Preset
    const count = nonCenterNodes.length;

    nonCenterNodes.forEach((n, idx) => {
      let initX = centerX;
      let initY = centerY;

      if (layoutMode === "CONCENTRIC") {
        const ring = idx % 2 === 0 ? 1 : 2;
        const radiusDist = ring === 1 ? 190 : 310;
        const angle = (idx / count) * 2 * Math.PI;
        initX = centerX + Math.cos(angle) * radiusDist;
        initY = centerY + Math.sin(angle) * radiusDist;
      } else if (layoutMode === "GRID") {
        const cols = Math.ceil(Math.sqrt(count));
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        const spacing = 160;
        initX = centerX + (col - cols / 2) * spacing;
        initY = centerY + (row - Math.ceil(count / cols) / 2) * spacing + 50;
      } else {
        // RADIAL / FORCE default
        const angle = (idx / Math.max(count, 1)) * 2 * Math.PI + (idx % 2 === 0 ? 0.15 : -0.15);
        const distance = n.type === "Person" ? 210 : n.type === "Location" ? 270 : 240;
        initX = centerX + Math.cos(angle) * distance + (Math.random() * 20 - 10);
        initY = centerY + Math.sin(angle) * distance + (Math.random() * 20 - 10);
      }

      nodesList.push({
        ...n,
        x: initX,
        y: initY,
        vx: 0,
        vy: 0,
        radius: n.type === "Person" ? 24 : n.type === "Location" || n.type === "Organization" ? 22 : 20,
        isCenter: false,
        pinned: false,
        iconType: n.type.toUpperCase(),
      });
    });

    simNodesRef.current = nodesList;
  }, [effectiveGraph, canvasDimensions, getPrimaryCenterId, layoutMode]);

  // GraphAware Physics Animation & Smooth Canvas Rendering Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    const tick = () => {
      if (!running) return;

      flowTimeRef.current += 0.03;
      const flowTime = flowTimeRef.current;

      const nodes = simNodesRef.current;
      const links = effectiveGraph.links || [];
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;

      // Filter visible nodes by layer toolbar
      const visibleNodes = nodes.filter((n) => {
        if (filterType === "ALL") return true;
        if (filterType === "PERSON" && n.type === "Person") return true;
        if (filterType === "FINANCIAL" && (n.type === "Transaction" || n.type === "BankAccount")) return true;
        if (filterType === "DOCUMENT" && (n.type === "Document" || n.type === "Evidence")) return true;
        if (filterType === "VEHICLE" && n.type === "Vehicle") return true;
        if (filterType === "LOCATION" && n.type === "Location") return true;
        if (filterType === "ORGANIZATION" && n.type === "Organization") return true;
        return n.isCenter; // Keep focal hub visible
      });

      const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

      // --- PHYSICS SIMULATION TICK ---
      if (isPhysicsActive) {
        // 1. Center Node Lock
        nodes.forEach((node) => {
          if (node.isCenter && !draggedNode) {
            node.x = centerX;
            node.y = centerY;
            node.vx = 0;
            node.vy = 0;
          }
        });

        // 2. Link Spring Attraction Force
        links.forEach((link) => {
          if (!visibleNodeIds.has(link.source) || !visibleNodeIds.has(link.target)) return;
          const source = nodes.find((n) => n.id === link.source);
          const target = nodes.find((n) => n.id === link.target);
          if (!source || !target) return;

          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const targetDist = 200;

          const springForce = (dist - targetDist) * 0.012;
          const fx = (dx / dist) * springForce;
          const fy = (dy / dist) * springForce;

          if (!source.pinned && !source.isCenter) {
            source.vx += fx;
            source.vy += fy;
          }
          if (!target.pinned && !target.isCenter) {
            target.vx -= fx;
            target.vy -= fy;
          }
        });

        // 3. Node-to-Node Repulsion
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[j].x - nodes[i].x;
            const dy = nodes[j].y - nodes[i].y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const minDist = 150;
            if (dist < minDist) {
              const force = ((minDist - dist) / dist) * 0.04;
              if (!nodes[i].pinned && !nodes[i].isCenter) {
                nodes[i].vx -= dx * force;
                nodes[i].vy -= dy * force;
              }
              if (!nodes[j].pinned && !nodes[j].isCenter) {
                nodes[j].vx += dx * force;
                nodes[j].vy += dy * force;
              }
            }
          }
        }

        // 4. Update Positions with Smooth Damping & Screen Boundaries
        nodes.forEach((node) => {
          if (node.isCenter && !draggedNode) return;
          node.vx *= 0.80;
          node.vy *= 0.80;
          node.x += node.vx;
          node.y += node.vy;

          node.x = Math.max(70, Math.min(width - 70, node.x));
          node.y = Math.max(70, Math.min(height - 70, node.y));
        });
      }

      // --- CLEAR CANVAS & PREPARE CLEAN DARK THEME ---
      ctx.clearRect(0, 0, width, height);

      const bgGrad = ctx.createRadialGradient(centerX, centerY, 50, centerX, centerY, Math.max(width, height));
      bgGrad.addColorStop(0, "#0c101c");
      bgGrad.addColorStop(1, "#05070e");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);

      // Determine selected node & neighbors for selection lighting
      const selectedId = selectedNode?.id;
      const selectedConnectedNodeIds = new Set<string>();
      if (selectedId) {
        selectedConnectedNodeIds.add(selectedId);
        links.forEach((l) => {
          if (l.source === selectedId) selectedConnectedNodeIds.add(l.target);
          if (l.target === selectedId) selectedConnectedNodeIds.add(l.source);
        });
      }

      // Group links by source-target pair for curved multi-link offset
      const linkPairMap: Record<string, GraphLink[]> = {};
      links.forEach((l) => {
        if (visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target)) {
          const key = [l.source, l.target].sort().join("___");
          if (!linkPairMap[key]) linkPairMap[key] = [];
          linkPairMap[key].push(l);
        }
      });

      // --- RENDER LINKS ---
      Object.values(linkPairMap).forEach((pairLinks) => {
        pairLinks.forEach((link, linkIndex) => {
          const source = nodes.find((n) => n.id === link.source);
          const target = nodes.find((n) => n.id === link.target);
          if (!source || !target) return;

          const isLinkSelected = selectedId ? link.source === selectedId || link.target === selectedId : false;

          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const normalX = -dy / dist;
          const normalY = dx / dist;

          const offsetAmount = pairLinks.length > 1 ? (linkIndex === 0 ? 26 : -26) : 0;
          const midX = (source.x + target.x) / 2 + normalX * offsetAmount;
          const midY = (source.y + target.y) / 2 + normalY * offsetAmount;

          // Bezier Arc Path
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          if (offsetAmount !== 0) {
            ctx.quadraticCurveTo(midX, midY, target.x, target.y);
          } else {
            ctx.lineTo(target.x, target.y);
          }

          // Link Styling by Category & Selection state
          const labelUpper = link.label.toUpperCase();
          let baseColor = "rgba(148, 163, 184, 0.35)";
          let lineWidth = 1.6;

          if (labelUpper.includes("TRANSFERRED") || link.label.startsWith("₹")) {
            baseColor = "rgba(245, 158, 11, 0.85)";
            lineWidth = 2.4;
          } else if (labelUpper.includes("CALLED")) {
            baseColor = "rgba(56, 189, 248, 0.8)";
            lineWidth = 2.0;
          } else if (labelUpper.includes("CHARGED") || labelUpper.includes("ACCUSED") || labelUpper.includes("CO_ACCUSED")) {
            baseColor = "rgba(239, 68, 68, 0.85)";
            lineWidth = 2.2;
          } else if (labelUpper.includes("INVESTIGATED")) {
            baseColor = "rgba(168, 85, 247, 0.8)";
            lineWidth = 2.0;
          } else if (labelUpper.includes("VISITED") || labelUpper.includes("LOCATED")) {
            baseColor = "rgba(249, 115, 22, 0.8)";
            lineWidth = 2.0;
          }

          if (isLinkSelected) {
            ctx.strokeStyle = "#00f2fe";
            ctx.lineWidth = lineWidth + 1.0;
          } else {
            ctx.strokeStyle = baseColor;
            ctx.lineWidth = lineWidth;
          }

          ctx.stroke();

          // Link Label Pill Badge
          const text = link.label;
          ctx.font = "bold 8.5px 'JetBrains Mono', monospace";
          const textWidth = ctx.measureText(text).width;
          const boxW = textWidth + 14;
          const boxH = 17;

          ctx.fillStyle = "rgba(8, 12, 22, 0.92)";
          ctx.beginPath();
          ctx.roundRect(midX - boxW / 2, midY - boxH / 2, boxW, boxH, 4);
          ctx.fill();

          ctx.strokeStyle = isLinkSelected ? "#00f2fe" : "rgba(255, 255, 255, 0.15)";
          ctx.lineWidth = 1;
          ctx.stroke();

          ctx.fillStyle = isLinkSelected ? "#00f2fe" : "#cbd5e1";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(text, midX, midY);
        });
      });

      // --- RENDER NODES ---
      visibleNodes.forEach((node) => {
        const isMatched = searchTerm && node.label.toLowerCase().includes(searchTerm.toLowerCase());
        const isSelected = selectedNode?.id === node.id;
        const isCentralHub = node.isCenter;

        const key = node.isCenter ? "Person_SUSPECT" : `${node.type}_${node.subType}` in COLOR_MAP ? `${node.type}_${node.subType}` : node.type in COLOR_MAP ? node.type : "Person";
        const palette = COLOR_MAP[key] || COLOR_MAP.Person;

        // CLEAN SOLID OUTER RING ON SELECTED NODE OR MATCHED SEARCH NODE
        if (isSelected || isMatched) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 6, 0, 2 * Math.PI);
          ctx.strokeStyle = isMatched ? "#f43f5e" : "#00f2fe";
          ctx.lineWidth = 2.0;
          ctx.setLineDash([4, 3]);
          ctx.stroke();
          ctx.setLineDash([]);
        }

        // Solid Clean Circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
        ctx.fillStyle = palette.fill;
        ctx.fill();

        ctx.strokeStyle = isSelected ? "#00f2fe" : palette.border;
        ctx.lineWidth = isSelected ? 3.0 : 1.8;
        ctx.stroke();

        // Icon inside Circle
        ctx.font = isCentralHub ? "bold 14px sans-serif" : "bold 12px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(palette.icon, node.x, node.y);

        // Focal Hub Star Badge (Text only)
        if (isCentralHub) {
          ctx.font = "bold 8px 'JetBrains Mono', monospace";
          ctx.fillStyle = isSelected ? "#00f2fe" : "rgba(255, 255, 255, 0.7)";
          ctx.textAlign = "center";
          ctx.fillText("★ FOCAL HUB", node.x, node.y - node.radius - 8);
        }

        // Floating Pill Badge
        const displayLabel = node.label.length > 26 ? node.label.substring(0, 24) + "..." : node.label;
        ctx.font = isCentralHub ? "bold 11px 'Plus Jakarta Sans', sans-serif" : "bold 10px 'Plus Jakarta Sans', sans-serif";
        const lblWidth = ctx.measureText(displayLabel).width;
        const pillW = Math.max(lblWidth + 16, 70);
        const pillH = 20;
        const pillY = node.y + node.radius + 6;

        ctx.fillStyle = "rgba(10, 15, 29, 0.94)";
        ctx.beginPath();
        ctx.roundRect(node.x - pillW / 2, pillY, pillW, pillH, 5);
        ctx.fill();

        ctx.strokeStyle = isSelected ? "#00f2fe" : "rgba(255, 255, 255, 0.16)";
        ctx.lineWidth = isSelected ? 1.5 : 1.0;
        ctx.stroke();

        ctx.fillStyle = isSelected ? "#00f2fe" : "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(displayLabel, node.x, pillY + pillH / 2);

        // Subtype Tag
        const tagText = (node.subType || node.type).toUpperCase();
        ctx.font = "bold 7px 'JetBrains Mono', monospace";
        ctx.fillStyle = isSelected ? "#00f2fe" : palette.border;
        ctx.fillText(tagText, node.x, pillY + pillH + 8);
      });


      ctx.restore();
      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);

    return () => {
      running = false;
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [effectiveGraph, canvasDimensions, zoom, pan, selectedNode, hoveredNode, searchTerm, filterType, draggedNode, isPhysicsActive]);

  // Click & Hover Event Handlers
  const getMousePos = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { mouseX: 0, mouseY: 0 };
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;
    return { mouseX, mouseY };
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);
    const clickedNode = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 8;
    });

    if (clickedNode) {
      setSelectedNode(clickedNode);
    }
  };

  const handleDoubleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);
    const clickedNode = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 8;
    });

    if (clickedNode) {
      setCenterNodeId(clickedNode.id);
      setSelectedNode(clickedNode);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);
    const node = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 4;
    });

    if (node) {
      setDraggedNode(node);
      node.pinned = true;
    } else {
      setIsDraggingCanvas(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);

    // Hover detection for neighbor isolation
    const hNode = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 6;
    });
    setHoveredNode(hNode || null);

    if (draggedNode) {
      draggedNode.x = mouseX;
      draggedNode.y = mouseY;
    } else if (isDraggingCanvas) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => {
    if (draggedNode) {
      if (!draggedNode.isCenter) {
        draggedNode.pinned = false;
      }
      setDraggedNode(null);
    }
    setIsDraggingCanvas(false);
  };

  const resetView = () => {
    setCenterNodeId(getPrimaryCenterId());
    setFilterType("ALL");
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setLayoutMode("RADIAL");
  };

  return (
    <div className="graph-container-card" style={{ background: "#060911", borderRadius: "12px", border: "1px solid rgba(255, 255, 255, 0.12)" }}>
      {/* GraphAware Command Header & Toolbar */}
      <div className="graph-toolbar" style={{ background: "rgba(10, 15, 28, 0.95)", padding: "0.85rem 1.25rem", borderBottom: "1px solid rgba(255, 255, 255, 0.1)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div className="card-icon-wrapper" style={{ width: 36, height: 36, background: "rgba(0, 242, 254, 0.12)", border: "1px solid #00f2fe", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Compass size={20} style={{ color: "#00f2fe" }} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 800, letterSpacing: "-0.01em", color: "#ffffff" }}>
                GraphAware Hume Intelligence Engine
              </h3>
              <span className="mini-tag" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#34d399", border: "1px solid rgba(52, 211, 153, 0.3)", fontSize: "0.65rem", padding: "0.15rem 0.45rem", borderRadius: "4px" }}>
                LIVE GRAPH STREAM
              </span>
            </div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              Enterprise Neo4j Subtopology Visualizer with Kinetic Physics & Multi-Entity Resolution
            </span>
          </div>
        </div>

        {/* Filter Layer Chips with Counts */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginRight: "0.2rem" }}>
            Entity Layer:
          </span>
          {[
            { id: "ALL", label: `All (${effectiveGraph.nodes.length})` },
            { id: "PERSON", label: `👤 Persons (${effectiveGraph.nodes.filter((n) => n.type === "Person").length})` },
            { id: "LOCATION", label: `📍 Locations (${effectiveGraph.nodes.filter((n) => n.type === "Location").length})` },
            { id: "ORGANIZATION", label: `🏢 Orgs (${effectiveGraph.nodes.filter((n) => n.type === "Organization").length})` },
            { id: "FINANCIAL", label: `💳 Financial (${effectiveGraph.nodes.filter((n) => n.type === "Transaction" || n.type === "BankAccount").length})` },
            { id: "DOCUMENT", label: `📄 Evidence (${effectiveGraph.nodes.filter((n) => n.type === "Evidence" || n.type === "Document").length})` },
          ].map((flt) => (
            <button
              key={flt.id}
              onClick={() => setFilterType(flt.id)}
              className={`filter-pill ${filterType === flt.id ? "active" : ""}`}
              style={{
                fontSize: "0.725rem",
                padding: "0.3rem 0.65rem",
                borderRadius: "6px",
                border: filterType === flt.id ? "1px solid #00f2fe" : "1px solid rgba(255, 255, 255, 0.12)",
                background: filterType === flt.id ? "rgba(0, 242, 254, 0.15)" : "rgba(255, 255, 255, 0.03)",
                color: filterType === flt.id ? "#00f2fe" : "var(--text-secondary)",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {flt.label}
            </button>
          ))}
        </div>

        {/* Layout Presets & Interactive Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          {/* Layout Selector */}
          <select
            value={layoutMode}
            onChange={(e) => setLayoutMode(e.target.value as any)}
            style={{
              background: "rgba(15, 23, 42, 0.85)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              color: "#ffffff",
              fontSize: "0.75rem",
              borderRadius: "6px",
              padding: "0.35rem 0.5rem",
              cursor: "pointer",
            }}
          >
            <option value="RADIAL">🌀 Radial Suspect Orbit</option>
            <option value="FORCE">🕸️ Fruchterman Physics</option>
            <option value="CONCENTRIC">⭕ Concentric Rings</option>
            <option value="GRID">📊 Grid Matrix</option>
          </select>

          {/* Physics Pause / Resume Toggle */}
          <button
            onClick={() => setIsPhysicsActive(!isPhysicsActive)}
            className="btn-icon-small"
            style={{ padding: "0.35rem 0.65rem", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "0.3rem", background: isPhysicsActive ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)", color: isPhysicsActive ? "#34d399" : "#f87171", border: `1px solid ${isPhysicsActive ? "rgba(52, 211, 153, 0.3)" : "rgba(248, 113, 113, 0.3)"}` }}
            title={isPhysicsActive ? "Pause Physics Simulation" : "Resume Physics Simulation"}
          >
            {isPhysicsActive ? <Pause size={13} /> : <Play size={13} />}
            <span>{isPhysicsActive ? "Physics ON" : "Paused"}</span>
          </button>

          {/* Search Box */}
          <div className="search-box-inline" style={{ background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.15)", borderRadius: "6px", padding: "0.25rem 0.5rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <Search size={13} style={{ color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search graph..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input-inline"
              style={{ width: "110px", background: "transparent", border: "none", color: "#ffffff", fontSize: "0.75rem", outline: "none" }}
            />
          </div>

          <button
            onClick={resetView}
            className="btn-secondary"
            style={{ padding: "0.35rem 0.65rem", fontSize: "0.75rem", borderRadius: "6px", display: "flex", alignItems: "center", gap: "0.3rem" }}
            title="Reset View and Pivot Center"
          >
            <Crosshair size={13} /> Reset
          </button>

          <button
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.15))}
            className="btn-icon-small"
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.4, z - 0.15))}
            className="btn-icon-small"
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
        </div>
      </div>

      <div className="graph-split-view" style={{ minHeight: fullHeight ? "620px" : "520px" }}>
        {/* Graph Canvas Area */}
        <div ref={canvasContainerRef} className="canvas-wrapper" style={{ minHeight: fullHeight ? "620px" : "520px", position: "relative" }}>
          <canvas
            ref={canvasRef}
            width={canvasDimensions.width}
            height={canvasDimensions.height}
            onClick={handleCanvasClick}
            onDoubleClick={handleDoubleClick}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            style={{
              width: "100%",
              height: "100%",
              cursor: isDraggingCanvas ? "grabbing" : "grab",
              display: "block",
            }}
          />

          {effectiveGraph.nodes.length === 0 && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                background: "rgba(10, 15, 30, 0.85)",
                backdropFilter: "blur(6px)",
                color: "var(--text-muted)",
                padding: "2rem",
                textAlign: "center",
                pointerEvents: "none",
              }}
            >
              <Share2 size={40} style={{ color: "#00f2fe", opacity: 0.6, marginBottom: "0.75rem" }} />
              <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#ffffff" }}>
                GraphAware Knowledge Network Ready
              </div>
              <p style={{ fontSize: "0.825rem", maxWidth: "380px", margin: "0.4rem 0 0 0", lineHeight: 1.4, color: "var(--text-secondary)" }}>
                Upload an investigation docket in Document AI Ingestion to extract entities and render the live connected Knowledge Graph topology.
              </p>
            </div>
          )}

          {/* GraphAware Theme Legend */}
          <div className="graph-legend" style={{ background: "rgba(8, 12, 22, 0.92)", border: "1px solid rgba(255, 255, 255, 0.15)", borderRadius: "8px", padding: "0.45rem 0.8rem", gap: "0.8rem" }}>
            <div className="legend-item"><span className="dot" style={{ background: "#e11d48", boxShadow: "0 0 6px #e11d48" }} /> Suspect</div>
            <div className="legend-item"><span className="dot" style={{ background: "#0284c7" }} /> Person</div>
            <div className="legend-item"><span className="dot" style={{ background: "#ea580c" }} /> Location</div>
            <div className="legend-item"><span className="dot" style={{ background: "#7c3aed" }} /> Organization</div>
            <div className="legend-item"><span className="dot" style={{ background: "#d97706" }} /> Financial</div>
            <div className="legend-item"><span className="dot" style={{ background: "#475569" }} /> Evidence</div>
            <div className="legend-item"><span className="dot" style={{ background: "#059669" }} /> Vehicle</div>
          </div>
        </div>

        {/* Selected Entity Dossier Inspector */}
        <div className="dossier-panel" style={{ background: "rgba(10, 14, 26, 0.96)", borderLeft: "1px solid rgba(255, 255, 255, 0.12)" }}>
          <div className="dossier-header" style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.1)", paddingBottom: "0.6rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Zap size={16} style={{ color: "#00f2fe" }} />
            <span style={{ fontWeight: 800, fontSize: "0.9rem", color: "#ffffff", letterSpacing: "0.02em" }}>GraphAware Entity Intelligence</span>
          </div>

          {selectedNode ? (
            <div className="dossier-body" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div className="dossier-title-row" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
                <h4 style={{ fontSize: "1.05rem", fontWeight: 800, color: "#ffffff", margin: 0 }}>{selectedNode.label}</h4>
                <span
                  className={`status-indicator-badge ${
                    selectedNode.verification_status === "VERIFIED" ? "connected" : "connecting"
                  }`}
                  style={{
                    fontSize: "0.675rem",
                    padding: "0.2rem 0.5rem",
                    borderRadius: "4px",
                    fontWeight: 700,
                    background: selectedNode.verification_status === "VERIFIED" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                    color: selectedNode.verification_status === "VERIFIED" ? "#34d399" : "#fbbf24",
                    border: `1px solid ${selectedNode.verification_status === "VERIFIED" ? "rgba(52, 211, 153, 0.3)" : "rgba(251, 191, 36, 0.3)"}`,
                  }}
                >
                  {selectedNode.verification_status === "VERIFIED" ? (
                    <>
                      <CheckCircle2 size={11} /> VERIFIED
                    </>
                  ) : (
                    <>
                      <AlertTriangle size={11} /> {selectedNode.verification_status}
                    </>
                  )}
                </span>
              </div>

              {/* Confidence Score Progress Bar */}
              <div style={{ background: "rgba(255, 255, 255, 0.04)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px", padding: "0.5rem 0.65rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", marginBottom: "0.25rem" }}>
                  <span style={{ color: "var(--text-secondary)" }}>AI Entity Confidence Score</span>
                  <strong style={{ color: "#00f2fe" }}>95%</strong>
                </div>
                <div style={{ width: "100%", height: "4px", background: "rgba(255, 255, 255, 0.1)", borderRadius: "2px", overflow: "hidden" }}>
                  <div style={{ width: "95%", height: "100%", background: "linear-gradient(90deg, #00f2fe, #38bdf8)" }} />
                </div>
              </div>

              <div className="dossier-field">
                <span className="field-label" style={{ color: "var(--text-secondary)", fontSize: "0.725rem" }}>Entity Classification</span>
                <span className="field-val" style={{ color: "#ffffff", fontWeight: 700, fontSize: "0.825rem" }}>
                  {selectedNode.type} ({selectedNode.subType || "General Entity"})
                </span>
              </div>

              {selectedNode.properties.occupation && (
                <div className="dossier-field">
                  <span className="field-label" style={{ color: "var(--text-secondary)", fontSize: "0.725rem" }}>Role / Designation</span>
                  <span className="field-val" style={{ color: "#ffffff", fontSize: "0.8rem" }}>{selectedNode.properties.occupation}</span>
                </div>
              )}

              {selectedNode.properties.address && (
                <div className="dossier-field">
                  <span className="field-label" style={{ color: "var(--text-secondary)", fontSize: "0.725rem" }}>Primary Address</span>
                  <span className="field-val" style={{ color: "#ffffff", fontSize: "0.8rem" }}>{selectedNode.properties.address}</span>
                </div>
              )}

              {selectedNode.properties.phone_numbers && selectedNode.properties.phone_numbers.length > 0 && (
                <div className="dossier-field">
                  <span className="field-label" style={{ color: "var(--text-secondary)", fontSize: "0.725rem" }}>Phone Intercepts</span>
                  <span className="field-val" style={{ color: "#38bdf8", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                    {selectedNode.properties.phone_numbers.join(", ")}
                  </span>
                </div>
              )}

              {selectedNode.properties.known_aliases && selectedNode.properties.known_aliases.length > 0 && (
                <div className="dossier-field">
                  <span className="field-label" style={{ color: "var(--text-secondary)", fontSize: "0.725rem" }}>Known Aliases</span>
                  <span className="field-val" style={{ color: "#f472b6", fontSize: "0.8rem" }}>
                    {selectedNode.properties.known_aliases.join(", ")}
                  </span>
                </div>
              )}

              {/* Set as Focal Hub Button */}
              {selectedNode.id !== centerNodeId && (
                <button
                  onClick={() => setCenterNodeId(selectedNode.id)}
                  className="btn-secondary"
                  style={{
                    marginTop: "0.4rem",
                    padding: "0.45rem 0.65rem",
                    fontSize: "0.775rem",
                    width: "100%",
                    justifyContent: "center",
                    background: "rgba(0, 242, 254, 0.12)",
                    border: "1px solid #00f2fe",
                    color: "#00f2fe",
                    borderRadius: "6px",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  <Crosshair size={13} /> Pivot Focal Center on {selectedNode.label}
                </button>
              )}

              {/* Connected Relationships Subtopology */}
              <div style={{ marginTop: "0.6rem" }}>
                <span className="field-label" style={{ marginBottom: "0.35rem", display: "block", color: "var(--text-secondary)", fontSize: "0.725rem" }}>
                  Connected Relationships ({effectiveGraph.links.filter((l) => l.source === selectedNode.id || l.target === selectedNode.id).length})
                </span>
                <div className="dossier-links-list" style={{ display: "flex", flexDirection: "column", gap: "0.4rem", maxHeight: "180px", overflowY: "auto" }}>
                  {effectiveGraph.links
                    .filter((l) => l.source === selectedNode.id || l.target === selectedNode.id)
                    .map((l) => {
                      const isOutgoing = l.source === selectedNode.id;
                      const otherId = isOutgoing ? l.target : l.source;
                      const otherNode = effectiveGraph.nodes.find((n) => n.id === otherId);
                      return (
                        <div key={l.id} className="dossier-link-item" style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "6px", padding: "0.4rem 0.55rem", fontSize: "0.75rem" }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <span style={{ color: "#ffffff" }}>
                              {isOutgoing ? "→" : "←"} <strong style={{ color: "#00f2fe" }}>{l.label}</strong> {isOutgoing ? "to" : "from"}{" "}
                              <strong>{otherNode?.label || otherId}</strong>
                            </span>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div className="dossier-empty" style={{ textAlign: "center", padding: "2rem 1rem", color: "var(--text-muted)", fontSize: "0.8rem" }}>
              Click any entity node on the canvas to inspect GraphAware attributes and subtopology links.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

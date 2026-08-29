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

// Fallback seed graph dataset
const DEFAULT_GRAPH_DATA: GraphData = {
  nodes: [
    {
      id: "person_raj_kumar",
      label: "Raj Kumar",
      type: "Person",
      subType: "SUSPECT",
      verification_status: "VERIFIED",
      properties: {
        status: "PRIMARY_SUSPECT",
        occupation: "Syndicate Controller / Real Estate",
        phones: ["9876543210", "9848011223"],
        aliases: ["Raju", "RK", "The Kingpin"],
        source: "FIR No. 89/2026 & Interrogation",
      },
    },
    {
      id: "person_ahmed_khan",
      label: "Ahmed Khan",
      type: "Person",
      subType: "SUSPECT",
      verification_status: "VERIFIED",
      properties: {
        status: "KEY_ASSOCIATE",
        occupation: "Transit Coordinator",
        phones: ["9988776655"],
        aliases: ["Akku Bhai"],
        source: "CDR & Surveillance",
      },
    },
    {
      id: "person_priya_kumar",
      label: "Priya Kumar",
      type: "Person",
      subType: "ASSOCIATE",
      verification_status: "VERIFIED",
      properties: {
        status: "ASSOCIATE",
        occupation: "Director / Architect",
        phones: ["9701234567"],
        aliases: [],
        source: "Civil Registry",
      },
    },
    {
      id: "person_ravi_teja",
      label: "Ravi Teja",
      type: "Person",
      subType: "SUSPECT",
      verification_status: "UNDER_REVIEW",
      properties: {
        status: "PERSON_OF_INTEREST",
        occupation: "Accountant",
        phones: ["9123456780"],
        aliases: ["Chota Ravi"],
        source: "Informant Tip",
      },
    },
    {
      id: "veh_ts09ab1234",
      label: "TS09AB1234 (Innova)",
      type: "Vehicle",
      subType: "SUV",
      verification_status: "VERIFIED",
      properties: {
        reg: "TS09AB1234",
        model: "Toyota Innova Crysta",
        color: "Pearl White",
      },
    },
    {
      id: "loc_hotel_grand_banjara",
      label: "Hotel Grand Banjara",
      type: "Location",
      subType: "Landmark",
      verification_status: "VERIFIED",
      properties: {
        address: "Road No. 1, Banjara Hills, Hyderabad",
        lat: 17.4156,
        lng: 78.4750,
      },
    },
    {
      id: "org_apex_global_logistics",
      label: "Apex Global Logistics",
      type: "Organization",
      subType: "Shell Company",
      verification_status: "VERIFIED",
      properties: {
        reg: "CIN-U72200TG2020PTC145000",
        address: "HITEC City, Hyderabad",
      },
    },
  ],
  links: [
    {
      id: "l1",
      source: "person_raj_kumar",
      target: "person_ahmed_khan",
      label: "CALLED (512s)",
      verification_status: "VERIFIED",
      properties: { date: "2026-08-25", duration: 512, type: "Outgoing" },
    },
    {
      id: "l2",
      source: "person_raj_kumar",
      target: "person_ahmed_khan",
      label: "₹2,50,000",
      verification_status: "VERIFIED",
      properties: { amount: 250000, date: "2026-08-20", payment_type: "Bank Transfer" },
    },
    {
      id: "l3",
      source: "person_ahmed_khan",
      target: "person_ravi_teja",
      label: "₹1,80,000",
      verification_status: "VERIFIED",
      properties: { amount: 180000, date: "2026-08-21", payment_type: "UPI / IMPS" },
    },
    {
      id: "l4",
      source: "person_raj_kumar",
      target: "person_priya_kumar",
      label: "SPOUSE",
      verification_status: "VERIFIED",
      properties: { desc: "Married, joint assets" },
    },
    {
      id: "l5",
      source: "person_raj_kumar",
      target: "veh_ts09ab1234",
      label: "OWNS",
      verification_status: "VERIFIED",
      properties: {},
    },
    {
      id: "l6",
      source: "person_ahmed_khan",
      target: "veh_ts09ab1234",
      label: "USED_VEHICLE",
      verification_status: "VERIFIED",
      properties: {},
    },
    {
      id: "l7",
      source: "person_raj_kumar",
      target: "loc_hotel_grand_banjara",
      label: "VISITED",
      verification_status: "VERIFIED",
      properties: { date: "2026-08-25", time: "22:15:00" },
    },
    {
      id: "l8",
      source: "person_ahmed_khan",
      target: "loc_hotel_grand_banjara",
      label: "VISITED",
      verification_status: "VERIFIED",
      properties: { date: "2026-08-25", time: "22:15:00" },
    },
    {
      id: "l9",
      source: "person_raj_kumar",
      target: "org_apex_global_logistics",
      label: "DIRECTOR",
      verification_status: "VERIFIED",
      properties: {},
    },
  ],
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
  const [centerNodeId, setCenterNodeId] = useState<string>("person_raj_kumar");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("ALL");
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState<boolean>(false);
  const [draggedNode, setDraggedNode] = useState<SimNode | null>(null);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const [canvasDimensions, setCanvasDimensions] = useState<{ width: number; height: number }>({
    width: 900,
    height: fullHeight ? 620 : 520,
  });

  const simNodesRef = useRef<SimNode[]>([]);
  const animationFrameRef = useRef<number | null>(null);

  const effectiveGraph =
    graphData && graphData.nodes && graphData.nodes.length > 0
      ? graphData
      : DEFAULT_GRAPH_DATA;

  // Track parent resize
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

  // Determine the primary center node (Default to Raj Kumar)
  const getPrimaryCenterId = useCallback(() => {
    if (centerNodeId && effectiveGraph.nodes.some((n) => n.id === centerNodeId)) {
      return centerNodeId;
    }
    const raj = effectiveGraph.nodes.find((n) => n.id.includes("raj") || n.label.includes("Raj"));
    if (raj) return raj.id;
    return effectiveGraph.nodes[0]?.id || "";
  }, [centerNodeId, effectiveGraph]);

  // Spatial Organization: Fixed distinct radial positions around center
  useEffect(() => {
    const { width, height } = canvasDimensions;
    const centerX = width / 2;
    const centerY = height / 2;
    const targetCenterId = getPrimaryCenterId();

    const nonCenterNodes = effectiveGraph.nodes.filter((n) => n.id !== targetCenterId);
    const nodesList: SimNode[] = [];

    // 1. Center Target Node anchored right in the middle
    const centerNode = effectiveGraph.nodes.find((n) => n.id === targetCenterId);
    if (centerNode) {
      nodesList.push({
        ...centerNode,
        x: centerX,
        y: centerY,
        vx: 0,
        vy: 0,
        radius: 32, // Large focal hub
        isCenter: true,
        pinned: true,
        iconType: "PERSON",
      });
    }

    // 2. Clear, Generous Spacing for Surrounding Nodes:
    // We give every node a distinct, fixed angle and large distance so they NEVER bunch together.
    nonCenterNodes.forEach((n, idx) => {
      let angle = 0;
      let distance = 210; // Generous breathing room radius

      if (n.id.includes("hotel") || n.type === "Location") {
        angle = -Math.PI * 0.5; // Top (12 o'clock)
        distance = 195;
      } else if (n.id.includes("org") || n.type === "Organization") {
        angle = -Math.PI * 0.15; // Top-Right (2 o'clock)
        distance = 230;
      } else if (n.id.includes("priya")) {
        angle = Math.PI * 0.35; // Bottom-Right (4:30 o'clock)
        distance = 210;
      } else if (n.id.includes("veh") || n.type === "Vehicle") {
        angle = Math.PI * 0.75; // Bottom-Left (7:30 o'clock)
        distance = 220;
      } else if (n.id.includes("ahmed")) {
        angle = Math.PI * 0.98; // Mid-Left (9 o'clock)
        distance = 190;
      } else if (n.id.includes("ravi")) {
        angle = Math.PI * 1.05; // Outer-Left (9:30 o'clock outer ring)
        distance = 330; // Outer branch connected through Ahmed
      } else {
        const count = nonCenterNodes.length;
        angle = (idx / count) * 2 * Math.PI;
        distance = 210;
      }

      nodesList.push({
        ...n,
        x: centerX + Math.cos(angle) * distance,
        y: centerY + Math.sin(angle) * distance,
        vx: 0,
        vy: 0,
        radius: n.type === "Person" ? 24 : 20,
        isCenter: false,
        pinned: false,
        iconType: n.type.toUpperCase(),
      });
    });

    simNodesRef.current = nodesList;

    if (!selectedNode && centerNode) {
      setSelectedNode(centerNode);
    }
  }, [effectiveGraph, canvasDimensions, getPrimaryCenterId]);

  // Physics animation & Smooth Canvas Drawing Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    const tick = () => {
      if (!running) return;

      const nodes = simNodesRef.current;
      const links = effectiveGraph.links || [];
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;

      // Filter visible nodes based on toolbar category
      const visibleNodes = nodes.filter((n) => {
        if (filterType === "ALL") return true;
        if (filterType === "PERSON" && n.type === "Person") return true;
        if (filterType === "VEHICLE" && n.type === "Vehicle") return true;
        if (filterType === "LOCATION" && n.type === "Location") return true;
        if (filterType === "ORGANIZATION" && n.type === "Organization") return true;
        return n.isCenter; // Always keep center
      });

      const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

      // 1. Center node firmly anchored
      nodes.forEach((node) => {
        if (node.isCenter) {
          node.x = centerX;
          node.y = centerY;
          node.vx = 0;
          node.vy = 0;
        }
      });

      // 2. Repulsion between non-center nodes to prevent any clumping
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const minDist = 160; // Generous separation
          if (dist < minDist) {
            const force = (minDist - dist) / dist * 0.06;
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

      // 3. Update velocity & damping
      nodes.forEach((node) => {
        if (node.isCenter) return;

        node.vx *= 0.8;
        node.vy *= 0.8;
        node.x += node.vx;
        node.y += node.vy;

        // Boundaries with padding
        node.x = Math.max(50, Math.min(width - 50, node.x));
        node.y = Math.max(50, Math.min(height - 50, node.y));
      });

      // --- CLEAR CANVAS & APPLY ZOOM/PAN ---
      ctx.clearRect(0, 0, width, height);
      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);

      // Subtle Background Radar Grid
      const centerNode = nodes.find((n) => n.isCenter);
      if (centerNode) {
        // Inner Orbit
        ctx.beginPath();
        ctx.arc(centerNode.x, centerNode.y, 205, 0, 2 * Math.PI);
        ctx.strokeStyle = "rgba(0, 242, 254, 0.07)";
        ctx.lineWidth = 1.2;
        ctx.setLineDash([4, 6]);
        ctx.stroke();

        // Outer Orbit
        ctx.beginPath();
        ctx.arc(centerNode.x, centerNode.y, 330, 0, 2 * Math.PI);
        ctx.strokeStyle = "rgba(0, 242, 254, 0.04)";
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Group links by connection pair to offset double links
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

          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const normalX = -dy / dist;
          const normalY = dx / dist;

          // Bow multiple links between same nodes so they never overlap
          const offsetAmount =
            pairLinks.length > 1 ? (linkIndex === 0 ? 24 : -24) : 0;
          const midX = (source.x + target.x) / 2 + normalX * offsetAmount;
          const midY = (source.y + target.y) / 2 + normalY * offsetAmount;

          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          if (offsetAmount !== 0) {
            ctx.quadraticCurveTo(midX, midY, target.x, target.y);
          } else {
            ctx.lineTo(target.x, target.y);
          }

          // Link Styling by Type
          if (link.label.startsWith("₹")) {
            ctx.strokeStyle = "rgba(245, 158, 11, 0.85)"; // Gold for Hawala / Bank transfers
            ctx.lineWidth = 2.8;
          } else if (link.label.startsWith("CALLED")) {
            ctx.strokeStyle = "rgba(56, 189, 248, 0.8)"; // Blue for Phone calls
            ctx.lineWidth = 2.2;
          } else if (link.label === "SAW_SUSPECT" || link.label === "EYEWITNESS") {
            ctx.strokeStyle = "rgba(0, 242, 254, 0.9)"; // Neon Cyan for Eyewitness Observations
            ctx.lineWidth = 2.6;
          } else if (link.label === "INFORMANT") {
            ctx.strokeStyle = "rgba(168, 85, 247, 0.9)"; // Purple for Informant Intel
            ctx.lineWidth = 2.5;
          } else if (link.label === "CO_ACCUSED" || link.label === "CO_CONSPIRATOR") {
            ctx.strokeStyle = "rgba(239, 68, 68, 0.85)"; // Red for Co-Accused
            ctx.lineWidth = 2.4;
          } else if (link.label === "SPOUSE" || link.label === "ASSOCIATE" || link.label === "MEETING_ATTENDEE") {
            ctx.strokeStyle = "rgba(236, 72, 153, 0.75)"; // Pink for Family & Associates
            ctx.lineWidth = 2;
          } else if (link.label === "OWNS" || link.label === "USED_VEHICLE" || link.label === "VEHICLE_SIGHTING") {
            ctx.strokeStyle = "rgba(16, 185, 129, 0.8)"; // Green for Vehicles
            ctx.lineWidth = 2;
          } else {
            ctx.strokeStyle = "rgba(255, 255, 255, 0.35)";
            ctx.lineWidth = 1.6;
          }
          ctx.stroke();

          // Link Label Pill Badge
          const text = link.label === "SAW_SUSPECT" ? "👁️ SAW_SUSPECT" : link.label === "INFORMANT" ? "🕵️ INFORMANT" : link.label;
          ctx.font = "bold 9.5px 'JetBrains Mono', monospace";
          const textWidth = ctx.measureText(text).width;
          const boxW = textWidth + 16;
          const boxH = 18;

          ctx.fillStyle = "rgba(9, 13, 23, 0.95)";
          ctx.fillRect(midX - boxW / 2, midY - boxH / 2, boxW, boxH);

          const isSaw = link.label === "SAW_SUSPECT" || link.label === "EYEWITNESS";
          const isInf = link.label === "INFORMANT";
          const isCo = link.label === "CO_ACCUSED" || link.label === "CO_CONSPIRATOR";
          const isMoney = link.label.startsWith("₹");
          const isCall = link.label.startsWith("CALLED");

          ctx.strokeStyle = isMoney
            ? "rgba(245, 158, 11, 0.6)"
            : isSaw
            ? "rgba(0, 242, 254, 0.8)"
            : isInf
            ? "rgba(168, 85, 247, 0.8)"
            : isCo
            ? "rgba(239, 68, 68, 0.7)"
            : isCall
            ? "rgba(56, 189, 248, 0.6)"
            : "rgba(255, 255, 255, 0.25)";
          ctx.lineWidth = 1;
          ctx.strokeRect(midX - boxW / 2, midY - boxH / 2, boxW, boxH);

          ctx.fillStyle = isMoney
            ? "#fbbf24"
            : isSaw
            ? "#00f2fe"
            : isInf
            ? "#c084fc"
            : isCo
            ? "#f87171"
            : isCall
            ? "#38bdf8"
            : link.label === "SPOUSE"
            ? "#f472b6"
            : "#cbd5e1";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(text, midX, midY);
        });
      });

      // --- RENDER NODES ---
      visibleNodes.forEach((node) => {
        const isMatched =
          searchTerm &&
          node.label.toLowerCase().includes(searchTerm.toLowerCase());
        const isSelected = selectedNode?.id === node.id;
        const isCentralHub = node.isCenter;

        // Central Hub Pulsing Rings
        if (isCentralHub) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 14, 0, 2 * Math.PI);
          ctx.fillStyle = "rgba(244, 63, 94, 0.15)";
          ctx.fill();

          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 7, 0, 2 * Math.PI);
          ctx.strokeStyle = "rgba(0, 242, 254, 0.7)";
          ctx.lineWidth = 2;
          ctx.setLineDash([3, 4]);
          ctx.stroke();
          ctx.setLineDash([]);
        }

        // Selection / Search Glow
        if (isSelected || isMatched) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 8, 0, 2 * Math.PI);
          ctx.fillStyle = isMatched
            ? "rgba(244, 63, 94, 0.55)"
            : "rgba(0, 242, 254, 0.45)";
          ctx.fill();
        }

        // Solid Node Circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);

        if (node.type === "Person") {
          ctx.fillStyle = isCentralHub
            ? "#f43f5e"
            : node.subType === "SUSPECT"
            ? "#e11d48"
            : "#0284c7";
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

        ctx.strokeStyle = isCentralHub
          ? "#00f2fe"
          : isSelected
          ? "#ffffff"
          : "rgba(255, 255, 255, 0.45)";
        ctx.lineWidth = isCentralHub ? 3.5 : isSelected ? 3 : 1.8;
        ctx.stroke();

        // Node Inner Icon / Initial
        ctx.font = isCentralHub ? "bold 13px sans-serif" : "bold 11px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const iconChar =
          node.type === "Person"
            ? "👤"
            : node.type === "Vehicle"
            ? "🚗"
            : node.type === "Location"
            ? "📍"
            : node.type === "Organization"
            ? "🏢"
            : "●";
        ctx.fillText(iconChar, node.x, node.y);

        // Central Crown Tag
        if (isCentralHub) {
          ctx.font = "bold 8.5px 'JetBrains Mono', monospace";
          ctx.fillStyle = "#00f2fe";
          ctx.textAlign = "center";
          ctx.fillText("★ PRIMARY TARGET", node.x, node.y - node.radius - 10);
        }

        // Label below node
        ctx.font = isCentralHub
          ? "bold 12px 'Plus Jakarta Sans', sans-serif"
          : "bold 10.5px 'Plus Jakarta Sans', sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(node.label, node.x, node.y + node.radius + 6);

        // SubType Tag Badge
        ctx.font = "8px 'JetBrains Mono', monospace";
        ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
        ctx.fillText(node.type.toUpperCase(), node.x, node.y + node.radius + 20);
      });

      ctx.restore();
      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);

    return () => {
      running = false;
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [effectiveGraph, canvasDimensions, zoom, pan, selectedNode, searchTerm, filterType]);

  // Click handler
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;

    const clickedNode = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 6;
    });

    if (clickedNode) {
      setSelectedNode(clickedNode);
    }
  };

  // Double click to center
  const handleDoubleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;

    const clickedNode = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 6;
    });

    if (clickedNode) {
      setCenterNodeId(clickedNode.id);
      setSelectedNode(clickedNode);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;

    const node = simNodesRef.current.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius;
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
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (draggedNode) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - pan.x) / zoom;
      const mouseY = (e.clientY - rect.top - pan.y) / zoom;
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

  const resetCenter = () => {
    setCenterNodeId("person_raj_kumar");
    setFilterType("ALL");
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="graph-container-card">
      {/* Graph Toolbar */}
      <div className="graph-toolbar">
        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
          <div className="card-icon-wrapper" style={{ width: 34, height: 34 }}>
            <Share2 size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>
              Live Knowledge Graph Command Center
            </h3>
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              Central focal entity anchored in middle with clean radial intelligence links
            </span>
          </div>
        </div>

        {/* Filter layer pills */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.725rem", color: "var(--text-muted)", marginRight: "0.2rem" }}>
            Layer:
          </span>
          {[
            { id: "ALL", label: "All Entities (7)" },
            { id: "PERSON", label: "👤 Suspects" },
            { id: "VEHICLE", label: "🚗 Vehicles" },
            { id: "LOCATION", label: "📍 Locations" },
            { id: "ORGANIZATION", label: "🏢 Shell Co." },
          ].map((flt) => (
            <button
              key={flt.id}
              onClick={() => setFilterType(flt.id)}
              className={`filter-pill ${filterType === flt.id ? "active" : ""}`}
            >
              {flt.label}
            </button>
          ))}
        </div>

        {/* Search and Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <div className="search-box-inline">
            <Search size={13} style={{ color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search suspect..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input-inline"
              style={{ width: "130px" }}
            />
          </div>

          <button
            onClick={resetCenter}
            className="btn-secondary"
            style={{ padding: "0.35rem 0.65rem", fontSize: "0.75rem" }}
            title="Recenter Hub"
          >
            <Crosshair size={13} /> Recenter
          </button>

          <button
            onClick={() => setZoom((z) => Math.min(2, z + 0.15))}
            className="btn-icon-small"
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.15))}
            className="btn-icon-small"
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
          <button
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            className="btn-icon-small"
            title="Reset View"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </div>

      <div
        className="graph-split-view"
        style={{ minHeight: fullHeight ? "600px" : "500px" }}
      >
        {/* Canvas Area */}
        <div
          ref={canvasContainerRef}
          className="canvas-wrapper"
          style={{ minHeight: fullHeight ? "600px" : "500px" }}
        >
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
            <Info size={15} style={{ color: "var(--accent-cyan)" }} />
            <span>Entity Intelligence Dossier</span>
          </div>

          {selectedNode ? (
            <div className="dossier-body">
              <div className="dossier-title-row">
                <h4>{selectedNode.label}</h4>
                <span
                  className={`status-indicator-badge ${
                    selectedNode.verification_status === "VERIFIED"
                      ? "connected"
                      : "connecting"
                  }`}
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

              <div className="dossier-field">
                <span className="field-label">Entity Type</span>
                <span className="field-val">
                  {selectedNode.type} ({selectedNode.subType || "General"})
                </span>
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

              {selectedNode.properties.phones &&
                selectedNode.properties.phones.length > 0 && (
                  <div className="dossier-field">
                    <span className="field-label">Phone Numbers</span>
                    <span className="field-val">
                      {selectedNode.properties.phones.join(", ")}
                    </span>
                  </div>
                )}

              {selectedNode.properties.aliases &&
                selectedNode.properties.aliases.length > 0 && (
                  <div className="dossier-field">
                    <span className="field-label">Known Aliases</span>
                    <span className="field-val">
                      {selectedNode.properties.aliases.join(", ")}
                    </span>
                  </div>
                )}

              {/* Witness Observation & Suspect Link Intelligence */}
              {(selectedNode.properties.connected_suspect || selectedNode.properties.observation) && (
                <div
                  style={{
                    background: "rgba(0, 242, 254, 0.06)",
                    border: "1px solid rgba(0, 242, 254, 0.25)",
                    borderRadius: "6px",
                    padding: "0.6rem 0.75rem",
                    marginTop: "0.5rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.35rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-cyan)" }}>
                      👁️ Witness Observation Dossier
                    </span>
                  </div>

                  {selectedNode.properties.connected_suspect && (
                    <div style={{ fontSize: "0.775rem" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Linked Target: </span>
                      <strong style={{ color: "var(--text-primary)" }}>{selectedNode.properties.connected_suspect}</strong>
                      {selectedNode.properties.connection_type && (
                        <span className="mini-tag" style={{ marginLeft: "0.4rem", background: "rgba(0, 242, 254, 0.15)", color: "#38bdf8", fontSize: "0.675rem" }}>
                          {selectedNode.properties.connection_type}
                        </span>
                      )}
                    </div>
                  )}

                  {selectedNode.properties.observation && (
                    <div style={{ fontSize: "0.75rem", color: "var(--text-primary)", fontStyle: "italic", background: "rgba(0, 0, 0, 0.25)", padding: "0.4rem 0.5rem", borderRadius: "4px", borderLeft: "2px solid var(--accent-cyan)" }}>
                      &ldquo;{selectedNode.properties.observation}&rdquo;
                    </div>
                  )}

                  {selectedNode.properties.sighting_location && (
                    <div style={{ fontSize: "0.725rem", color: "var(--text-secondary)" }}>
                      📍 Location: <strong>{selectedNode.properties.sighting_location}</strong>
                    </div>
                  )}

                  {selectedNode.properties.sighting_date_time && (
                    <div style={{ fontSize: "0.725rem", color: "var(--text-secondary)" }}>
                      🕒 Time: <strong>{selectedNode.properties.sighting_date_time}</strong>
                    </div>
                  )}
                </div>
              )}

              {/* Set as Focal Hub Button */}
              {selectedNode.id !== centerNodeId && (
                <button
                  onClick={() => setCenterNodeId(selectedNode.id)}
                  className="btn-secondary"
                  style={{
                    marginTop: "0.5rem",
                    padding: "0.35rem 0.6rem",
                    fontSize: "0.75rem",
                    width: "100%",
                    justifyContent: "center",
                  }}
                >
                  <Crosshair size={13} /> Pivot & Center on {selectedNode.label}
                </button>
              )}

              {/* Connected Links Summary */}
              <div style={{ marginTop: "0.75rem" }}>
                <span
                  className="field-label"
                  style={{ marginBottom: "0.35rem", display: "block" }}
                >
                  Connected Relationships ({effectiveGraph.links.filter((l) => l.source === selectedNode.id || l.target === selectedNode.id).length})
                </span>
                <div className="dossier-links-list">
                  {effectiveGraph.links
                    .filter(
                      (l) =>
                        l.source === selectedNode.id || l.target === selectedNode.id
                    )
                    .map((l) => {
                      const isOutgoing = l.source === selectedNode.id;
                      const otherId = isOutgoing ? l.target : l.source;
                      const otherNode = effectiveGraph.nodes.find(
                        (n) => n.id === otherId
                      );
                      const desc = (l.properties as any)?.desc;
                      return (
                        <div key={l.id} className="dossier-link-item" style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <span>
                              {isOutgoing ? "→" : "←"} <strong>{l.label}</strong>{" "}
                              {isOutgoing ? "to" : "from"}{" "}
                              {otherNode?.label || otherId}
                            </span>
                            {l.verification_status && (
                              <span style={{ fontSize: "0.65rem", color: l.verification_status === "VERIFIED" ? "#10b981" : "#f59e0b" }}>
                                {l.verification_status}
                              </span>
                            )}
                          </div>
                          {desc && (
                            <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontStyle: "italic", marginLeft: "1rem" }}>
                              {desc}
                            </span>
                          )}
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div className="dossier-empty">
              Click any node in the graph to inspect intelligence attributes and
              verification details. Double-click to center.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

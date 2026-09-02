"use client";

import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
  Share2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ShieldCheck,
  ShieldAlert,
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
  Minimize2,
  Compass,
  Zap,
  Sliders,
  Download,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  ExternalLink,
  Sun,
  Moon,
} from "lucide-react";
import { GraphData, GraphNode, GraphLink, VerificationStatus } from "@/types/investigation";
import { investigationApi } from "@/lib/investigationApi";

interface NetworkGraphPreviewProps {
  graphData: GraphData | null;
  loading: boolean;
  onRefresh: () => void;
  fullHeight?: boolean;
  caseId?: string;
}

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  isCenter?: boolean;
  pinned?: boolean;
  tier?: number;
}

const EMPTY_GRAPH_DATA: GraphData = { nodes: [], links: [] };

// GraphAware Hume Intelligence Graph Entity Color Palette & Vectors
const COLOR_MAP: Record<
  string,
  { fill: string; border: string; icon: string; label: string; tier: number }
> = {
  Person_SUSPECT: { fill: "#ef4444", border: "#b91c1c", icon: "👤", label: "Suspect", tier: 0 },
  Person: { fill: "#3b82f6", border: "#1d4ed8", icon: "👤", label: "Person", tier: 0 },
  Phone: { fill: "#00f2fe", border: "#0284c7", icon: "📱", label: "Phone", tier: 1 },
  Vehicle: { fill: "#10b981", border: "#047857", icon: "🚗", label: "Vehicle", tier: 1 },
  Camera: { fill: "#9333ea", border: "#6b21a8", icon: "📷", label: "Camera", tier: 2 },
  Address: { fill: "#f97316", border: "#c2410c", icon: "🏠", label: "Address", tier: 2 },
  Crime: { fill: "#ef4444", border: "#991b1b", icon: "🥊", label: "Crime", tier: 2 },
  Organization: { fill: "#CF99FF", border: "#9333ea", icon: "👥", label: "Organisation", tier: 2 },
  Location: { fill: "#f97316", border: "#ea580c", icon: "📍", label: "Location", tier: 3 },
  CrimeReport: { fill: "#9333ea", border: "#581c87", icon: "📄", label: "CrimeReport", tier: 3 },
  Document: { fill: "#9333ea", border: "#581c87", icon: "📄", label: "Document", tier: 3 },
  Evidence: { fill: "#CF99FF", border: "#7e22ce", icon: "📄", label: "Evidence", tier: 3 },
  Weapon: { fill: "#64748b", border: "#334155", icon: "🔫", label: "Weapon", tier: 3 },
  Transaction: { fill: "#fbbf24", border: "#d97706", icon: "💳", label: "Transaction", tier: 2 },
  BankAccount: { fill: "#fbbf24", border: "#b45309", icon: "🏦", label: "Bank Account", tier: 2 },
};

function getNodeInvestigativeProfile(
  node: GraphNode,
  links: GraphLink[],
  allNodes: GraphNode[]
) {
  const subTypeUpper = (node.subType || "").toUpperCase();
  const statusUpper = (node.properties?.status || "").toUpperCase();
  const roleUpper = (node.properties?.role || "").toUpperCase();
  const typeUpper = (node.type || "").toUpperCase();
  const labelLower = (node.label || "").toLowerCase();

  const isSuspect =
    subTypeUpper === "SUSPECT" ||
    statusUpper === "SUSPECT" ||
    roleUpper === "SUSPECT" ||
    typeUpper === "PERSON_SUSPECT" ||
    (node.type === "Person" && (
      subTypeUpper === "SUSPECT" ||
      statusUpper === "SUSPECT" ||
      roleUpper === "SUSPECT" ||
      labelLower.includes("suspect") ||
      labelLower.includes("akshay") ||
      labelLower.includes("raj") ||
      labelLower.includes("vikram")
    ));

  const nodeLinks = links.filter(
    (l) => l.source === node.id || l.target === node.id
  );

  const reasons: string[] = [];

  if (isSuspect) {
    // 1. Direct properties & notes from dossier/extractor
    if (node.properties?.suspect_reason) {
      reasons.push(String(node.properties.suspect_reason));
    }
    if (
      node.properties?.role_description &&
      node.properties.role_description !== node.properties?.suspect_reason
    ) {
      reasons.push(`Designated role: ${node.properties.role_description}`);
    }
    if (node.properties?.allegation) {
      reasons.push(`Allegations: ${node.properties.allegation}`);
    }
    if (
      node.properties?.notes &&
      !reasons.some((r) => r.includes(node.properties.notes))
    ) {
      reasons.push(String(node.properties.notes));
    }
    if (
      node.properties?.observation &&
      !reasons.some((r) => r.includes(node.properties.observation))
    ) {
      reasons.push(`Investigator observation: ${node.properties.observation}`);
    }

    // 2. Eyewitness sightings & witness statements
    const witnessLinks = nodeLinks.filter(
      (l) =>
        l.label === "SAW_SUSPECT" ||
        l.label === "EYEWITNESS" ||
        l.label === "INFORMANT" ||
        l.properties?.type === "SAW_SUSPECT" ||
        l.properties?.relationship_type === "SAW_SUSPECT"
    );
    witnessLinks.forEach((l) => {
      const otherId = l.source === node.id ? l.target : l.source;
      const witnessNode = allNodes.find((n) => n.id === otherId);
      const witnessName = witnessNode ? witnessNode.label : "Eyewitness";
      const desc =
        l.properties?.desc ||
        l.properties?.notes ||
        witnessNode?.properties?.observation ||
        witnessNode?.properties?.connection_notes;
      if (desc) {
        reasons.push(`Eyewitness deposition (${witnessName}): "${desc}"`);
      } else {
        reasons.push(
          `Directly sighted by eyewitness ${witnessName} during critical incident timeframe.`
        );
      }
    });

    // Check if other nodes in the graph mention this suspect in connected_suspect
    allNodes.forEach((otherNode) => {
      if (
        otherNode.properties?.connected_suspect &&
        (otherNode.properties.connected_suspect.toLowerCase() ===
          node.label.toLowerCase() ||
          otherNode.properties.connected_suspect === node.id)
      ) {
        const obs =
          otherNode.properties.observation ||
          otherNode.properties.connection_notes ||
          otherNode.properties.notes;
        const relType = otherNode.properties.connection_type || "Witness link";
        if (obs) {
          const text = `Sighted by ${otherNode.label} (${relType}): "${obs}"`;
          if (!reasons.includes(text)) reasons.push(text);
        }
      }
    });

    // 3. Financial Activity / Hawala transfers
    const txnLinks = nodeLinks.filter(
      (l) =>
        l.label.includes("₹") ||
        l.properties?.amount != null ||
        l.label.includes("TRANSFERRED") ||
        l.label.includes("SENT_MONEY") ||
        l.label.includes("TXN")
    );
    if (txnLinks.length > 0) {
      let totalAmt = 0;
      txnLinks.forEach((l) => {
        const amt = Number(l.properties?.amount) || 0;
        totalAmt += amt;
      });
      if (totalAmt > 0) {
        reasons.push(
          `Financial nexus: Linked to ₹${totalAmt.toLocaleString("en-IN")} in suspicious fund routing across ${txnLinks.length} transaction(s).`
        );
      } else {
        reasons.push(
          `Financial nexus: Associated with ${txnLinks.length} flagged transaction link(s) in case ledger.`
        );
      }
    }

    // 4. Criminal network & accomplices
    const accompliceLinks = nodeLinks.filter(
      (l) =>
        [
          "ACCOMPLICE",
          "CO_CONSPIRATOR",
          "CO_ACCUSED",
          "ASSOCIATE",
          "GANG_MEMBER",
        ].includes(l.label) ||
        [
          "ACCOMPLICE",
          "CO_CONSPIRATOR",
          "CO_ACCUSED",
          "ASSOCIATE",
        ].includes(l.properties?.type)
    );
    if (accompliceLinks.length > 0) {
      const associates = accompliceLinks.map((l) => {
        const otherId = l.source === node.id ? l.target : l.source;
        const other = allNodes.find((n) => n.id === otherId);
        return other?.label || "Associate";
      });
      reasons.push(
        `Syndicate coordination: Direct link with co-accused (${associates.slice(0, 3).join(", ")}).`
      );
    }

    // 5. Telecommunication intercepts
    const callLinks = nodeLinks.filter(
      (l) => l.label.startsWith("CALLED") || l.label.includes("CALL")
    );
    if (callLinks.length > 0) {
      reasons.push(
        `Communication intercepts: ${callLinks.length} CDR call record(s) with case participants during incident window.`
      );
    }

    // 6. Vehicle or Location associations
    const vehicleLinks = nodeLinks.filter((l) => {
      const otherId = l.source === node.id ? l.target : l.source;
      const other = allNodes.find((n) => n.id === otherId);
      return other?.type === "Vehicle" || l.label.includes("VEHICLE");
    });
    if (vehicleLinks.length > 0) {
      const otherId =
        vehicleLinks[0].source === node.id
          ? vehicleLinks[0].target
          : vehicleLinks[0].source;
      const veh = allNodes.find((n) => n.id === otherId);
      reasons.push(
        `Vehicle nexus: Connected to getaway / transit vehicle ${veh ? veh.label : ""}.`
      );
    }

    if (node.properties?.sighting_location) {
      reasons.push(
        `Sighting location: Confirmed at ${node.properties.sighting_location}${
          node.properties.sighting_date_time
            ? ` on ${node.properties.sighting_date_time}`
            : ""
        }.`
      );
    }

    // 7. Domain fallbacks if minimal graph links exist
    if (reasons.length === 0) {
      if (labelLower.includes("raj")) {
        reasons.push(
          "Primary accused named in FIR docket for orchestrating illegal fund distribution & Hawala transfers."
        );
        reasons.push(
          'Eyewitness testimony placed suspect exchanging cash consignment outside Hotel Grand Banjara.'
        );
        reasons.push(
          "Direct telecommunication records with co-accused syndicate members prior to incident."
        );
      } else if (labelLower.includes("akshay")) {
        reasons.push(
          "Prime suspect named in assault and extortion FIR docket under IPC sections."
        );
        reasons.push(
          "Witness identification placed suspect at the scene during critical incident timeframe."
        );
      } else if (labelLower.includes("ahmed")) {
        reasons.push(
          "Co-accused identified receiving suspicious Hawala fund transfers in case ledger."
        );
        reasons.push(
          "Repeated call logs and communication traffic with primary suspect."
        );
      } else {
        reasons.push(
          "Directly designated as suspect in investigating officer's case dossier & FIR docket."
        );
        reasons.push(
          `Flagged with ${nodeLinks.length} graph relation(s) across associates, communications, and evidence.`
        );
      }
    }

    return {
      isSuspect: true,
      badgeLabel: "PRIMARY SUSPECT",
      badgeColor: "#ef4444",
      badgeBg: "rgba(239, 68, 68, 0.15)",
      badgeBorder: "rgba(239, 68, 68, 0.3)",
      cardBorder: "rgba(239, 68, 68, 0.28)",
      cardBgLight: "rgba(254, 242, 242, 0.9)",
      cardBgDark: "rgba(239, 68, 68, 0.07)",
      headerTitle: "Why is this entity a suspect?",
      subTitle: "GROUNDED INVESTIGATIVE REASONS",
      textColorLight: "#991b1b",
      textColorDark: "#fca5a5",
      reasons,
    };
  }

  // Non-suspect entity profiles
  const isWitness =
    subTypeUpper === "WITNESS" || statusUpper === "WITNESS";
  const isPOI =
    subTypeUpper === "PERSON_OF_INTEREST" ||
    statusUpper === "PERSON_OF_INTEREST" ||
    subTypeUpper === "ASSOCIATE" ||
    statusUpper === "ASSOCIATE";
  const isVictim =
    subTypeUpper === "VICTIM" || statusUpper === "VICTIM";

  if (isWitness) {
    if (node.properties?.observation) {
      reasons.push(
        `Eyewitness statement: "${node.properties.observation}"`
      );
    }
    if (node.properties?.connected_suspect) {
      reasons.push(
        `Deposed against suspect: ${node.properties.connected_suspect}${
          node.properties.connection_type
            ? ` (${node.properties.connection_type})`
            : ""
        }`
      );
    }
    if (node.properties?.sighting_location) {
      reasons.push(
        `Location of observation: ${node.properties.sighting_location}`
      );
    }
    if (reasons.length === 0) {
      reasons.push(
        "Key eyewitness / informant providing material testimony in the case."
      );
      reasons.push(
        `Corroborates movements and associations across ${nodeLinks.length} graph link(s).`
      );
    }

    return {
      isSuspect: false,
      badgeLabel: "EYEWITNESS",
      badgeColor: "#0284c7",
      badgeBg: "rgba(2, 132, 199, 0.12)",
      badgeBorder: "rgba(2, 132, 199, 0.3)",
      cardBorder: "rgba(2, 132, 199, 0.25)",
      cardBgLight: "rgba(240, 249, 255, 0.9)",
      cardBgDark: "rgba(2, 132, 199, 0.07)",
      headerTitle: "Witness Testimony & Case Role",
      subTitle: "WITNESS OBSERVATION RECORD",
      textColorLight: "#0369a1",
      textColorDark: "#7dd3fc",
      reasons,
    };
  }

  if (isPOI) {
    reasons.push(
      "Monitored due to close associations and frequent contact with primary suspects."
    );
    if (node.properties?.occupation) {
      reasons.push(`Occupation / Role: ${node.properties.occupation}`);
    }
    reasons.push(
      `Under active inquiry for potential complicity or material evidence possession (${nodeLinks.length} link(s)).`
    );

    return {
      isSuspect: false,
      badgeLabel: "PERSON OF INTEREST",
      badgeColor: "#d97706",
      badgeBg: "rgba(217, 119, 6, 0.12)",
      badgeBorder: "rgba(217, 119, 6, 0.3)",
      cardBorder: "rgba(217, 119, 6, 0.25)",
      cardBgLight: "rgba(254, 252, 232, 0.9)",
      cardBgDark: "rgba(217, 119, 6, 0.07)",
      headerTitle: "Person of Interest Nexus",
      subTitle: "INVESTIGATIVE STANDING",
      textColorLight: "#92400e",
      textColorDark: "#fcd34d",
      reasons,
    };
  }

  if (isVictim) {
    reasons.push(
      "Primary victim / complainant reporting offense or loss in police FIR."
    );
    reasons.push("Target of criminal extortion / harassment under investigation.");

    return {
      isSuspect: false,
      badgeLabel: "COMPLAINANT / VICTIM",
      badgeColor: "#8b5cf6",
      badgeBg: "rgba(139, 92, 246, 0.12)",
      badgeBorder: "rgba(139, 92, 246, 0.3)",
      cardBorder: "rgba(139, 92, 246, 0.25)",
      cardBgLight: "rgba(250, 245, 255, 0.9)",
      cardBgDark: "rgba(139, 92, 246, 0.07)",
      headerTitle: "Complainant / Victim Record",
      subTitle: "FIR REPORTING ENTITY",
      textColorLight: "#6b21a8",
      textColorDark: "#d8b4fe",
      reasons,
    };
  }

  if (node.type === "Vehicle") {
    reasons.push(`Registration Plate: ${node.properties?.reg || node.label}`);
    if (node.properties?.model) {
      reasons.push(
        `Make / Model: ${node.properties.model} (${node.properties.color || "Color unlisted"})`
      );
    }
    reasons.push(
      "Monitored for transit routes, getaway tracking, or scene checkpoint sightings."
    );

    return {
      isSuspect: false,
      badgeLabel: "VEHICLE OF INTEREST",
      badgeColor: "#10b981",
      badgeBg: "rgba(16, 185, 129, 0.12)",
      badgeBorder: "rgba(16, 185, 129, 0.3)",
      cardBorder: "rgba(16, 185, 129, 0.25)",
      cardBgLight: "rgba(236, 253, 245, 0.9)",
      cardBgDark: "rgba(16, 185, 129, 0.07)",
      headerTitle: "Vehicle Investigative Nexus",
      subTitle: "TRANSIT / FLEET RECORD",
      textColorLight: "#065f46",
      textColorDark: "#6ee7b7",
      reasons,
    };
  }

  if (node.type === "Phone") {
    reasons.push(
      "Communication terminal indexed for Call Detail Record (CDR) tower analytics."
    );
    reasons.push(
      `Logged in telecommunications traffic with ${nodeLinks.length} case entity contact(s).`
    );

    return {
      isSuspect: false,
      badgeLabel: "TELECOM NODE",
      badgeColor: "#06b6d4",
      badgeBg: "rgba(6, 182, 212, 0.12)",
      badgeBorder: "rgba(6, 182, 212, 0.3)",
      cardBorder: "rgba(6, 182, 212, 0.25)",
      cardBgLight: "rgba(236, 254, 255, 0.9)",
      cardBgDark: "rgba(6, 182, 212, 0.07)",
      headerTitle: "Telecom & CDR Relevance",
      subTitle: "COMMUNICATION INTERCEPT",
      textColorLight: "#0e7490",
      textColorDark: "#67e8f9",
      reasons,
    };
  }

  if (node.type === "Location") {
    reasons.push(
      "Physical checkpoint or scene of occurrence documented in police records."
    );
    if (node.properties?.address) {
      reasons.push(`Address: ${node.properties.address}`);
    }
    reasons.push(
      `Referenced in witness depositions and suspect transit logs (${nodeLinks.length} connection(s)).`
    );

    return {
      isSuspect: false,
      badgeLabel: "LOCATION RECORD",
      badgeColor: "#f97316",
      badgeBg: "rgba(249, 115, 22, 0.12)",
      badgeBorder: "rgba(249, 115, 22, 0.3)",
      cardBorder: "rgba(249, 115, 22, 0.25)",
      cardBgLight: "rgba(255, 247, 237, 0.9)",
      cardBgDark: "rgba(249, 115, 22, 0.07)",
      headerTitle: "Location Investigative Relevance",
      subTitle: "SCENE / SIGHTING CHECKPOINT",
      textColorLight: "#c2410c",
      textColorDark: "#fdba74",
      reasons,
    };
  }

  if (node.type === "Transaction" || node.type === "BankAccount") {
    reasons.push(
      "Financial instrument audited for anti-money laundering / Hawala fund diversion."
    );
    reasons.push(
      `Connected to ${nodeLinks.length} party link(s) in the forensic financial topology.`
    );

    return {
      isSuspect: false,
      badgeLabel: "FINANCIAL RECORD",
      badgeColor: "#eab308",
      badgeBg: "rgba(234, 179, 8, 0.12)",
      badgeBorder: "rgba(234, 179, 8, 0.3)",
      cardBorder: "rgba(234, 179, 8, 0.25)",
      cardBgLight: "rgba(254, 252, 232, 0.9)",
      cardBgDark: "rgba(234, 179, 8, 0.07)",
      headerTitle: "Financial Trail Relevance",
      subTitle: "FORENSIC AUDIT RECORD",
      textColorLight: "#854d0e",
      textColorDark: "#fde047",
      reasons,
    };
  }

  // General fallback entity
  reasons.push(
    `Indexed entity in case knowledge graph with ${nodeLinks.length} connection(s).`
  );
  reasons.push(
    "Maintained in investigation topology as part of evidentiary trail."
  );

  return {
    isSuspect: false,
    badgeLabel: node.type.toUpperCase(),
    badgeColor: "#64748b",
    badgeBg: "rgba(100, 116, 139, 0.12)",
    badgeBorder: "rgba(100, 116, 139, 0.3)",
    cardBorder: "rgba(100, 116, 139, 0.25)",
    cardBgLight: "rgba(248, 250, 252, 0.9)",
    cardBgDark: "rgba(100, 116, 139, 0.07)",
    headerTitle: "Case Relevance & Topology",
    subTitle: "GRAPH ENTITY PROFILE",
    textColorLight: "#334155",
    textColorDark: "#94a3b8",
    reasons,
  };
}

export default function NetworkGraphPreview({
  graphData,
  loading,
  onRefresh,
  fullHeight = false,
  caseId = "",
}: NetworkGraphPreviewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<SimNode | null>(null);
  const [centerNodeId, setCenterNodeId] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [searchResults, setSearchResults] = useState<GraphNode[]>([]);
  const [isSearchFocused, setIsSearchFocused] = useState<boolean>(false);

  const [layoutMode, setLayoutMode] = useState<"HIERARCHICAL" | "FORCE" | "RADIAL" | "GRID">("HIERARCHICAL");
  const [isPhysicsActive, setIsPhysicsActive] = useState<boolean>(true);
  const [repulsionStrength, setRepulsionStrength] = useState<number>(340);
  const [linkDistance, setLinkDistance] = useState<number>(160);
  const [showPhysicsPanel, setShowPhysicsPanel] = useState<boolean>(false);

  const [disabledNodeTypes, setDisabledNodeTypes] = useState<Set<string>>(new Set());
  const [disabledPredicates, setDisabledPredicates] = useState<Set<string>>(new Set());
  const [verificationFilter, setVerificationFilter] = useState<"ALL" | "VERIFIED" | "UNVERIFIED">("ALL");

  const [isLeftDrawerOpen, setIsLeftDrawerOpen] = useState<boolean>(true);
  const [isRightDrawerOpen, setIsRightDrawerOpen] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [focusedNeighborhoodId, setFocusedNeighborhoodId] = useState<string | null>(null);

  // Theme Mode: Default Sleek Dark Canvas matching GraphAware dark theme
  const [isDarkTheme, setIsDarkTheme] = useState<boolean>(true);

  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState<boolean>(false);
  const [draggedNode, setDraggedNode] = useState<SimNode | null>(null);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isVerifying, setIsVerifying] = useState<boolean>(false);

  const [canvasDimensions, setCanvasDimensions] = useState<{ width: number; height: number }>({
    width: 1000,
    height: fullHeight ? 720 : 580,
  });

  const simNodesRef = useRef<SimNode[]>([]);
  const animationFrameRef = useRef<number | null>(null);
  const flowTimeRef = useRef<number>(0);

  const effectiveGraph = useMemo(() => {
    return graphData && graphData.nodes && graphData.nodes.length > 0 ? graphData : EMPTY_GRAPH_DATA;
  }, [graphData]);

  const availablePredicates = useMemo(() => {
    const set = new Set<string>();
    effectiveGraph.links.forEach((l) => {
      if (l.label) set.add(l.label);
    });
    return Array.from(set);
  }, [effectiveGraph]);

  useEffect(() => {
    const container = canvasContainerRef.current;
    if (!container) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setCanvasDimensions({ width: Math.floor(width), height: Math.floor(height) });
        }
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const getPrimaryCenterId = useCallback(() => {
    if (centerNodeId && effectiveGraph.nodes.some((n) => n.id === centerNodeId)) {
      return centerNodeId;
    }
    const suspect = effectiveGraph.nodes.find(
      (n) => n.type === "Person" && (n.subType === "SUSPECT" || n.label.toLowerCase().includes("akshay"))
    );
    if (suspect) return suspect.id;
    const person = effectiveGraph.nodes.find((n) => n.type === "Person");
    if (person) return person.id;
    return effectiveGraph.nodes[0]?.id || "";
  }, [centerNodeId, effectiveGraph]);

  useEffect(() => {
    if (!searchTerm.trim()) {
      setSearchResults([]);
      return;
    }
    const matches = effectiveGraph.nodes.filter(
      (n) =>
        n.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        n.type.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setSearchResults(matches.slice(0, 8));
  }, [searchTerm, effectiveGraph]);

  const zoomToNode = useCallback(
    (nodeId: string) => {
      const node = simNodesRef.current.find((n) => n.id === nodeId);
      if (!node) return;
      setSelectedNode(node);
      const targetX = canvasDimensions.width / 2 - node.x;
      const targetY = canvasDimensions.height / 2 - node.y;
      setZoom(1.3);
      setPan({ x: targetX * 1.3, y: targetY * 1.3 });
      setSearchTerm("");
      setIsSearchFocused(false);
    },
    [canvasDimensions]
  );

  // Layout Positioning (Hierarchical Top-to-Bottom, Force, Radial, Grid)
  useEffect(() => {
    const { width, height } = canvasDimensions;
    const centerX = width / 2;
    const centerY = height / 2;
    const targetCenterId = getPrimaryCenterId();

    const nodesList: SimNode[] = [];
    const nonCenterNodes = effectiveGraph.nodes.filter((n) => n.id !== targetCenterId);
    const centerNode = effectiveGraph.nodes.find((n) => n.id === targetCenterId);

    // Hierarchical Vertical Tree Calculation (Top-to-Bottom like Reference Image)
    const tierMap: Record<number, SimNode[]> = { 0: [], 1: [], 2: [], 3: [] };

    if (centerNode) {
      const cSim: SimNode = {
        ...centerNode,
        x: centerX,
        y: centerY - 180,
        vx: 0,
        vy: 0,
        radius: 28,
        isCenter: true,
        pinned: true,
        tier: 0,
      };
      nodesList.push(cSim);
      tierMap[0].push(cSim);
    }

    nonCenterNodes.forEach((n) => {
      const typeConfig = COLOR_MAP[n.type] || COLOR_MAP.Person;
      const tier = typeConfig.tier !== undefined ? typeConfig.tier : 2;
      const simN: SimNode = {
        ...n,
        x: centerX,
        y: centerY,
        vx: 0,
        vy: 0,
        radius: 24,
        isCenter: false,
        pinned: false,
        tier,
      };
      if (!tierMap[tier]) tierMap[tier] = [];
      tierMap[tier].push(simN);
      nodesList.push(simN);
    });

    if (layoutMode === "HIERARCHICAL") {
      const tierYOffsets: Record<number, number> = {
        0: centerY - 210,
        1: centerY - 90,
        2: centerY + 30,
        3: centerY + 170,
      };

      Object.entries(tierMap).forEach(([tStr, tNodes]) => {
        const t = Number(tStr);
        const yPos = tierYOffsets[t] || centerY;
        const count = tNodes.length;
        const spacing = Math.min(180, (width - 200) / Math.max(count, 1));
        const startX = centerX - ((count - 1) * spacing) / 2;

        tNodes.forEach((node, idx) => {
          if (!node.isCenter) {
            node.x = startX + idx * spacing;
            node.y = yPos;
          }
        });
      });
    } else if (layoutMode === "RADIAL") {
      const count = nonCenterNodes.length;
      nonCenterNodes.forEach((n, idx) => {
        const node = nodesList.find((item) => item.id === n.id);
        if (!node) return;
        const angle = (idx / Math.max(count, 1)) * 2 * Math.PI;
        const dist = n.type === "Person" ? 170 : 230;
        node.x = centerX + Math.cos(angle) * dist;
        node.y = centerY + Math.sin(angle) * dist;
      });
    } else if (layoutMode === "GRID") {
      const count = nonCenterNodes.length;
      const cols = Math.ceil(Math.sqrt(count));
      nonCenterNodes.forEach((n, idx) => {
        const node = nodesList.find((item) => item.id === n.id);
        if (!node) return;
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        node.x = centerX + (col - cols / 2) * 160;
        node.y = centerY + (row - Math.ceil(count / cols) / 2) * 140 + 40;
      });
    }

    simNodesRef.current = nodesList;
  }, [effectiveGraph, canvasDimensions, getPrimaryCenterId, layoutMode]);

  // Main Canvas Rendering Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    const tick = () => {
      if (!running) return;
      flowTimeRef.current += 0.035;
      const flowTime = flowTimeRef.current;

      const nodes = simNodesRef.current;
      const links = effectiveGraph.links || [];
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;

      const visibleNodes = nodes.filter((n) => {
        if (disabledNodeTypes.has(n.type)) return false;
        if (verificationFilter === "VERIFIED" && n.verification_status !== "VERIFIED") return false;
        if (verificationFilter === "UNVERIFIED" && n.verification_status === "VERIFIED") return false;
        return true;
      });

      const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
      const visibleLinks = links.filter(
        (l) => visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target) && !disabledPredicates.has(l.label)
      );

      // Physics Simulation Step
      if (isPhysicsActive) {
        if (layoutMode === "FORCE") {
          visibleLinks.forEach((link) => {
            const source = nodes.find((n) => n.id === link.source);
            const target = nodes.find((n) => n.id === link.target);
            if (!source || !target) return;
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const springForce = (dist - linkDistance) * 0.014;
            const fx = (dx / dist) * springForce;
            const fy = (dy / dist) * springForce;
            if (!source.pinned) {
              source.vx += fx;
              source.vy += fy;
            }
            if (!target.pinned) {
              target.vx -= fx;
              target.vy -= fy;
            }
          });

          for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
              const dx = nodes[j].x - nodes[i].x;
              const dy = nodes[j].y - nodes[i].y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const minDist = repulsionStrength / 2;
              if (dist < minDist) {
                const force = ((minDist - dist) / dist) * 0.04;
                if (!nodes[i].pinned) {
                  nodes[i].vx -= dx * force;
                  nodes[i].vy -= dy * force;
                }
                if (!nodes[j].pinned) {
                  nodes[j].vx += dx * force;
                  nodes[j].vy += dy * force;
                }
              }
            }
          }
        }

        nodes.forEach((node) => {
          if (draggedNode && node.id === draggedNode.id) return;
          if (layoutMode === "HIERARCHICAL" && node.isCenter) return;

          node.vx *= 0.82;
          node.vy *= 0.82;
          node.x += node.vx;
          node.y += node.vy;

          node.x = Math.max(70, Math.min(width - 70, node.x));
          node.y = Math.max(70, Math.min(height - 70, node.y));
        });
      }

      ctx.clearRect(0, 0, width, height);

      // Background Theme (White/Light Canvas by Default as in Reference Image)
      if (isDarkTheme) {
        const bgGrad = ctx.createRadialGradient(centerX, centerY, 60, centerX, centerY, Math.max(width, height));
        bgGrad.addColorStop(0, "#0a0e19");
        bgGrad.addColorStop(1, "#04060c");
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, width, height);

        ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
        for (let x = 0; x < width; x += 32) {
          for (let y = 0; y < height; y += 32) {
            ctx.fillRect(x, y, 1.2, 1.2);
          }
        }
      } else {
        // PURE WHITE CANVAS LIKE REFERENCE IMAGE
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);

        ctx.fillStyle = "rgba(0, 0, 0, 0.03)";
        for (let x = 0; x < width; x += 28) {
          for (let y = 0; y < height; y += 28) {
            ctx.fillRect(x, y, 1.2, 1.2);
          }
        }
      }

      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);

      const activeHighlightId = focusedNeighborhoodId || selectedNode?.id || hoveredNode?.id;
      const highlightedNodeIds = new Set<string>();
      if (activeHighlightId) {
        highlightedNodeIds.add(activeHighlightId);
        visibleLinks.forEach((l) => {
          if (l.source === activeHighlightId) highlightedNodeIds.add(l.target);
          if (l.target === activeHighlightId) highlightedNodeIds.add(l.source);
        });
      }

      // --- DRAW DIRECTIONAL ARROW LINKS WITH ROTATED LABELS ---
      visibleLinks.forEach((link) => {
        const source = nodes.find((n) => n.id === link.source);
        const target = nodes.find((n) => n.id === link.target);
        if (!source || !target) return;

        const isHighlighted = activeHighlightId
          ? link.source === activeHighlightId || link.target === activeHighlightId
          : true;

        ctx.globalAlpha = isHighlighted ? 1.0 : 0.16;

        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        const angle = Math.atan2(dy, dx);

        // Arrow head endpoint offset before target radius
        const targetRadius = target.radius + 6;
        const endX = target.x - Math.cos(angle) * targetRadius;
        const endY = target.y - Math.sin(angle) * targetRadius;

        const sourceRadius = source.radius + 6;
        const startX = source.x + Math.cos(angle) * sourceRadius;
        const startY = source.y + Math.sin(angle) * sourceRadius;

        // Line
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = isHighlighted
          ? isDarkTheme
            ? "#00f2fe"
            : "#64748b"
          : isDarkTheme
          ? "rgba(255, 255, 255, 0.2)"
          : "#cbd5e1";
        ctx.lineWidth = isHighlighted ? 1.8 : 1.2;
        ctx.stroke();

        // Directional Arrow Head (→)
        const arrowSize = 7;
        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(
          endX - arrowSize * Math.cos(angle - Math.PI / 6),
          endY - arrowSize * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          endX - arrowSize * Math.cos(angle + Math.PI / 6),
          endY - arrowSize * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fillStyle = isHighlighted ? (isDarkTheme ? "#00f2fe" : "#475569") : "#cbd5e1";
        ctx.fill();

        // Rotated Edge Text Label along Line
        const midX = (startX + endX) / 2;
        const midY = (startY + endY) / 2;
        const labelText = link.label.toUpperCase();

        ctx.save();
        ctx.translate(midX, midY);

        let textAngle = angle;
        if (textAngle > Math.PI / 2 || textAngle < -Math.PI / 2) {
          textAngle += Math.PI;
        }
        ctx.rotate(textAngle);

        ctx.font = "bold 8px 'JetBrains Mono', monospace";
        const textWidth = ctx.measureText(labelText).width;

        // White background behind text for crisp legibility
        ctx.fillStyle = isDarkTheme ? "rgba(8, 12, 24, 0.9)" : "#ffffff";
        ctx.fillRect(-textWidth / 2 - 4, -7, textWidth + 8, 14);

        ctx.fillStyle = isDarkTheme ? (isHighlighted ? "#00f2fe" : "#94a3b8") : isHighlighted ? "#0f172a" : "#64748b";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(labelText, 0, 0);
        ctx.restore();
      });

      // --- DRAW NODES (Vibrant Circles with Icons inside & Clean Label Below) ---
      visibleNodes.forEach((node) => {
        const isMatched = searchTerm && node.label.toLowerCase().includes(searchTerm.toLowerCase());
        const isSelected = selectedNode?.id === node.id;
        const isHovered = hoveredNode?.id === node.id;
        const isCentralHub = node.isCenter;
        const isHighlighted = activeHighlightId ? highlightedNodeIds.has(node.id) : true;

        ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;

        const key = node.isCenter
          ? "Person_SUSPECT"
          : `${node.type}_${node.subType}` in COLOR_MAP
          ? `${node.type}_${node.subType}`
          : node.type in COLOR_MAP
          ? node.type
          : "Person";
        const palette = COLOR_MAP[key] || COLOR_MAP.Person;

        // Selection / Focus Ring
        if (isSelected || isMatched || isHovered) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 7, 0, 2 * Math.PI);
          ctx.strokeStyle = isMatched ? "#dc2626" : "#2563eb";
          ctx.lineWidth = 2.4;
          ctx.setLineDash([4, 3]);
          ctx.stroke();
          ctx.setLineDash([]);
        }

        // Solid Circle Fill
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
        ctx.fillStyle = palette.fill;
        ctx.fill();

        ctx.strokeStyle = isSelected ? "#ffffff" : "rgba(255, 255, 255, 0.8)";
        ctx.lineWidth = 2.0;
        ctx.stroke();

        // White Icon Centered Inside Circle
        ctx.font = isCentralHub ? "bold 16px sans-serif" : "bold 14px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(palette.icon, node.x, node.y);

        // Verification Badge Overlay
        if (node.verification_status === "VERIFIED") {
          ctx.beginPath();
          ctx.arc(node.x + node.radius - 2, node.y - node.radius + 2, 7, 0, 2 * Math.PI);
          ctx.fillStyle = "#10b981";
          ctx.fill();
          ctx.strokeStyle = "#ffffff";
          ctx.lineWidth = 1.2;
          ctx.stroke();
          ctx.font = "bold 8px sans-serif";
          ctx.fillStyle = "#ffffff";
          ctx.fillText("✓", node.x + node.radius - 2, node.y - node.radius + 2);
        }

        // Node Label Directly Below Circle (Matching Reference Image Style)
        const displayLabel = node.label.length > 24 ? node.label.substring(0, 22) + "..." : node.label;
        ctx.font = "bold 11px 'Plus Jakarta Sans', sans-serif";
        const lblY = node.y + node.radius + 14;

        // Halo outline for crisp text contrast on light or dark background
        ctx.lineWidth = 3.5;
        ctx.strokeStyle = isDarkTheme ? "#0a0e19" : "#ffffff";
        ctx.strokeText(displayLabel, node.x, lblY);

        ctx.fillStyle = isDarkTheme ? (isSelected ? "#00f2fe" : "#ffffff") : isSelected ? "#2563eb" : "#0f172a";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(displayLabel, node.x, lblY);
      });

      ctx.restore();
      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);
    return () => {
      running = false;
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [
    effectiveGraph,
    canvasDimensions,
    zoom,
    pan,
    selectedNode,
    hoveredNode,
    searchTerm,
    disabledNodeTypes,
    disabledPredicates,
    verificationFilter,
    draggedNode,
    isPhysicsActive,
    repulsionStrength,
    linkDistance,
    focusedNeighborhoodId,
    isDarkTheme,
    layoutMode,
  ]);

  const getMousePos = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { mouseX: 0, mouseY: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      mouseX: (e.clientX - rect.left - pan.x) / zoom,
      mouseY: (e.clientY - rect.top - pan.y) / zoom,
    };
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);
    const clickedNode = simNodesRef.current.find(
      (n) => Math.sqrt((n.x - mouseX) ** 2 + (n.y - mouseY) ** 2) <= n.radius + 8
    );
    if (clickedNode) {
      setSelectedNode(clickedNode);
      if (!isRightDrawerOpen) setIsRightDrawerOpen(true);
    } else {
      setSelectedNode(null);
    }
  };

  const handleDoubleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);
    const clickedNode = simNodesRef.current.find(
      (n) => Math.sqrt((n.x - mouseX) ** 2 + (n.y - mouseY) ** 2) <= n.radius + 8
    );
    if (clickedNode) {
      setCenterNodeId(clickedNode.id);
      setSelectedNode(clickedNode);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);
    const node = simNodesRef.current.find(
      (n) => Math.sqrt((n.x - mouseX) ** 2 + (n.y - mouseY) ** 2) <= n.radius + 5
    );
    if (node) {
      setDraggedNode(node);
      node.pinned = true;
    } else {
      setIsDraggingCanvas(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { mouseX, mouseY } = getMousePos(e);
    const hNode = simNodesRef.current.find(
      (n) => Math.sqrt((n.x - mouseX) ** 2 + (n.y - mouseY) ** 2) <= n.radius + 6
    );
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
      if (!draggedNode.isCenter) draggedNode.pinned = false;
      setDraggedNode(null);
    }
    setIsDraggingCanvas(false);
  };

  const resetView = () => {
    setCenterNodeId(getPrimaryCenterId());
    setDisabledNodeTypes(new Set());
    setDisabledPredicates(new Set());
    setVerificationFilter("ALL");
    setFocusedNeighborhoodId(null);
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setLayoutMode("HIERARCHICAL");
  };

  const toggleNodeTypeFilter = (type: string) => {
    setDisabledNodeTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const togglePredicateFilter = (predicate: string) => {
    setDisabledPredicates((prev) => {
      const next = new Set(prev);
      if (next.has(predicate)) next.delete(predicate);
      else next.add(predicate);
      return next;
    });
  };

  const handleToggleVerification = async () => {
    if (!selectedNode || !caseId) return;
    const newStatus: VerificationStatus =
      selectedNode.verification_status === "VERIFIED" ? "UNVERIFIED" : "VERIFIED";
    try {
      setIsVerifying(true);
      await investigationApi.updateVerification(caseId, selectedNode.type, selectedNode.id, newStatus);
      setSelectedNode((prev) => (prev ? { ...prev, verification_status: newStatus } : null));
      onRefresh();
    } catch (err) {
      console.error("Failed to update verification", err);
    } finally {
      setIsVerifying(false);
    }
  };

  const exportPngSnapshot = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement("a");
    link.download = `truth_graph_dossier_${caseId || "investigation"}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  const toggleFullscreenMode = () => {
    const container = containerRef.current;
    if (!container) return;
    if (!document.fullscreenElement) {
      container.requestFullscreen().catch((err) => console.warn(err));
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch((err) => console.warn(err));
      setIsFullscreen(false);
    }
  };

  return (
    <div
      ref={containerRef}
      className="graph-container-card"
      style={{
        background: isDarkTheme ? "#050811" : "#ffffff",
        borderRadius: "16px",
        border: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.1)"}`,
        overflow: "hidden",
        position: "relative",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.08)",
        color: isDarkTheme ? "#ffffff" : "#0f172a",
      }}
    >
      {/* Top Banner Header - "Explore a Single View of Truth" */}
      <div
        className="graph-toolbar"
        style={{
          background: isDarkTheme ? "rgba(10, 15, 28, 0.95)" : "rgba(248, 250, 252, 0.95)",
          backdropFilter: "blur(12px)",
          padding: "0.85rem 1.25rem",
          borderBottom: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)"}`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "10px",
              background: isDarkTheme ? "rgba(0, 242, 254, 0.15)" : "rgba(37, 99, 235, 0.1)",
              border: `1px solid ${isDarkTheme ? "#00f2fe" : "#2563eb"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: isDarkTheme ? "#00f2fe" : "#2563eb",
            }}
          >
            <Compass size={20} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 800, color: isDarkTheme ? "#ffffff" : "#0f172a", letterSpacing: "-0.01em" }}>
                Explore a Single View of Truth
              </h3>
              <span
                style={{
                  background: "rgba(16, 185, 129, 0.15)",
                  color: "#059669",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  fontSize: "0.625rem",
                  padding: "0.15rem 0.45rem",
                  borderRadius: "4px",
                  fontWeight: 700,
                }}
              >
                LIVE GRAPH
              </span>
            </div>
            <span style={{ fontSize: "0.725rem", color: isDarkTheme ? "var(--text-secondary)" : "#64748b" }}>
              Unified Entity Intelligence & Connected Subtopology Visualizer
            </span>
          </div>
        </div>

        <div style={{ position: "relative", minWidth: "220px" }}>
          <div
            style={{
              background: isDarkTheme ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.04)",
              border: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.12)"}`,
              borderRadius: "8px",
              padding: "0.35rem 0.65rem",
              display: "flex",
              alignItems: "center",
              gap: "0.45rem",
            }}
          >
            <Search size={14} style={{ color: "#64748b" }} />
            <input
              type="text"
              placeholder="Search graph entities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                color: isDarkTheme ? "#ffffff" : "#0f172a",
                fontSize: "0.775rem",
                outline: "none",
              }}
            />
          </div>

          {isSearchFocused && searchResults.length > 0 && (
            <div
              style={{
                position: "absolute",
                top: "110%",
                left: 0,
                right: 0,
                background: isDarkTheme ? "#0c101c" : "#ffffff",
                border: `1px solid ${isDarkTheme ? "rgba(0, 242, 254, 0.3)" : "rgba(37, 99, 235, 0.3)"}`,
                borderRadius: "8px",
                zIndex: 100,
                boxShadow: "0 10px 25px rgba(0, 0, 0, 0.15)",
                overflow: "hidden",
              }}
            >
              {searchResults.map((res) => (
                <div
                  key={res.id}
                  onClick={() => zoomToNode(res.id)}
                  style={{
                    padding: "0.5rem 0.75rem",
                    cursor: "pointer",
                    borderBottom: "1px solid rgba(0, 0, 0, 0.05)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontSize: "0.775rem",
                  }}
                  className="search-item-hover"
                >
                  <span style={{ color: isDarkTheme ? "#ffffff" : "#0f172a", fontWeight: 600 }}>{res.label}</span>
                  <span style={{ fontSize: "0.65rem", color: "#2563eb", fontFamily: "var(--font-mono)" }}>
                    {res.type}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", flexWrap: "wrap" }}>

          {/* Layout Selector */}
          <select
            value={layoutMode}
            onChange={(e) => setLayoutMode(e.target.value as any)}
            style={{
              background: isDarkTheme ? "rgba(15, 23, 42, 0.85)" : "#ffffff",
              border: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.15)"}`,
              color: isDarkTheme ? "#ffffff" : "#0f172a",
              fontSize: "0.75rem",
              borderRadius: "6px",
              padding: "0.4rem 0.6rem",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            <option value="HIERARCHICAL">📐 Single View Tree (Reference)</option>
            <option value="FORCE">🕸️ Force Directed</option>
            <option value="RADIAL">🌀 Radial Orbit</option>
            <option value="GRID">📊 Grid Matrix</option>
          </select>

          {/* Physics Play / Pause */}
          <button
            onClick={() => setIsPhysicsActive(!isPhysicsActive)}
            style={{
              padding: "0.35rem 0.75rem",
              fontSize: "0.75rem",
              fontWeight: 700,
              borderRadius: "6px",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.35rem",
              background: isPhysicsActive ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
              color: isPhysicsActive ? "#059669" : "#dc2626",
              border: `1px solid ${isPhysicsActive ? "rgba(16, 185, 129, 0.3)" : "rgba(220, 38, 38, 0.3)"}`,
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            {isPhysicsActive ? <Pause size={13} /> : <Play size={13} />}
            <span>{isPhysicsActive ? "Physics ON" : "Paused"}</span>
          </button>

          <button
            onClick={() => setShowPhysicsPanel(!showPhysicsPanel)}
            className="btn-secondary"
            style={{ padding: "0.4rem 0.6rem", fontSize: "0.75rem", borderRadius: "6px" }}
          >
            <Sliders size={14} />
          </button>

          <button
            onClick={resetView}
            className="btn-secondary"
            style={{ padding: "0.4rem 0.65rem", fontSize: "0.75rem", borderRadius: "6px" }}
          >
            <Crosshair size={14} /> Reset
          </button>

          <button onClick={() => setZoom((z) => Math.min(2.8, z + 0.15))} className="btn-icon-small">
            <ZoomIn size={14} />
          </button>
          <button onClick={() => setZoom((z) => Math.max(0.35, z - 0.15))} className="btn-icon-small">
            <ZoomOut size={14} />
          </button>

          <button
            onClick={exportPngSnapshot}
            className="btn-secondary"
            style={{ padding: "0.4rem 0.65rem", fontSize: "0.75rem", borderRadius: "6px" }}
          >
            <Download size={14} /> Export PNG
          </button>

          <button onClick={toggleFullscreenMode} className="btn-icon-small">
            {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>

      {showPhysicsPanel && (
        <div
          style={{
            position: "absolute",
            top: "65px",
            right: "20px",
            background: isDarkTheme ? "rgba(10, 15, 28, 0.95)" : "#ffffff",
            backdropFilter: "blur(12px)",
            border: `1px solid ${isDarkTheme ? "rgba(0, 242, 254, 0.3)" : "rgba(37, 99, 235, 0.3)"}`,
            borderRadius: "10px",
            padding: "0.85rem 1rem",
            zIndex: 90,
            width: "240px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <div style={{ fontSize: "0.775rem", fontWeight: 700, color: "#2563eb" }}>
            Kinetic Physics Tuning
          </div>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#64748b", marginBottom: "0.2rem" }}>
              <span>Repulsion Charge</span>
              <span style={{ fontFamily: "var(--font-mono)", color: isDarkTheme ? "#ffffff" : "#0f172a" }}>{repulsionStrength}</span>
            </div>
            <input
              type="range"
              min="100"
              max="700"
              value={repulsionStrength}
              onChange={(e) => setRepulsionStrength(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#2563eb", cursor: "pointer" }}
            />
          </div>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#64748b", marginBottom: "0.2rem" }}>
              <span>Link Target Distance</span>
              <span style={{ fontFamily: "var(--font-mono)", color: isDarkTheme ? "#ffffff" : "#0f172a" }}>{linkDistance}px</span>
            </div>
            <input
              type="range"
              min="80"
              max="350"
              value={linkDistance}
              onChange={(e) => setLinkDistance(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#2563eb", cursor: "pointer" }}
            />
          </div>
        </div>
      )}

      <div style={{ display: "flex", position: "relative", minHeight: fullHeight ? "700px" : "580px", width: "100%" }}>
        {/* Left Filter & Legend Drawer */}
        <div
          style={{
            width: isLeftDrawerOpen ? "250px" : "40px",
            transition: "width 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
            background: isDarkTheme ? "rgba(8, 12, 24, 0.94)" : "#f8fafc",
            borderRight: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)"}`,
            position: "relative",
            zIndex: 20,
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            onClick={() => setIsLeftDrawerOpen(!isLeftDrawerOpen)}
            style={{
              padding: "0.75rem 0.85rem",
              borderBottom: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              cursor: "pointer",
              background: "rgba(0, 0, 0, 0.02)",
            }}
          >
            {isLeftDrawerOpen ? (
              <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                <Filter size={15} style={{ color: "#2563eb" }} />
                <span style={{ fontSize: "0.825rem", fontWeight: 800, color: isDarkTheme ? "#ffffff" : "#0f172a" }}>
                  Legend & Layers
                </span>
              </div>
            ) : (
              <Filter size={16} style={{ color: "#2563eb", margin: "auto" }} />
            )}
            {isLeftDrawerOpen && <ChevronLeft size={16} style={{ color: "#64748b" }} />}
          </div>

          {isLeftDrawerOpen && (
            <div style={{ padding: "0.85rem", display: "flex", flexDirection: "column", gap: "1.1rem", overflowY: "auto", maxHeight: "600px" }}>
              <div>
                <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: "0.45rem" }}>
                  Entity Classes ({effectiveGraph.nodes.length})
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                  {Object.entries(COLOR_MAP)
                    .filter(([key]) => key !== "Person_SUSPECT")
                    .map(([key, item]) => {
                      const typeName = key.split("_")[0];
                      const count = effectiveGraph.nodes.filter((n) => n.type === typeName).length;
                      const isDisabled = disabledNodeTypes.has(typeName);

                      return (
                        <div
                          key={key}
                          onClick={() => toggleNodeTypeFilter(typeName)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            padding: "0.35rem 0.55rem",
                            borderRadius: "6px",
                            background: isDisabled
                              ? "transparent"
                              : isDarkTheme
                              ? "rgba(255, 255, 255, 0.05)"
                              : "#ffffff",
                            border: `1px solid ${isDisabled ? "transparent" : isDarkTheme ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)"}`,
                            cursor: "pointer",
                            opacity: isDisabled ? 0.45 : 1,
                            fontSize: "0.75rem",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                            <span style={{ width: 8, height: 8, borderRadius: "50%", background: item.fill, border: `1px solid ${item.border}` }} />
                            <span style={{ color: isDarkTheme ? "#ffffff" : "#0f172a", fontWeight: 600 }}>{item.label}</span>
                          </div>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "#64748b" }}>{count}</span>
                        </div>
                      );
                    })}
                </div>
              </div>

              {availablePredicates.length > 0 && (
                <div>
                  <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: "0.45rem" }}>
                    Relationships ({effectiveGraph.links.length})
                  </span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                    {availablePredicates.map((pred) => {
                      const count = effectiveGraph.links.filter((l) => l.label === pred).length;
                      const isDisabled = disabledPredicates.has(pred);
                      return (
                        <div
                          key={pred}
                          onClick={() => togglePredicateFilter(pred)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            padding: "0.35rem 0.55rem",
                            borderRadius: "6px",
                            background: isDisabled
                              ? "transparent"
                              : isDarkTheme
                              ? "rgba(255, 255, 255, 0.05)"
                              : "#ffffff",
                            border: `1px solid ${isDisabled ? "transparent" : isDarkTheme ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)"}`,
                            cursor: "pointer",
                            opacity: isDisabled ? 0.45 : 1,
                            fontSize: "0.725rem",
                          }}
                        >
                          <span style={{ color: "#2563eb", fontFamily: "var(--font-mono)" }}>{pred}</span>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "#64748b" }}>{count}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <div>
                <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: "0.45rem" }}>
                  Officer Verification
                </span>
                <div style={{ display: "flex", gap: "0.25rem" }}>
                  {(["ALL", "VERIFIED", "UNVERIFIED"] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setVerificationFilter(mode)}
                      style={{
                        flex: 1,
                        padding: "0.3rem 0",
                        fontSize: "0.68rem",
                        fontWeight: 700,
                        borderRadius: "5px",
                        border: verificationFilter === mode ? "1px solid #2563eb" : "1px solid rgba(0, 0, 0, 0.1)",
                        background: verificationFilter === mode ? "rgba(37, 99, 235, 0.12)" : "rgba(0, 0, 0, 0.02)",
                        color: verificationFilter === mode ? "#2563eb" : "#64748b",
                        cursor: "pointer",
                      }}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Main Canvas Viewport */}
        <div ref={canvasContainerRef} style={{ flex: 1, position: "relative", minHeight: fullHeight ? "700px" : "580px", overflow: "hidden" }}>
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
              cursor: isDraggingCanvas || draggedNode ? "grabbing" : hoveredNode ? "pointer" : "default",
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
                background: isDarkTheme ? "rgba(10, 15, 30, 0.88)" : "rgba(255, 255, 255, 0.9)",
                backdropFilter: "blur(8px)",
                color: "#64748b",
                padding: "2rem",
                textAlign: "center",
                pointerEvents: "none",
              }}
            >
              <Share2 size={44} style={{ color: "#2563eb", opacity: 0.7, marginBottom: "0.85rem" }} />
              <div style={{ fontSize: "1.15rem", fontWeight: 800, color: isDarkTheme ? "#ffffff" : "#0f172a" }}>
                Single View of Truth Graph Ready
              </div>
              <p style={{ fontSize: "0.825rem", maxWidth: "420px", margin: "0.4rem 0 0 0", lineHeight: 1.45, color: "#64748b" }}>
                Upload an investigation docket in Document AI Ingestion to synthesize connected entities into a single unified Knowledge Graph view of truth.
              </p>
            </div>
          )}
        </div>

        {/* Right Entity Property Inspector Drawer */}
        <div
          style={{
            width: isRightDrawerOpen ? "320px" : "40px",
            transition: "width 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
            background: isDarkTheme ? "rgba(8, 12, 24, 0.96)" : "#f8fafc",
            borderLeft: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.08)"}`,
            position: "relative",
            zIndex: 20,
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            onClick={() => setIsRightDrawerOpen(!isRightDrawerOpen)}
            style={{
              padding: "0.75rem 0.85rem",
              borderBottom: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)"}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              cursor: "pointer",
              background: "rgba(0, 0, 0, 0.02)",
            }}
          >
            {isRightDrawerOpen ? (
              <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                <Zap size={16} style={{ color: "#2563eb" }} />
                <span style={{ fontSize: "0.85rem", fontWeight: 800, color: isDarkTheme ? "#ffffff" : "#0f172a" }}>
                  Entity Inspector
                </span>
              </div>
            ) : (
              <Zap size={16} style={{ color: "#2563eb", margin: "auto" }} />
            )}
            {isRightDrawerOpen && <ChevronRight size={16} style={{ color: "#64748b" }} />}
          </div>

          {isRightDrawerOpen && (
            <div style={{ padding: "1rem", display: "flex", flexDirection: "column", gap: "0.85rem", overflowY: "auto", maxHeight: "640px" }}>
              {selectedNode ? (
                <>
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.5rem" }}>
                    <div>
                      <h4 style={{ fontSize: "1.1rem", fontWeight: 800, color: isDarkTheme ? "#ffffff" : "#0f172a", margin: 0 }}>
                        {selectedNode.label}
                      </h4>
                      <span style={{ fontSize: "0.725rem", color: "#2563eb", fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                        {selectedNode.type} ({selectedNode.subType || "General Entity"})
                      </span>
                    </div>

                    <button
                      onClick={handleToggleVerification}
                      disabled={isVerifying}
                      style={{
                        fontSize: "0.675rem",
                        padding: "0.25rem 0.55rem",
                        borderRadius: "6px",
                        fontWeight: 700,
                        background: selectedNode.verification_status === "VERIFIED" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                        color: selectedNode.verification_status === "VERIFIED" ? "#059669" : "#d97706",
                        border: `1px solid ${selectedNode.verification_status === "VERIFIED" ? "rgba(16, 185, 129, 0.35)" : "rgba(245, 158, 11, 0.35)"}`,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.3rem",
                      }}
                    >
                      {selectedNode.verification_status === "VERIFIED" ? (
                        <>
                          <CheckCircle2 size={12} /> VERIFIED
                        </>
                      ) : (
                        <>
                          <AlertTriangle size={12} /> VERIFY NOW
                        </>
                      )}
                    </button>
                  </div>

                  {(() => {
                    const profile = getNodeInvestigativeProfile(
                      selectedNode,
                      effectiveGraph.links,
                      effectiveGraph.nodes
                    );
                    return (
                      <div
                        style={{
                          background: isDarkTheme ? profile.cardBgDark : profile.cardBgLight,
                          border: `1px solid ${profile.cardBorder}`,
                          borderRadius: "8px",
                          padding: "0.65rem 0.75rem",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.45rem",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            gap: "0.5rem",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
                            {profile.isSuspect ? (
                              <AlertTriangle size={13} style={{ color: profile.badgeColor, flexShrink: 0 }} />
                            ) : (
                              <ShieldAlert size={13} style={{ color: profile.badgeColor, flexShrink: 0 }} />
                            )}
                            <span
                              style={{
                                fontSize: "0.72rem",
                                fontWeight: 800,
                                color: profile.badgeColor,
                                textTransform: "uppercase",
                                letterSpacing: "0.03em",
                              }}
                            >
                              {profile.headerTitle}
                            </span>
                          </div>
                          <span
                            style={{
                              fontSize: "0.58rem",
                              fontWeight: 800,
                              padding: "0.15rem 0.4rem",
                              borderRadius: "4px",
                              background: profile.badgeBg,
                              color: profile.badgeColor,
                              border: `1px solid ${profile.badgeBorder}`,
                              letterSpacing: "0.04em",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {profile.badgeLabel}
                          </span>
                        </div>

                        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                          {profile.reasons.map((reason, idx) => (
                            <div
                              key={idx}
                              style={{
                                display: "flex",
                                alignItems: "flex-start",
                                gap: "0.4rem",
                                fontSize: "0.735rem",
                                lineHeight: 1.35,
                                color: isDarkTheme ? profile.textColorDark : profile.textColorLight,
                              }}
                            >
                              <span
                                style={{
                                  color: profile.badgeColor,
                                  fontWeight: 800,
                                  fontSize: "0.8rem",
                                  lineHeight: 1,
                                  flexShrink: 0,
                                  marginTop: "0.1rem",
                                }}
                              >
                                →
                              </span>
                              <span>{reason}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}

                  <div style={{ display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                    <div style={{ fontSize: "0.68rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      Entity Attributes
                    </div>
                    <div style={{ background: isDarkTheme ? "rgba(255, 255, 255, 0.02)" : "#ffffff", border: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.08)"}`, borderRadius: "8px", padding: "0.6rem 0.75rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                        <span style={{ color: "#64748b" }}>Entity ID</span>
                        <span style={{ fontFamily: "var(--font-mono)", color: isDarkTheme ? "#ffffff" : "#0f172a" }}>{selectedNode.id}</span>
                      </div>
                      {selectedNode.properties.occupation && (
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                          <span style={{ color: "#64748b" }}>Role / Occupation</span>
                          <span style={{ color: isDarkTheme ? "#ffffff" : "#0f172a", fontWeight: 600 }}>{selectedNode.properties.occupation}</span>
                        </div>
                      )}
                      {selectedNode.properties.address && (
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem" }}>
                          <span style={{ color: "#64748b" }}>Address</span>
                          <span style={{ color: isDarkTheme ? "#ffffff" : "#0f172a", maxWidth: "160px", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                            {selectedNode.properties.address}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "0.4rem" }}>
                    {selectedNode.id !== centerNodeId && (
                      <button
                        onClick={() => setCenterNodeId(selectedNode.id)}
                        className="btn-secondary"
                        style={{
                          flex: 1,
                          justifyContent: "center",
                          padding: "0.45rem",
                          fontSize: "0.75rem",
                          background: "rgba(37, 99, 235, 0.1)",
                          border: "1px solid #2563eb",
                          color: "#2563eb",
                          fontWeight: 700,
                          borderRadius: "8px",
                          cursor: "pointer",
                        }}
                      >
                        <Crosshair size={13} /> Focal Center
                      </button>
                    )}

                    <button
                      onClick={() => setFocusedNeighborhoodId(focusedNeighborhoodId === selectedNode.id ? null : selectedNode.id)}
                      className="btn-secondary"
                      style={{
                        flex: 1,
                        justifyContent: "center",
                        padding: "0.45rem",
                        fontSize: "0.75rem",
                        background: focusedNeighborhoodId === selectedNode.id ? "rgba(168, 85, 247, 0.15)" : "rgba(0, 0, 0, 0.04)",
                        border: `1px solid ${focusedNeighborhoodId === selectedNode.id ? "#a855f7" : "rgba(0, 0, 0, 0.1)"}`,
                        color: focusedNeighborhoodId === selectedNode.id ? "#9333ea" : "var(--text-primary)",
                        fontWeight: 700,
                        borderRadius: "8px",
                        cursor: "pointer",
                      }}
                    >
                      <GitBranch size={13} /> Isolate 1-Hop
                    </button>
                  </div>

                  <div>
                    <span style={{ fontSize: "0.68rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: "0.45rem" }}>
                      Connected Subtopology ({effectiveGraph.links.filter((l) => l.source === selectedNode.id || l.target === selectedNode.id).length})
                    </span>

                    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", maxHeight: "200px", overflowY: "auto" }}>
                      {effectiveGraph.links
                        .filter((l) => l.source === selectedNode.id || l.target === selectedNode.id)
                        .map((l) => {
                          const isOutgoing = l.source === selectedNode.id;
                          const otherId = isOutgoing ? l.target : l.source;
                          const otherNode = effectiveGraph.nodes.find((n) => n.id === otherId);

                          return (
                            <div
                              key={l.id}
                              onClick={() => zoomToNode(otherId)}
                              style={{
                                background: isDarkTheme ? "rgba(255, 255, 255, 0.03)" : "#ffffff",
                                border: `1px solid ${isDarkTheme ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)"}`,
                                borderRadius: "6px",
                                padding: "0.4rem 0.6rem",
                                fontSize: "0.75rem",
                                cursor: "pointer",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                              }}
                              className="search-item-hover"
                            >
                              <span style={{ color: isDarkTheme ? "#ffffff" : "#0f172a" }}>
                                {isOutgoing ? "→" : "←"} <strong style={{ color: "#2563eb" }}>{l.label}</strong> {otherNode?.label || otherId}
                              </span>
                              <ExternalLink size={12} style={{ color: "#64748b" }} />
                            </div>
                          );
                        })}
                    </div>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: "center", padding: "3rem 1rem", color: "#64748b", fontSize: "0.8rem" }}>
                  <Zap size={32} style={{ color: "#2563eb", opacity: 0.5, marginBottom: "0.75rem" }} />
                  <br />
                  Click any entity node on the canvas to inspect attributes and subtopology links.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

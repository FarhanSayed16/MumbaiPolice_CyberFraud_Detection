import React, { useEffect, useRef, useState, useCallback } from "react";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import {
  trailService,
  accountService,
  type TrailResponse,
  type TrailNode,
  type TrailEdge,
  type TrailExplainPlan,
} from "@/api/client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  SlidersHorizontal,
  Download,
  ShieldAlert,
  HelpCircle,
  Eye,
  CheckCircle,
  Clock,
  Repeat,
  FileSpreadsheet,
  FileCode,
  Activity,
  Layers,
  ArrowRight,
  Database,
  Lock,
  X,
  AlertTriangle,
  Info
} from "lucide-react";

cytoscape.use(dagre);

interface CaseTrailGraphProps {
  caseId: string;
  onAccountRevealed?: () => void;
  /** Increment to force trail reload after import (H2) */
  refreshToken?: number;
}

type SelectionType = { type: "node"; data: TrailNode } | { type: "edge"; data: TrailEdge } | null;

export const CaseTrailGraph: React.FC<CaseTrailGraphProps> = ({ caseId, onAccountRevealed, refreshToken = 0 }) => {
  const graphRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  const [trailData, setTrailData] = useState<TrailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Layout Controls
  const [maxDepth, setMaxDepth] = useState<number>(5);
  const [minAmount, setMinAmount] = useState<number>(0);
  const [minLayer, setMinLayer] = useState<number>(0);
  const [maxLayer, setMaxLayer] = useState<number>(15);
  const [layoutDir, setLayoutDir] = useState<"LR" | "TB">("LR");
  const [showFilters, setShowFilters] = useState<boolean>(false);

  // Selection & Drawer
  const [selection, setSelection] = useState<SelectionType>(null);
  const [revealBusy, setRevealBusy] = useState<boolean>(false);
  const [revealError, setRevealError] = useState<string | null>(null);
  const [revealedData, setRevealedData] = useState<Record<string, { account_number?: string; ifsc_code?: string; upi_id?: string; account_holder?: string }>>({});
  const [revealTargetNode, setRevealTargetNode] = useState<TrailNode | null>(null);
  const [revealReason, setRevealReason] = useState<string>("");

  // Advanced / developer-facing UI
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Explain Sanity Modal
  const [explainPlan, setExplainPlan] = useState<TrailExplainPlan | null>(null);
  const [explainBusy, setExplainBusy] = useState<boolean>(false);
  const [showExplainModal, setShowExplainModal] = useState<boolean>(false);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount || 0);

  const loadTrail = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await trailService.traverse(caseId, { max_depth: maxDepth });
      setTrailData(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to fetch multi-hop trail graph.");
      setTrailData(null);
    } finally {
      setLoading(false);
    }
  }, [caseId, maxDepth]);

  useEffect(() => {
    loadTrail();
  }, [loadTrail, refreshToken]);

  const openRevealModal = (node: TrailNode) => {
    setRevealTargetNode(node);
    setRevealReason("");
    setRevealError(null);
  };

  const cancelReveal = () => {
    setRevealTargetNode(null);
    setRevealReason("");
  };

  const confirmReveal = async () => {
    if (!revealTargetNode) return;
    const reason = revealReason.trim();
    if (reason.length < 10) {
      setRevealError("Justification must be at least 10 characters for audit compliance.");
      return;
    }
    setRevealBusy(true);
    setRevealError(null);
    try {
      const res = await accountService.reveal(revealTargetNode.id, reason, caseId);
      setRevealedData((prev) => ({
        ...prev,
        [revealTargetNode.id]: {
          account_number: res.account_number,
          ifsc_code: res.ifsc_code,
          upi_id: res.upi_id,
          account_holder: res.account_holder,
        },
      }));
      setRevealTargetNode(null);
      setRevealReason("");
      if (onAccountRevealed) onAccountRevealed();
    } catch (err: any) {
      setRevealError(err?.response?.data?.detail || "Account reveal failed (audit error).");
    } finally {
      setRevealBusy(false);
    }
  };

  const handleFetchExplain = async () => {
    setExplainBusy(true);
    try {
      const plan = await trailService.explain(caseId);
      setExplainPlan(plan);
      setShowExplainModal(true);
    } catch (err: any) {
      setError("Failed to fetch query EXPLAIN plan.");
    } finally {
      setExplainBusy(false);
    }
  };

  // Export CSV / JSON (`Sub-phase 10.3`)
  const exportJson = () => {
    if (!trailData) return;
    const blob = new Blob([JSON.stringify(trailData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trail-summary-${caseId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCsv = () => {
    if (!trailData) return;
    const headers = ["Layer", "Account ID", "Stable ID", "Bank Name", "Masked Number", "IFSC", "Incoming INR", "Outgoing INR", "Freeze Status", "Mule/Risk", "Dead-End", "Pending"];
    const rows = trailData.nodes.map((n) => [
      n.layer_depth,
      n.id,
      n.stable_id,
      n.bank_name || "N/A",
      revealedData[n.id]?.account_number || n.account_number_masked || "••••",
      revealedData[n.id]?.ifsc_code || n.ifsc_code_masked || "••••",
      n.incoming_total,
      n.outgoing_total,
      n.freeze_status,
      n.is_mule ? `YES (${n.risk_score})` : "NO",
      n.is_dead_end ? "YES" : "NO",
      n.pending_hop ? "YES" : "NO",
    ]);
    const csvContent = [headers.join(","), ...rows.map((r) => r.map((c) => `"${c}"`).join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trail-summary-${caseId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Build and render Cytoscape graph
  useEffect(() => {
    if (!graphRef.current || !trailData) return;

    // Filter nodes/edges by minAmount + layer range (M2)
    const layerOk = (n: TrailNode) => n.layer_depth >= minLayer && n.layer_depth <= maxLayer;
    const filteredEdges = trailData.edges.filter((e) => {
      if (e.amount < minAmount) return false;
      const src = trailData.nodes.find((n) => n.id === e.source_id);
      const tgt = trailData.nodes.find((n) => n.id === e.target_id);
      return (!src || layerOk(src)) && (!tgt || layerOk(tgt));
    });
    const activeNodeIds = new Set<string>();
    filteredEdges.forEach((e) => {
      activeNodeIds.add(e.source_id);
      activeNodeIds.add(e.target_id);
    });
    activeNodeIds.add(trailData.start_account_id);

    const filteredNodes = trailData.nodes.filter(
      (n) => (activeNodeIds.has(n.id) || n.layer_depth === 0) && layerOk(n)
    );

    const elements: any[] = [];

    filteredNodes.forEach((node) => {
      const isStart = node.id === trailData.start_account_id || node.layer_depth === 0;
      const rev = revealedData[node.id];
      const accNum = rev?.account_number || node.account_number_masked || "••••";
      const bank = node.bank_name || "Bank";
      const tags: string[] = [];
      if (node.cash_out_detected) tags.push("ATM");
      if (node.is_mule) tags.push("MULE");
      if (node.risk_score > 80) tags.push("HIGH RISK");
      else if (node.risk_score > 50) tags.push("MED RISK");
      if (node.is_dead_end) tags.push("DEAD-END");
      if (node.pending_hop) tags.push("PENDING");
      if (node.is_cycle_target) tags.push("LOOP");

      const label = `[L${node.layer_depth}] ${bank}\n${accNum}\nINR ${node.incoming_total.toLocaleString("en-IN")}${tags.length > 0 ? `\n[${tags.join(" | ")}]` : ""}`;

      let nodeType = "normal";
      if (isStart) nodeType = "start";
      else if (node.risk_score > 80) nodeType = "high_risk";
      else if (node.risk_score > 50) nodeType = "med_risk";
      else if (node.cash_out_detected || node.is_mule) nodeType = "mule";
      else if (node.is_dead_end) nodeType = "deadend";
      else if (node.pending_hop) nodeType = "pending";
      else if (node.is_cycle_target) nodeType = "cycle";

      elements.push({
        data: {
          id: node.id,
          label,
          type: nodeType,
          nodeData: node,
        },
      });
    });

    filteredEdges.forEach((edge) => {
      const label = `INR ${edge.amount.toLocaleString("en-IN")}\n${edge.utr_number || "UTR"}`;
      elements.push({
        data: {
          id: edge.id,
          source: edge.source_id,
          target: edge.target_id,
          label,
          edgeData: edge,
        },
      });
    });

    const cy = cytoscape({
      container: graphRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "text-wrap": "wrap",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": 10,
            "font-weight": 600,
            color: "#0f172a",
            width: 140,
            height: 70,
            "background-color": "#f1f5f9",
            "border-width": 2,
            "border-color": "#64748b",
            shape: "roundrectangle",
            "transition-property": "background-color, border-color, width, height",
            "transition-duration": 0.2,
          },
        },
        {
          selector: 'node[type="start"]',
          style: {
            "background-color": "#dbeafe",
            "border-color": "#2563eb",
            "border-width": 3,
            color: "#1e3a8a",
          },
        },
        {
          selector: 'node[type="mule"]',
          style: {
            "background-color": "#fee2e2",
            "border-color": "#dc2626",
            "border-width": 3,
            color: "#7f1d1d",
          },
        },
        {
          selector: 'node[type="high_risk"]',
          style: {
            "background-color": "#fef2f2",
            "border-color": "#ef4444",
            "border-width": 3,
            color: "#991b1b",
          },
        },
        {
          selector: 'node[type="med_risk"]',
          style: {
            "background-color": "#fff7ed",
            "border-color": "#f97316",
            "border-width": 3,
            color: "#9a3412",
          },
        },
        {
          selector: 'node[type="deadend"]',
          style: {
            "background-color": "#f8fafc",
            "border-color": "#94a3b8",
            "border-style": "dashed",
            "border-width": 2,
            color: "#475569",
          },
        },
        {
          selector: 'node[type="pending"]',
          style: {
            "background-color": "#fef3c7",
            "border-color": "#d97706",
            "border-style": "dashed",
            "border-width": 2,
            color: "#92400e",
          },
        },
        {
          selector: 'node[type="cycle"]',
          style: {
            "background-color": "#f3e8ff",
            "border-color": "#9333ea",
            "border-style": "dashed",
            "border-width": 2,
            color: "#581c87",
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 4,
            "border-color": "#0ea5e9",
            "background-color": "#e0f2fe",
          },
        },
        {
          selector: "edge",
          style: {
            label: "data(label)",
            "font-size": 9,
            "text-background-color": "#ffffff",
            "text-background-opacity": 0.9,
            "text-background-padding": "2px",
            "text-border-opacity": 0.5,
            "text-border-width": 1,
            "text-border-color": "#cbd5e1",
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            width: 2.5,
            "line-color": "#94a3b8",
            "target-arrow-color": "#94a3b8",
          },
        },
        {
          selector: "edge:selected",
          style: {
            width: 4,
            "line-color": "#0ea5e9",
            "target-arrow-color": "#0ea5e9",
          },
        },
      ],
      layout: {
        name: "dagre",
        rankDir: layoutDir,
        nodeSep: 50,
        rankSep: 90,
      } as any,
    });

    cyRef.current = cy;

    cy.on("tap", "node", (evt) => {
      const nodeData: TrailNode = evt.target.data("nodeData");
      if (nodeData) setSelection({ type: "node", data: nodeData });
    });

    cy.on("tap", "edge", (evt) => {
      const edgeData: TrailEdge = evt.target.data("edgeData");
      if (edgeData) setSelection({ type: "edge", data: edgeData });
    });

    cy.on("tap", (evt) => {
      if (evt.target === cy) {
        setSelection(null);
      }
    });

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [trailData, minAmount, minLayer, maxLayer, layoutDir, revealedData]);

  const handleZoom = (direction: "in" | "out" | "fit") => {
    if (!cyRef.current) return;
    if (direction === "fit") {
      cyRef.current.fit(undefined, 30);
    } else if (direction === "in") {
      cyRef.current.zoom(cyRef.current.zoom() * 1.25);
    } else {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Cockpit & Stats Header (`Sub-phase 10.1 & 10.3`) */}
      <div className="bg-slate-900 text-white p-4 rounded-xl shadow-lg border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="p-2.5 bg-blue-600/30 rounded-lg border border-blue-500/30">
            <Activity className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-base text-white">Money Trail</h3>
              {trailData && (
                <Badge
                  className={`text-[10px] uppercase font-bold border ${
                    trailData.summary.engine_source === "neo4j"
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                      : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                  }`}
                >
                  <Database className="h-3 w-3 mr-1 inline" />
                  {showAdvanced
                    ? trailData.summary.engine_source === "neo4j"
                      ? "Neo4j Graph Engine"
                      : "Postgres Fallback Engine"
                    : trailData.summary.engine_source === "neo4j"
                      ? "Graph engine"
                      : "Standard engine"}
                </Badge>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Interactive path discovery with masking and cycle detection.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`text-xs gap-1.5 border-slate-700 ${showAdvanced ? "bg-slate-700 text-white border-slate-600" : "bg-transparent text-slate-300 hover:bg-slate-800 hover:text-white"}`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>Advanced tools</span>
          </Button>

          {showAdvanced && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleFetchExplain}
              disabled={explainBusy}
              className="bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white text-xs gap-1.5"
            >
              <HelpCircle className="h-3.5 w-3.5 text-blue-400" />
              <span>EXPLAIN Sanity Check</span>
            </Button>
          )}

          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className={`text-xs gap-1.5 border-slate-700 ${showFilters ? "bg-blue-600 text-white border-blue-500" : "bg-slate-800 text-slate-200 hover:bg-slate-700 hover:text-white"}`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>Filters ({showFilters ? "Open" : "Closed"})</span>
          </Button>

          <Button
            size="sm"
            variant="outline"
            onClick={loadTrail}
            disabled={loading}
            className="bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700 hover:text-white text-xs gap-1"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh Graph</span>
          </Button>

          <div className="flex items-center bg-slate-800 border border-slate-700 rounded-md overflow-hidden ml-1">
            <button
              onClick={exportJson}
              disabled={!trailData}
              title="Export Trail JSON"
              className="px-2.5 py-1.5 text-xs text-slate-300 hover:bg-slate-700 flex items-center gap-1 border-r border-slate-700"
            >
              <FileCode className="h-3.5 w-3.5 text-blue-400" /> JSON
            </button>
            <button
              onClick={exportCsv}
              disabled={!trailData}
              title="Export Trail CSV Annex"
              className="px-2.5 py-1.5 text-xs text-slate-300 hover:bg-slate-700 flex items-center gap-1"
            >
              <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-400" /> CSV Annex
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Strip */}
      {trailData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3">
          <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border shadow-2xs flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Traced</span>
            <span className="text-base font-extrabold text-slate-800 dark:text-slate-200 font-mono mt-1">{formatCurrency(trailData.summary.total_amount_traced)}</span>
          </div>
          <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border shadow-2xs flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Nodes / Edges</span>
            <span className="text-base font-extrabold text-slate-800 dark:text-slate-200 font-mono mt-1">{trailData.summary.total_nodes} / {trailData.summary.total_edges}</span>
          </div>
          <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border shadow-2xs flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Max Layer Reached</span>
            <span className="text-base font-extrabold text-slate-800 dark:text-slate-200 font-mono mt-1">Layer {trailData.summary.max_layer_reached} (Cap: {trailData.depth_cap_applied})</span>
          </div>
          <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border shadow-2xs flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Split Branches</span>
            <span className="text-base font-extrabold text-blue-600 font-mono mt-1">{trailData.summary.split_transactions_count} accounts</span>
          </div>
          <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border shadow-2xs flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Dead-Ends</span>
            <span className="text-base font-extrabold text-slate-600 dark:text-slate-400 font-mono mt-1">{trailData.summary.dead_end_count}</span>
          </div>
          <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border shadow-2xs flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Pending Hops</span>
            <span className="text-base font-extrabold text-amber-600 font-mono mt-1">{trailData.summary.pending_hop_count}</span>
          </div>
          <div className="bg-white dark:bg-slate-900 p-3 rounded-xl border shadow-2xs flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Bounded Cycles</span>
            <span className="text-base font-extrabold text-purple-600 font-mono mt-1">{trailData.summary.cycle_count}</span>
          </div>
        </div>
      )}

      {/* Expandable Filter & Layout Bar (`Sub-phase 10.3`) */}
      {showFilters && (
        <Card className="bg-slate-50 dark:bg-slate-950 border-blue-200">
          <CardContent className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-center">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center justify-between">
                <span>Depth Cap (Layers to Traverse):</span>
                <span className="font-mono text-blue-600">{maxDepth} Layers</span>
              </label>
              <input
                type="range"
                min={1}
                max={15}
                value={maxDepth}
                onChange={(e) => setMaxDepth(Number(e.target.value))}
                className="w-full accent-blue-600 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Hard maximum is 15 layers (`GRAPH_TRAVERSAL_MAX_DEPTH`)</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center justify-between">
                <span>Min Transfer Amount Filter:</span>
                <span className="font-mono text-emerald-700">{formatCurrency(minAmount)}</span>
              </label>
              <input
                type="number"
                min={0}
                step={10000}
                value={minAmount}
                onChange={(e) => setMinAmount(Math.max(0, Number(e.target.value)))}
                className="w-full text-xs px-2.5 py-1.5 border rounded bg-white dark:bg-slate-900 font-mono"
                placeholder="0"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Hide low-value transactions to declutter dense graphs</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Layer Range Filter:</label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={0}
                  max={15}
                  value={minLayer}
                  onChange={(e) => setMinLayer(Math.max(0, Number(e.target.value)))}
                  className="w-16 text-xs px-2 py-1.5 border rounded bg-white dark:bg-slate-900 font-mono"
                />
                <span className="text-xs text-slate-500 dark:text-slate-400">to</span>
                <input
                  type="number"
                  min={0}
                  max={15}
                  value={maxLayer}
                  onChange={(e) => setMaxLayer(Math.min(15, Number(e.target.value)))}
                  className="w-16 text-xs px-2 py-1.5 border rounded bg-white dark:bg-slate-900 font-mono"
                />
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Show only nodes within hop layers L{minLayer}–L{maxLayer}</span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">Graph Layout Orientation:</label>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  type="button"
                  variant={layoutDir === "LR" ? "default" : "outline"}
                  onClick={() => setLayoutDir("LR")}
                  className="flex-1 text-xs"
                >
                  Left → Right
                </Button>
                <Button
                  size="sm"
                  type="button"
                  variant={layoutDir === "TB" ? "default" : "outline"}
                  onClick={() => setLayoutDir("TB")}
                  className="flex-1 text-xs"
                >
                  Top → Bottom
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Graph Container + Sidebar Split */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Cytoscape Canvas Area (`Sub-phase 10.1`) */}
        <div className="lg:col-span-3 bg-white dark:bg-slate-900 border rounded-xl shadow-sm relative overflow-hidden flex flex-col">
          {/* Zoom Toolbar */}
          <div className="absolute top-3 right-3 z-10 flex flex-col gap-1 bg-white dark:bg-slate-900/90 backdrop-blur border rounded-lg shadow-md p-1">
            <button
              onClick={() => handleZoom("in")}
              title="Zoom In"
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
            >
              <ZoomIn className="h-4 w-4" />
            </button>
            <button
              onClick={() => handleZoom("out")}
              title="Zoom Out"
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
            >
              <ZoomOut className="h-4 w-4" />
            </button>
            <button
              onClick={() => handleZoom("fit")}
              title="Fit to Canvas"
              className="p-1.5 text-slate-600 dark:text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>

          {/* Legend Banner (`Sub-phase 10.3`) */}
          <div className="bg-slate-50 dark:bg-slate-950 border-b px-4 py-2 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400 flex-wrap gap-3">
            <span className="font-bold text-slate-700 dark:text-slate-300">Legend:</span>
            <div className="flex items-center gap-4 flex-wrap">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-blue-100 border-2 border-blue-600 inline-block" />
                Start / Layer 0
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-red-100 border-2 border-red-600 inline-block" />
                Suspect / Mule / ATM
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-amber-100 border-2 border-amber-600 border-dashed inline-block" />
                Pending Bank Reply
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-purple-100 border-2 border-purple-600 border-dashed inline-block" />
                Bounded Cycle
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-slate-100 border-2 border-slate-400 border-dashed inline-block" />
                Dead-End
              </span>
            </div>
            {trailData && <span className="font-mono text-[10px] text-slate-400">Execution: {trailData.summary.execution_time_ms.toFixed(1)} ms</span>}
          </div>

          {loading ? (
            <div className="h-[520px] flex flex-col items-center justify-center text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950/50">
              <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-3" />
              <p className="font-semibold text-slate-700 dark:text-slate-300">Computing Multi-Hop Traversal...</p>
              <p className="text-xs text-slate-400 mt-1">Executing graph algorithms across linked accounts & split branches</p>
            </div>
          ) : error ? (
            <div className="h-[520px] flex flex-col items-center justify-center p-8 text-center bg-red-50 dark:bg-red-900/40/30">
              <AlertTriangle className="h-10 w-10 text-red-500 mb-3" />
              <p className="font-bold text-red-800 text-sm mb-1">{error}</p>
              <Button size="sm" variant="outline" onClick={loadTrail} className="mt-3">
                Retry Query
              </Button>
            </div>
          ) : !trailData || trailData.nodes.length === 0 ? (
            <div className="h-[520px] flex flex-col items-center justify-center text-slate-400 p-8 text-center bg-slate-50 dark:bg-slate-950/50">
              <Layers className="h-10 w-10 text-slate-300 mb-3" />
              <p className="font-semibold text-slate-600 dark:text-slate-400">No Trail Hops Available</p>
              <p className="text-xs max-w-md mt-1">
                Upload transaction sheets via "Import Transactions (CSV/XLSX)" or add suspect accounts at intake to generate live multi-hop visual graphs.
              </p>
            </div>
          ) : (
            <div ref={graphRef} className="w-full h-[520px] bg-slate-50 dark:bg-slate-950/40 cursor-grab active:cursor-grabbing" />
          )}
        </div>

        {/* Provenance & Detail Side Drawer (`Sub-phase 10.2`) */}
        <div className="lg:col-span-1 flex flex-col">
          <Card className="h-full flex flex-col border shadow-sm overflow-hidden">
            <CardHeader className="pb-3 border-b bg-slate-50 dark:bg-slate-950/80">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-1.5">
                  <Info className="h-4 w-4 text-blue-600" />
                  <span>Provenance & Details</span>
                </CardTitle>
                {selection && (
                  <button onClick={() => setSelection(null)} className="text-slate-400 hover:text-slate-600 dark:text-slate-400">
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </CardHeader>

            <CardContent className="p-4 flex-1 overflow-y-auto space-y-4">
              {!selection ? (
                <div className="text-center py-12 text-slate-400 space-y-2">
                  <Eye className="h-8 w-8 mx-auto text-slate-300" />
                  <p className="font-semibold text-slate-600 dark:text-slate-400 text-xs">Click Any Node or Edge</p>
                  <p className="text-[11px] leading-relaxed max-w-xs mx-auto">
                    Select a bank account or transaction arrow in the chart to inspect full investigative provenance, statutory unmasking, and split transaction statistics.
                  </p>
                </div>
              ) : selection.type === "node" ? (
                <div className="space-y-4 text-xs">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">Selected Account</span>
                      <Badge className="bg-blue-100 text-blue-800 text-[10px] uppercase font-bold">
                        Layer {selection.data.layer_depth}
                      </Badge>
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">{selection.data.bank_name || "Bank Account"}</h4>
                    <p className="font-mono text-slate-600 dark:text-slate-400 mt-0.5">{selection.data.stable_id}</p>
                  </div>

                  {/* Status Badges */}
                  <div className="flex flex-wrap gap-1.5">
                    <Badge variant="outline" className="text-[10px] uppercase font-semibold">
                      Freeze: {selection.data.freeze_status}
                    </Badge>
                    {selection.data.risk_score > 50 && (
                      <Badge className={selection.data.risk_score > 80 ? "bg-red-100 text-red-800 border-red-200 text-[10px] font-bold" : "bg-orange-100 text-orange-800 border-orange-200 text-[10px] font-bold"}>
                        Risk Score: {selection.data.risk_score}
                      </Badge>
                    )}
                    {selection.data.is_mule && selection.data.risk_score <= 50 && (
                      <Badge className="bg-red-100 text-red-800 border-red-200 text-[10px] font-bold">
                        Mule (No Score)
                      </Badge>
                    )}
                    {selection.data.cash_out_detected && (
                      <Badge className="bg-orange-100 text-orange-800 border-orange-200 text-[10px] font-bold">
                        ATM / Cash-Out
                      </Badge>
                    )}
                    {selection.data.is_dead_end && (
                      <Badge variant="secondary" className="text-[10px] font-bold">
                        Dead-End Node
                      </Badge>
                    )}
                    {selection.data.pending_hop && (
                      <Badge className="bg-amber-100 text-amber-800 border-amber-200 text-[10px] font-bold gap-1">
                        <Clock className="h-3 w-3 inline" /> Awaiting Bank Reply
                      </Badge>
                    )}
                    {selection.data.is_cycle_target && (
                      <Badge className="bg-purple-100 text-purple-800 border-purple-200 text-[10px] font-bold gap-1">
                        <Repeat className="h-3 w-3 inline" /> Cycle Target
                      </Badge>
                    )}
                  </div>

                  {/* Account Identifiers Box */}
                  <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-lg border space-y-2 font-mono">
                    <div>
                      <span className="text-[10px] text-slate-400 block font-sans uppercase">Account Number</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {revealedData[selection.data.id]?.account_number || selection.data.account_number_masked || "••••"}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-sans uppercase">IFSC Code</span>
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {revealedData[selection.data.id]?.ifsc_code || selection.data.ifsc_code_masked || "••••"}
                      </span>
                    </div>
                    {selection.data.upi_id_masked && (
                      <div>
                        <span className="text-[10px] text-slate-400 block font-sans uppercase">UPI ID</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {revealedData[selection.data.id]?.upi_id || selection.data.upi_id_masked}
                        </span>
                      </div>
                    )}
                    {(revealedData[selection.data.id]?.account_holder || selection.data.account_holder) && (
                      <div>
                        <span className="text-[10px] text-slate-400 block font-sans uppercase">Holder Name</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {revealedData[selection.data.id]?.account_holder || selection.data.account_holder}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Statutory Reveal Button */}
                  <div>
                    {revealError && <p className="text-red-600 text-[11px] mb-2 font-medium">{revealError}</p>}
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={revealBusy}
                      onClick={() => openRevealModal(selection.data as TrailNode)}
                      className="w-full text-xs font-semibold gap-1.5 border-blue-300 text-blue-700 bg-blue-50 dark:bg-blue-900/40/50 hover:bg-blue-100"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      {revealedData[selection.data.id] ? "Re-reveal Account (Audited)" : "Unmask Statutory Details"}
                    </Button>
                    <span className="text-[10px] text-slate-400 block mt-1 text-center">
                      Writes append-only audit log `ACCOUNT_REVEALED`
                    </span>
                  </div>

                  {/* Financial Flow Summary */}
                  <div className="border-t pt-3 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500 dark:text-slate-400">Total Incoming:</span>
                      <span className="font-mono font-bold text-emerald-600">{formatCurrency(selection.data.incoming_total)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500 dark:text-slate-400">Total Outgoing:</span>
                      <span className="font-mono font-bold text-red-600">{formatCurrency(selection.data.outgoing_total)}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-xs">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Selected Transfer Edge</span>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-0.5">{formatCurrency(selection.data.amount)}</h4>
                    <p className="font-mono text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">UTR: {selection.data.utr_number || "N/A"}</p>
                  </div>

                  <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-lg border space-y-2 font-mono">
                    <div>
                      <span className="text-[10px] text-slate-400 block font-sans uppercase">Transaction Date</span>
                      <span>{selection.data.transaction_date ? new Date(selection.data.transaction_date).toLocaleString("en-IN") : "N/A"}</span>
                    </div>
                    {selection.data.rrn_number && (
                      <div>
                        <span className="text-[10px] text-slate-400 block font-sans uppercase">RRN Number</span>
                        <span>{selection.data.rrn_number}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-[10px] text-slate-400 block font-sans uppercase">Transfer Type</span>
                      <Badge variant="secondary" className="text-[10px] uppercase mt-0.5">{selection.data.transaction_type || "ONLINE"}</Badge>
                    </div>
                    {selection.data.withdrawal_flag && (
                      <div className="p-2 bg-red-50 dark:bg-red-900/40 border border-red-200 rounded text-red-800 font-sans text-xs font-bold">
                        ATM / Cash Withdrawal Flagged
                      </div>
                    )}
                    {selection.data.raw_narration && (
                      <div>
                        <span className="text-[10px] text-slate-400 block font-sans uppercase">Raw Narration</span>
                        <p className="text-[11px] text-slate-700 dark:text-slate-300 font-sans bg-white dark:bg-slate-900 p-1.5 rounded border">{selection.data.raw_narration}</p>
                      </div>
                    )}
                  </div>

                  {/* Risk Explanation Section */}
                  {(() => {
                    const riskJson = (selection.data as { risk_explanation_json?: { rules_fired?: string[] } }).risk_explanation_json;
                    const rules = riskJson?.rules_fired;
                    if (!rules?.length) return null;
                    return (
                    <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/40/50 border border-red-100 rounded-md">
                      <h5 className="font-semibold text-red-800 mb-1 flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" /> Risk Assessment
                      </h5>
                      <ul className="list-disc pl-4 space-y-1 text-red-700 text-[11px]">
                        {rules.map((rule: string, i: number) => (
                          <li key={i}>{rule}</li>
                        ))}
                      </ul>
                    </div>
                    );
                  })()}

                  {/* Provenance Metadata (`Sub-phase 10.2`) */}
                  <div className="border-t pt-3 space-y-2">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Provenance Record</span>
                    <div className="flex flex-wrap gap-1.5">
                      <Badge variant="outline" className="text-[10px] text-emerald-700 bg-emerald-50 dark:bg-emerald-900/40 border-emerald-300">
                        <CheckCircle className="h-3 w-3 mr-1 inline" />
                        {(selection.data.provenance?.confidence as string) || "medium"} confidence
                      </Badge>
                      <Badge variant="outline" className="text-[10px] text-blue-700 bg-blue-50 dark:bg-blue-900/40 border-blue-300">
                        {(selection.data.provenance?.data_source as string) || "manual_or_intake"}
                      </Badge>
                      {selection.data.provenance?.source_file && (
                        <Badge variant="outline" className="text-[10px] text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-950 border-slate-300">
                          {String(selection.data.provenance.source_file)}
                        </Badge>
                      )}
                    </div>
                    {showAdvanced && (
                      <div className="bg-slate-900 text-slate-200 p-2.5 rounded font-mono text-[10px] overflow-x-auto">
                        <pre>{JSON.stringify(selection.data.provenance || {}, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Statutory Reveal Modal */}
      {revealTargetNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl max-w-md w-full border overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="bg-slate-900 text-white p-4 flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-blue-400" />
                <h3 className="font-bold text-sm">Unmask Account Details</h3>
              </div>
              <button onClick={cancelReveal} disabled={revealBusy} className="text-slate-400 hover:text-white disabled:opacity-50">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                Provide statutory or investigative justification to reveal masked account details for{" "}
                <span className="font-semibold text-slate-900 dark:text-slate-100">
                  {revealTargetNode.bank_name || "this account"}
                </span>
                . This action is logged for audit compliance.
              </p>

              <div>
                <label htmlFor="reveal-reason" className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase mb-1.5">
                  Justification (min 10 characters)
                </label>
                <textarea
                  id="reveal-reason"
                  value={revealReason}
                  onChange={(e) => setRevealReason(e.target.value)}
                  disabled={revealBusy}
                  rows={4}
                  placeholder="Enter reason for unmasking this account..."
                  className="w-full text-sm px-3 py-2 border rounded-lg bg-white dark:bg-slate-950 resize-none focus:outline-hidden focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                />
                <span className="text-[10px] text-slate-400 mt-1 block">
                  {revealReason.trim().length}/10 characters minimum
                </span>
              </div>

              {revealError && (
                <p className="text-red-600 text-[11px] font-medium flex items-start gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  {revealError}
                </p>
              )}
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-950 border-t flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={cancelReveal} disabled={revealBusy}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={confirmReveal}
                disabled={revealBusy || revealReason.trim().length < 10}
              >
                {revealBusy ? "Revealing..." : "Confirm Reveal"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* EXPLAIN Sanity Check Modal */}
      {showExplainModal && explainPlan && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl max-w-2xl w-full border overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="bg-slate-900 text-white p-4 flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center gap-2">
                <HelpCircle className="h-5 w-5 text-blue-400" />
                <h3 className="font-bold text-sm">Query EXPLAIN Plan & Sanity Verification</h3>
              </div>
              <button onClick={() => setShowExplainModal(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[80vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border">
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold">Engine Source</span>
                  <span className="font-bold text-sm text-slate-900 dark:text-slate-100">{explainPlan.engine_source === "neo4j" ? "Neo4j Graph Database" : "Postgres Fallback Engine"}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold">Sanity Status</span>
                  {explainPlan.sanity_check_passed ? (
                    <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 font-bold">INDEX SANITY PASSED</Badge>
                  ) : (
                    <Badge className="bg-amber-100 text-amber-800 border-amber-300 font-bold">INDEX SCAN UNVERIFIED</Badge>
                  )}
                </div>
              </div>

              <div>
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase block mb-1">Indexes Utilized:</span>
                <div className="flex flex-wrap gap-1.5">
                  {explainPlan.indexes_used.map((idx, i) => (
                    <Badge key={i} variant="outline" className="font-mono bg-blue-50 dark:bg-blue-900/40 text-blue-800 border-blue-200">
                      {idx}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase block mb-1">Raw Query Statement:</span>
                <pre className="bg-slate-900 text-emerald-400 p-3 rounded-lg font-mono text-[11px] overflow-x-auto">
                  {explainPlan.query}
                </pre>
              </div>

              <div>
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase block mb-1">Execution Plan Tree:</span>
                <pre className="bg-slate-100 text-slate-800 dark:text-slate-200 p-3 rounded-lg font-mono text-[10px] overflow-x-auto max-h-60">
                  {JSON.stringify(explainPlan.execution_plan, null, 2)}
                </pre>
              </div>
            </div>

            <div className="p-4 bg-slate-50 dark:bg-slate-950 border-t flex justify-end">
              <Button size="sm" onClick={() => setShowExplainModal(false)}>Close Sanity Plan</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

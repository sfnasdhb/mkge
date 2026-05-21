import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape from "cytoscape";
import type { Core, ElementDefinition } from "cytoscape";
import type { DocumentGraph, GraphNode, EntityType, RelationType } from "@/shared/types";

const ENTITY_COLOR: Record<EntityType, string> = {
  DRUG: "#3b82f6",
  DISEASE: "#ef4444",
  SYMPTOM: "#f59e0b",
};

const ENTITY_LABEL: Record<EntityType, string> = {
  DRUG: "Thuốc",
  DISEASE: "Bệnh",
  SYMPTOM: "Triệu chứng",
};

const RELATION_LABEL: Record<RelationType, string> = {
  TREATS: "điều trị",
  CAUSES_SE: "tác dụng phụ",
  HAS_SYMPTOM: "có triệu chứng",
  COMORBID: "đồng mắc",
};

interface Props {
  graph: DocumentGraph;
}

export function GraphViewer({ graph }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);

  const elements = useMemo<ElementDefinition[]>(() => {
    const nodes: ElementDefinition[] = graph.nodes.map((n) => ({
      data: { id: n.id, label: n.name, type: n.type, raw: n },
    }));
    const edges: ElementDefinition[] = graph.edges.map((e) => ({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        label: RELATION_LABEL[e.type] ?? e.type,
      },
    }));
    return [...nodes, ...edges];
  }, [graph]);

  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#6b7280",
            label: "data(label)",
            color: "#e5e7eb",
            "text-outline-width": 2,
            "text-outline-color": "#0f172a",
            "font-size": 11,
            "text-valign": "bottom",
            "text-margin-y": 6,
            width: 36,
            height: 36,
            "border-width": 2,
            "border-color": "#0f172a",
          },
        },
        { selector: 'node[type="DRUG"]', style: { "background-color": ENTITY_COLOR.DRUG } },
        { selector: 'node[type="DISEASE"]', style: { "background-color": ENTITY_COLOR.DISEASE } },
        { selector: 'node[type="SYMPTOM"]', style: { "background-color": ENTITY_COLOR.SYMPTOM } },
        {
          selector: "node:selected",
          style: {
            "border-color": "#fbbf24",
            "border-width": 3,
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#475569",
            "target-arrow-color": "#475569",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 9,
            color: "#94a3b8",
            "text-background-color": "#0f172a",
            "text-background-opacity": 0.8,
            "text-background-padding": "2px",
          },
        },
        {
          selector: "edge:selected",
          style: {
            "line-color": "#fbbf24",
            "target-arrow-color": "#fbbf24",
          },
        },
      ],
      layout: {
        name: "cose",
        animate: false,
        nodeRepulsion: 8000,
        idealEdgeLength: 120,
        edgeElasticity: 100,
        gravity: 0.25,
      },
      wheelSensitivity: 0.2,
      minZoom: 0.2,
      maxZoom: 3,
    });

    cy.on("tap", "node", (evt) => {
      setSelected(evt.target.data("raw"));
    });
    cy.on("tap", (evt) => {
      if (evt.target === cy) setSelected(null);
    });

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [elements]);

  const fit = () => cyRef.current?.fit(undefined, 50);
  const zoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.2);
  const zoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full rounded-xl border border-border bg-card/40" />

      <div className="absolute left-3 top-3 space-y-2">
        <div className="rounded-lg border border-border bg-card/90 p-3 text-xs backdrop-blur">
          <p className="mb-2 font-medium text-foreground">Chú giải</p>
          <ul className="space-y-1">
            {(Object.keys(ENTITY_COLOR) as EntityType[]).map((t) => (
              <li key={t} className="flex items-center gap-2">
                <span
                  className="inline-block h-3 w-3 rounded-full"
                  style={{ backgroundColor: ENTITY_COLOR[t] }}
                />
                <span className="text-muted-foreground">{ENTITY_LABEL[t]}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="absolute right-3 top-3 flex flex-col gap-1">
        <button
          onClick={fit}
          className="rounded-md border border-border bg-card/90 px-2 py-1 text-xs backdrop-blur hover:bg-accent"
        >
          Fit
        </button>
        <button
          onClick={zoomIn}
          className="rounded-md border border-border bg-card/90 px-2 py-1 text-xs backdrop-blur hover:bg-accent"
        >
          +
        </button>
        <button
          onClick={zoomOut}
          className="rounded-md border border-border bg-card/90 px-2 py-1 text-xs backdrop-blur hover:bg-accent"
        >
          −
        </button>
      </div>

      {selected && (
        <div className="absolute bottom-3 left-3 right-3 max-w-md rounded-lg border border-border bg-card/95 p-4 backdrop-blur">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: ENTITY_COLOR[selected.type] }}
                />
                <span className="text-xs uppercase tracking-wider text-muted-foreground">
                  {ENTITY_LABEL[selected.type]}
                </span>
              </div>
              <p className="mt-1 text-sm font-semibold text-foreground">{selected.name}</p>
              {selected.description && (
                <p className="mt-2 text-xs text-muted-foreground">{selected.description}</p>
              )}
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

interface ClusterGraphProps {
  graphData: {
    nodes: any[];
    edges: any[];
  };
}

export const ClusterGraph: React.FC<ClusterGraphProps> = ({ graphData }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    const elements = [
      ...graphData.nodes.map(n => ({
        data: { id: n.id, label: n.label, type: n.type }
      })),
      ...graphData.edges.map(e => ({
        data: { source: e.source, target: e.target, label: e.label }
      }))
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'font-size': '10px',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'background-color': '#94a3b8',
            'width': 30,
            'height': 30,
          }
        },
        {
          selector: 'node[type="case"]',
          style: {
            'background-color': '#3b82f6',
            'shape': 'rectangle',
            'width': 40,
            'height': 40,
          }
        },
        {
          selector: 'node[type="account"]',
          style: {
            'background-color': '#f59e0b',
            'shape': 'ellipse',
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#cbd5e1',
            'curve-style': 'bezier',
          }
        }
      ],
      layout: {
        name: 'cose',
        padding: 50,
        nodeRepulsion: () => 4000,
        idealEdgeLength: () => 100,
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData]);

  return (
    <div className="w-full h-[500px] border rounded-lg bg-slate-50 dark:bg-slate-950 relative overflow-hidden shadow-inner">
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
};

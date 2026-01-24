'use client';

/**
 * PipelineCanvas Component
 * The main canvas where nodes are displayed and can be connected
 */

import React, {
  useRef,
  useState,
  useCallback,
  useEffect,
  MouseEvent as ReactMouseEvent,
} from 'react';
import { PipelineNode } from './PipelineNode';
import type {
  Pipeline,
  PipelineEdge,
  ToolDefinition,
  Position,
  PipelineExecutionState,
} from './types';

interface PipelineCanvasProps {
  pipeline: Pipeline;
  selectedNodeId: string | null;
  executionState: PipelineExecutionState;
  onSelectNode: (nodeId: string | null) => void;
  onDeleteNode: (nodeId: string) => void;
  onUpdateNodePosition: (nodeId: string, position: Position) => void;
  onAddEdge: (edge: Omit<PipelineEdge, 'id'>) => string | null;
  onDropTool: (tool: ToolDefinition, position: Position) => void;
  getNodeInputConnections: (nodeId: string) => PipelineEdge[];
}

interface DragState {
  type: 'node' | 'connection' | null;
  nodeId?: string;
  startPos?: Position;
  currentPos?: Position;
  sourceOutput?: string;
}

export function PipelineCanvas({
  pipeline,
  selectedNodeId,
  executionState,
  onSelectNode,
  onDeleteNode,
  onUpdateNodePosition,
  onAddEdge,
  onDropTool,
  getNodeInputConnections,
}: PipelineCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [dragState, setDragState] = useState<DragState>({ type: null });
  const [pendingConnection, setPendingConnection] = useState<{
    sourceNodeId: string;
    sourceOutput: string;
  } | null>(null);

  // Handle node dragging
  const handleNodeDragStart = useCallback(
    (nodeId: string, e: ReactMouseEvent) => {
      const node = pipeline.nodes.find((n) => n.id === nodeId);
      if (!node) return;

      setDragState({
        type: 'node',
        nodeId,
        startPos: { x: e.clientX - node.position.x, y: e.clientY - node.position.y },
      });
    },
    [pipeline.nodes]
  );

  // Handle connection dragging
  const handleConnectionStart = useCallback(
    (nodeId: string, outputName: string, e: ReactMouseEvent) => {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;

      const node = pipeline.nodes.find((n) => n.id === nodeId);
      if (!node) return;

      setPendingConnection({ sourceNodeId: nodeId, sourceOutput: outputName });
      setDragState({
        type: 'connection',
        nodeId,
        sourceOutput: outputName,
        startPos: { x: e.clientX - rect.left, y: e.clientY - rect.top },
        currentPos: { x: e.clientX - rect.left, y: e.clientY - rect.top },
      });
    },
    [pipeline.nodes]
  );

  const handleConnectionEnd = useCallback(
    (targetNodeId: string, targetInput: string) => {
      if (pendingConnection) {
        onAddEdge({
          sourceNodeId: pendingConnection.sourceNodeId,
          sourceOutput: pendingConnection.sourceOutput,
          targetNodeId,
          targetInput,
        });
        setPendingConnection(null);
        setDragState({ type: null });
      }
    },
    [pendingConnection, onAddEdge]
  );

  // Global mouse move handler
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragState.type) return;

      if (dragState.type === 'node' && dragState.nodeId && dragState.startPos) {
        onUpdateNodePosition(dragState.nodeId, {
          x: e.clientX - dragState.startPos.x,
          y: e.clientY - dragState.startPos.y,
        });
      }

      if (dragState.type === 'connection') {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
          setDragState((prev) => ({
            ...prev,
            currentPos: { x: e.clientX - rect.left, y: e.clientY - rect.top },
          }));
        }
      }
    };

    const handleMouseUp = () => {
      setDragState({ type: null });
      setPendingConnection(null);
    };

    if (dragState.type) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [dragState, onUpdateNodePosition]);

  // Handle canvas click to deselect
  const handleCanvasClick = useCallback(
    (e: ReactMouseEvent) => {
      if (e.target === canvasRef.current) {
        onSelectNode(null);
      }
    },
    [onSelectNode]
  );

  // Handle drop from tool palette
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const toolData = e.dataTransfer.getData('tool');
      if (toolData) {
        const tool: ToolDefinition = JSON.parse(toolData);
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
          onDropTool(tool, {
            x: e.clientX - rect.left - 90,
            y: e.clientY - rect.top - 20,
          });
        }
      }
    },
    [onDropTool]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  // Calculate edge path
  const getEdgePath = (edge: PipelineEdge): string => {
    const sourceNode = pipeline.nodes.find((n) => n.id === edge.sourceNodeId);
    const targetNode = pipeline.nodes.find((n) => n.id === edge.targetNodeId);
    if (!sourceNode || !targetNode) return '';

    const sourceOutputIndex = sourceNode.tool.outputs.findIndex(
      (o) => o.name === edge.sourceOutput
    );
    const targetInputIndex = targetNode.tool.inputs.findIndex(
      (i) => i.name === edge.targetInput
    );

    // Calculate start and end points
    const startX = sourceNode.position.x + 180;
    const startY =
      sourceNode.position.y +
      60 +
      (sourceNode.tool.inputs.length > 0 ? 30 + sourceNode.tool.inputs.length * 20 : 0) +
      sourceOutputIndex * 20 +
      10;

    const endX = targetNode.position.x;
    const endY = targetNode.position.y + 60 + targetInputIndex * 20 + 10;

    // Create curved path
    const midX = (startX + endX) / 2;
    return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
  };

  // Get pending connection path
  const getPendingConnectionPath = (): string => {
    if (!dragState.startPos || !dragState.currentPos || !dragState.nodeId) return '';

    const sourceNode = pipeline.nodes.find((n) => n.id === dragState.nodeId);
    if (!sourceNode) return '';

    const startX = dragState.startPos.x;
    const startY = dragState.startPos.y;
    const endX = dragState.currentPos.x;
    const endY = dragState.currentPos.y;

    const midX = (startX + endX) / 2;
    return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
  };

  return (
    <div
      ref={canvasRef}
      className="relative w-full h-full overflow-hidden"
      style={{
        backgroundColor: '#0d0d0d',
        backgroundImage: `
          linear-gradient(rgba(255, 107, 53, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255, 107, 53, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: '20px 20px',
      }}
      onClick={handleCanvasClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      {/* SVG layer for edges */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#ff6b35" />
          </marker>
        </defs>

        {/* Existing edges */}
        {pipeline.edges.map((edge) => (
          <path
            key={edge.id}
            d={getEdgePath(edge)}
            fill="none"
            stroke="#ff6b35"
            strokeWidth={2}
            strokeOpacity={0.6}
            markerEnd="url(#arrowhead)"
          />
        ))}

        {/* Pending connection */}
        {dragState.type === 'connection' && (
          <path
            d={getPendingConnectionPath()}
            fill="none"
            stroke="#ff6b35"
            strokeWidth={2}
            strokeDasharray="5,5"
            strokeOpacity={0.8}
          />
        )}
      </svg>

      {/* Nodes layer */}
      {pipeline.nodes.map((node) => (
        <PipelineNode
          key={node.id}
          node={node}
          isSelected={selectedNodeId === node.id}
          isRunning={executionState.currentNodeId === node.id}
          inputConnections={getNodeInputConnections(node.id)}
          onSelect={onSelectNode}
          onDelete={onDeleteNode}
          onDragStart={handleNodeDragStart}
          onConnectionStart={handleConnectionStart}
          onConnectionEnd={handleConnectionEnd}
        />
      ))}

      {/* Empty state */}
      {pipeline.nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div
              className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center"
              style={{ backgroundColor: 'rgba(255, 107, 53, 0.1)' }}
            >
              <svg
                className="w-8 h-8"
                style={{ color: '#ff6b35' }}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                />
              </svg>
            </div>
            <p className="text-gray-500 text-sm">
              Drag tools from the palette to build your pipeline
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

/**
 * PipelineCanvas Component
 * The main canvas where nodes are displayed and can be connected.
 * Uses simplified side ports for image/mask connections.
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
import { getPortConfig } from './utils/connectionUtils';

interface PipelineCanvasProps {
  pipeline: Pipeline;
  selectedNodeId: string | null;
  executionState: PipelineExecutionState;
  onSelectNode: (nodeId: string | null) => void;
  onDeleteNode: (nodeId: string) => void;
  onUpdateNodePosition: (nodeId: string, position: Position) => void;
  onAddEdge: (sourceNodeId: string, targetNodeId: string) => string | null;
  onDropTool: (tool: ToolDefinition, position: Position) => void;
  getNodeInputConnections: (nodeId: string) => PipelineEdge[];
  getNodeOutputConnections: (nodeId: string) => PipelineEdge[];
}

interface DragState {
  type: 'node' | 'connection' | null;
  nodeId?: string;
  startPos?: Position;
  currentPos?: Position;
}

// Constants for node dimensions (must match actual CSS)
const NODE_WIDTH = 180;
const NODE_HEADER_HEIGHT = 36; // Header with py-2
const NODE_TITLE_HEIGHT = 33; // Tool name with py-2 + border
const NODE_CONNECTABLE_ROW = 29; // Connectable input row with py-1.5 + border
const NODE_ROW_HEIGHT = 22; // Each parameter/output row
const NODE_SECTION_PADDING = 16; // Section py-2 padding
const NODE_SECTION_HEADER = 14; // "Parameters", "Outputs" label height

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
  getNodeOutputConnections,
}: PipelineCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [dragState, setDragState] = useState<DragState>({ type: null });
  const [pendingConnection, setPendingConnection] = useState<{
    sourceNodeId: string;
  } | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // Calculate node height based on its content
  const getNodeHeight = useCallback((node: typeof pipeline.nodes[0]): number => {
    const portConfig = getPortConfig(node.tool);
    let height = NODE_HEADER_HEIGHT + NODE_TITLE_HEIGHT;

    // Connectable input row (with py-1.5 padding)
    if (portConfig.hasInputPort) {
      height += NODE_CONNECTABLE_ROW;
    }

    // Non-connectable inputs (parameters section)
    const parameterInputs = node.tool.inputs.filter(i =>
      !['IMAGE', 'MASK', 'ARRAY'].includes(i.type)
    );
    if (parameterInputs.length > 0) {
      height += NODE_SECTION_PADDING + NODE_SECTION_HEADER + parameterInputs.length * NODE_ROW_HEIGHT;
    }

    // Outputs section
    if (node.tool.outputs.length > 0) {
      height += NODE_SECTION_PADDING + NODE_SECTION_HEADER + node.tool.outputs.length * NODE_ROW_HEIGHT;
    }

    return height;
  }, []);

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

  // Handle connection dragging from output port
  const handleConnectionStart = useCallback(
    (nodeId: string, e: ReactMouseEvent) => {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;

      const node = pipeline.nodes.find((n) => n.id === nodeId);
      if (!node) return;

      // Verify this node has an output port
      const portConfig = getPortConfig(node.tool);
      if (!portConfig.hasOutputPort) return;

      setPendingConnection({ sourceNodeId: nodeId });
      setDragState({
        type: 'connection',
        nodeId,
        startPos: { x: e.clientX - rect.left, y: e.clientY - rect.top },
        currentPos: { x: e.clientX - rect.left, y: e.clientY - rect.top },
      });
    },
    [pipeline.nodes]
  );

  // Track which node's input port is being hovered
  const handleInputPortHover = useCallback((nodeId: string | null) => {
    setHoveredNodeId(nodeId);
  }, []);

  // Use refs to access latest values in event handlers
  const pendingConnectionRef = useRef(pendingConnection);
  const hoveredNodeIdRef = useRef(hoveredNodeId);
  pendingConnectionRef.current = pendingConnection;
  hoveredNodeIdRef.current = hoveredNodeId;

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
      // If we were dragging a connection and hovering over a node's input, create the edge
      if (pendingConnectionRef.current && hoveredNodeIdRef.current) {
        onAddEdge(
          pendingConnectionRef.current.sourceNodeId,
          hoveredNodeIdRef.current
        );
      }
      setDragState({ type: null });
      setPendingConnection(null);
      setHoveredNodeId(null);
    };

    if (dragState.type) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [dragState, onUpdateNodePosition, onAddEdge]);

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

  // Calculate edge path between two nodes (side ports)
  const getEdgePath = (edge: PipelineEdge): string => {
    const sourceNode = pipeline.nodes.find((n) => n.id === edge.sourceNodeId);
    const targetNode = pipeline.nodes.find((n) => n.id === edge.targetNodeId);
    if (!sourceNode || !targetNode) return '';

    const sourceHeight = getNodeHeight(sourceNode);
    const targetHeight = getNodeHeight(targetNode);

    // Right side of source node (output port), vertically centered
    const startX = sourceNode.position.x + NODE_WIDTH;
    const startY = sourceNode.position.y + sourceHeight / 2;

    // Left side of target node (input port), vertically centered
    const endX = targetNode.position.x;
    const endY = targetNode.position.y + targetHeight / 2;

    // Create smooth bezier curve
    const controlPointOffset = Math.min(Math.abs(endX - startX) / 2, 80);
    return `M ${startX} ${startY} C ${startX + controlPointOffset} ${startY}, ${endX - controlPointOffset} ${endY}, ${endX} ${endY}`;
  };

  // Get pending connection path (during drag)
  const getPendingConnectionPath = (): string => {
    if (!dragState.startPos || !dragState.currentPos || !dragState.nodeId) return '';

    const sourceNode = pipeline.nodes.find((n) => n.id === dragState.nodeId);
    if (!sourceNode) return '';

    const sourceHeight = getNodeHeight(sourceNode);

    // Start from the right side port
    const startX = sourceNode.position.x + NODE_WIDTH;
    const startY = sourceNode.position.y + sourceHeight / 2;
    const endX = dragState.currentPos.x;
    const endY = dragState.currentPos.y;

    const controlPointOffset = Math.min(Math.abs(endX - startX) / 2, 80);
    return `M ${startX} ${startY} C ${startX + controlPointOffset} ${startY}, ${endX - controlPointOffset} ${endY}, ${endX} ${endY}`;
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
          outputConnections={getNodeOutputConnections(node.id)}
          isInputPortHovered={hoveredNodeId === node.id && pendingConnection !== null}
          onSelect={onSelectNode}
          onDelete={onDeleteNode}
          onDragStart={handleNodeDragStart}
          onConnectionStart={handleConnectionStart}
          onInputPortHover={handleInputPortHover}
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

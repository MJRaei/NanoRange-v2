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
  WheelEvent as ReactWheelEvent,
} from 'react';
import { PipelineNode } from './PipelineNode';
import type {
  Pipeline,
  PipelineEdge,
  ToolDefinition,
  Position,
  PipelineExecutionState,
  CanvasState,
} from './types';
import { getPortConfig } from './utils/connectionUtils';

// Zoom constraints
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 2;
const ZOOM_SENSITIVITY = 0.001;

interface PipelineCanvasProps {
  pipeline: Pipeline;
  selectedNodeId: string | null;
  executionState: PipelineExecutionState;
  onSelectNode: (nodeId: string | null) => void;
  onDeleteNode: (nodeId: string) => void;
  onUpdateNodePosition: (nodeId: string, position: Position) => void;
  onAddEdge: (sourceNodeId: string, targetNodeId: string) => string | null;
  onRemoveEdge: (edgeId: string) => void;
  onDropTool: (tool: ToolDefinition, position: Position) => void;
  getNodeInputConnections: (nodeId: string) => PipelineEdge[];
  getNodeOutputConnections: (nodeId: string) => PipelineEdge[];
}

// Expansion state for node sections
interface NodeExpansionState {
  params: boolean;
  outputs: boolean;
}

// Maximum items to show when collapsed
const MAX_VISIBLE_ITEMS = 2;

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

// Snap radius for easier connection (pixels)
const CONNECTION_SNAP_RADIUS = 40;

export function PipelineCanvas({
  pipeline,
  selectedNodeId,
  executionState,
  onSelectNode,
  onDeleteNode,
  onUpdateNodePosition,
  onAddEdge,
  onRemoveEdge,
  onDropTool,
  getNodeInputConnections,
  getNodeOutputConnections,
}: PipelineCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [dragState, setDragState] = useState<DragState>({ type: null });
  const [pendingConnection, setPendingConnection] = useState<{
    sourceNodeId: string;
  } | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [snapTargetNodeId, setSnapTargetNodeId] = useState<string | null>(null);
  const [nodeExpansion, setNodeExpansion] = useState<Record<string, NodeExpansionState>>({});
  const [hoveredEdgeId, setHoveredEdgeId] = useState<string | null>(null);

  // Canvas zoom and pan state
  const [canvasState, setCanvasState] = useState<CanvasState>({ zoom: 1, pan: { x: 0, y: 0 } });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState<Position | null>(null);
  const [spacePressed, setSpacePressed] = useState(false);

  // Convert screen coordinates to canvas coordinates (accounting for zoom and pan)
  const screenToCanvas = useCallback((screenX: number, screenY: number): Position => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return { x: screenX, y: screenY };
    const x = (screenX - rect.left - canvasState.pan.x) / canvasState.zoom;
    const y = (screenY - rect.top - canvasState.pan.y) / canvasState.zoom;
    return { x, y };
  }, [canvasState]);

  // Get expansion state for a node (defaults to collapsed)
  const getNodeExpansion = useCallback((nodeId: string): NodeExpansionState => {
    return nodeExpansion[nodeId] || { params: false, outputs: false };
  }, [nodeExpansion]);

  // Toggle expansion state for a node section
  const toggleNodeExpansion = useCallback((nodeId: string, section: 'params' | 'outputs') => {
    setNodeExpansion(prev => ({
      ...prev,
      [nodeId]: {
        ...prev[nodeId] || { params: false, outputs: false },
        [section]: !(prev[nodeId]?.[section] ?? false)
      }
    }));
  }, []);

  // Calculate node height based on its content and expansion state
  const getNodeHeight = useCallback((node: typeof pipeline.nodes[0]): number => {
    const portConfig = getPortConfig(node.tool);
    const expansion = getNodeExpansion(node.id);
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
      const visibleParams = expansion.params ? parameterInputs.length : Math.min(parameterInputs.length, MAX_VISIBLE_ITEMS);
      const hasMoreParams = parameterInputs.length > MAX_VISIBLE_ITEMS;
      height += NODE_SECTION_PADDING + NODE_SECTION_HEADER + visibleParams * NODE_ROW_HEIGHT;
      if (hasMoreParams) {
        height += NODE_ROW_HEIGHT; // "Show more/less" button
      }
    }

    // Outputs section
    if (node.tool.outputs.length > 0) {
      const visibleOutputs = expansion.outputs ? node.tool.outputs.length : Math.min(node.tool.outputs.length, MAX_VISIBLE_ITEMS);
      const hasMoreOutputs = node.tool.outputs.length > MAX_VISIBLE_ITEMS;
      height += NODE_SECTION_PADDING + NODE_SECTION_HEADER + visibleOutputs * NODE_ROW_HEIGHT;
      if (hasMoreOutputs) {
        height += NODE_ROW_HEIGHT; // "Show more/less" button
      }
    }

    return height;
  }, [getNodeExpansion]);

  // Find the closest node with a valid input port within snap radius
  const findSnapTarget = useCallback(
    (mousePos: Position, sourceNodeId: string): string | null => {
      let closestNodeId: string | null = null;
      let closestDistance = CONNECTION_SNAP_RADIUS;

      for (const node of pipeline.nodes) {
        // Can't connect to self
        if (node.id === sourceNodeId) continue;

        // Check if this node has an input port
        const portConfig = getPortConfig(node.tool);
        if (!portConfig.hasInputPort) continue;

        // Use the same height calculation as getNodeHeight
        const nodeHeight = getNodeHeight(node);

        // Input port is on the left side, vertically centered
        const portX = node.position.x;
        const portY = node.position.y + nodeHeight / 2;

        // Calculate distance from mouse to port
        const dx = mousePos.x - portX;
        const dy = mousePos.y - portY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < closestDistance) {
          closestDistance = distance;
          closestNodeId = node.id;
        }
      }

      return closestNodeId;
    },
    [pipeline.nodes, getNodeHeight]
  );

  // Handle node dragging
  const handleNodeDragStart = useCallback(
    (nodeId: string, e: ReactMouseEvent) => {
      const node = pipeline.nodes.find((n) => n.id === nodeId);
      if (!node) return;

      // Convert mouse position to canvas coordinates and calculate offset
      const canvasPos = screenToCanvas(e.clientX, e.clientY);
      setDragState({
        type: 'node',
        nodeId,
        startPos: { x: canvasPos.x - node.position.x, y: canvasPos.y - node.position.y },
      });
    },
    [pipeline.nodes, screenToCanvas]
  );

  // Handle connection dragging from output port
  const handleConnectionStart = useCallback(
    (nodeId: string, e: ReactMouseEvent) => {
      const node = pipeline.nodes.find((n) => n.id === nodeId);
      if (!node) return;

      // Verify this node has an output port
      const portConfig = getPortConfig(node.tool);
      if (!portConfig.hasOutputPort) return;

      // Convert to canvas coordinates
      const canvasPos = screenToCanvas(e.clientX, e.clientY);
      setPendingConnection({ sourceNodeId: nodeId });
      setDragState({
        type: 'connection',
        nodeId,
        startPos: canvasPos,
        currentPos: canvasPos,
      });
    },
    [pipeline.nodes, screenToCanvas]
  );

  // Track which node's input port is being hovered
  const handleInputPortHover = useCallback((nodeId: string | null) => {
    setHoveredNodeId(nodeId);
  }, []);

  // Use refs to access latest values in event handlers
  const pendingConnectionRef = useRef(pendingConnection);
  const hoveredNodeIdRef = useRef(hoveredNodeId);
  const dragStateRef = useRef(dragState);
  const findSnapTargetRef = useRef(findSnapTarget);
  const screenToCanvasRef = useRef(screenToCanvas);
  pendingConnectionRef.current = pendingConnection;
  hoveredNodeIdRef.current = hoveredNodeId;
  dragStateRef.current = dragState;
  findSnapTargetRef.current = findSnapTarget;
  screenToCanvasRef.current = screenToCanvas;

  // Global mouse move handler
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragState.type) return;

      if (dragState.type === 'node' && dragState.nodeId && dragState.startPos) {
        // Convert mouse position to canvas coordinates
        const canvasPos = screenToCanvasRef.current(e.clientX, e.clientY);
        onUpdateNodePosition(dragState.nodeId, {
          x: canvasPos.x - dragState.startPos.x,
          y: canvasPos.y - dragState.startPos.y,
        });
      }

      if (dragState.type === 'connection' && dragState.nodeId) {
        // Convert to canvas coordinates
        const currentPos = screenToCanvasRef.current(e.clientX, e.clientY);
        setDragState((prev) => ({
          ...prev,
          currentPos,
        }));
        // Update snap target for visual feedback
        const snapTarget = findSnapTargetRef.current(currentPos, dragState.nodeId);
        setSnapTargetNodeId(snapTarget);
      }
    };

    const handleMouseUp = () => {
      // If we were dragging a connection, try to create the edge
      if (pendingConnectionRef.current) {
        let targetNodeId = hoveredNodeIdRef.current;

        // If not directly hovering, try to snap to nearby port
        if (!targetNodeId && dragStateRef.current.currentPos) {
          targetNodeId = findSnapTargetRef.current(
            dragStateRef.current.currentPos,
            pendingConnectionRef.current.sourceNodeId
          );
        }

        if (targetNodeId) {
          onAddEdge(pendingConnectionRef.current.sourceNodeId, targetNodeId);
        }
      }
      setDragState({ type: null });
      setPendingConnection(null);
      setHoveredNodeId(null);
      setSnapTargetNodeId(null);
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

  // Keyboard event handlers for space key (pan mode)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeElement = document.activeElement;
      const isTyping = activeElement instanceof HTMLInputElement ||
                       activeElement instanceof HTMLTextAreaElement ||
                       activeElement?.getAttribute('contenteditable') === 'true';

      if (e.code === 'Space' && !e.repeat && !isTyping) {
        e.preventDefault();
        setSpacePressed(true);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setSpacePressed(false);
        setIsPanning(false);
        setPanStart(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // Handle mouse wheel for zooming
  const handleWheel = useCallback((e: ReactWheelEvent) => {
    e.preventDefault();
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    // Mouse position relative to canvas
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Calculate new zoom level
    const delta = -e.deltaY * ZOOM_SENSITIVITY;
    const newZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, canvasState.zoom * (1 + delta)));
    const zoomRatio = newZoom / canvasState.zoom;

    // Adjust pan to zoom towards mouse position
    const newPanX = mouseX - (mouseX - canvasState.pan.x) * zoomRatio;
    const newPanY = mouseY - (mouseY - canvasState.pan.y) * zoomRatio;

    setCanvasState({
      zoom: newZoom,
      pan: { x: newPanX, y: newPanY }
    });
  }, [canvasState]);

  // Handle mouse down for panning (middle button, space+left click, or left click on background)
  const handleCanvasMouseDown = useCallback((e: ReactMouseEvent) => {
    // Middle mouse button or space+left click starts panning anywhere
    if (e.button === 1 || (spacePressed && e.button === 0)) {
      e.preventDefault();
      setIsPanning(true);
      setPanStart({ x: e.clientX - canvasState.pan.x, y: e.clientY - canvasState.pan.y });
    }
    // Left click on canvas background or content area (not on a node) also starts panning
    else if (e.button === 0 && (e.target === canvasRef.current || e.target === contentRef.current)) {
      e.preventDefault();
      setIsPanning(true);
      setPanStart({ x: e.clientX - canvasState.pan.x, y: e.clientY - canvasState.pan.y });
    }
  }, [spacePressed, canvasState.pan]);

  // Global pan move handler
  useEffect(() => {
    if (!isPanning || !panStart) return;

    const handleMouseMove = (e: MouseEvent) => {
      setCanvasState(prev => ({
        ...prev,
        pan: { x: e.clientX - panStart.x, y: e.clientY - panStart.y }
      }));
    };

    const handleMouseUp = () => {
      setIsPanning(false);
      setPanStart(null);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isPanning, panStart]);

  // Reset zoom and pan
  const resetView = useCallback(() => {
    setCanvasState({ zoom: 1, pan: { x: 0, y: 0 } });
  }, []);

  // Handle canvas click to deselect (but not when panning)
  const handleCanvasClick = useCallback(
    (e: ReactMouseEvent) => {
      // Don't deselect if we just finished panning or if space is pressed
      if (spacePressed || isPanning) return;
      if (e.target === canvasRef.current || e.target === contentRef.current) {
        onSelectNode(null);
      }
    },
    [onSelectNode, spacePressed, isPanning]
  );

  // Handle drop from tool palette
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const toolData = e.dataTransfer.getData('tool');
      if (toolData) {
        const tool: ToolDefinition = JSON.parse(toolData);
        // Convert drop position to canvas coordinates
        const canvasPos = screenToCanvas(e.clientX, e.clientY);
        onDropTool(tool, {
          x: canvasPos.x - 90,
          y: canvasPos.y - 20,
        });
      }
    },
    [onDropTool, screenToCanvas]
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

  // Grid size adjusted for zoom
  const gridSize = 20 * canvasState.zoom;

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
        backgroundSize: `${gridSize}px ${gridSize}px`,
        backgroundPosition: `${canvasState.pan.x}px ${canvasState.pan.y}px`,
        cursor: isPanning ? 'grabbing' : 'grab',
      }}
      onClick={handleCanvasClick}
      onMouseDown={handleCanvasMouseDown}
      onWheel={handleWheel}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      {/* Transformable content layer */}
      <div
        ref={contentRef}
        className="absolute"
        style={{
          transform: `translate(${canvasState.pan.x}px, ${canvasState.pan.y}px) scale(${canvasState.zoom})`,
          transformOrigin: '0 0',
          width: '10000px',
          height: '10000px',
        }}
      >
        {/* SVG layer for edges */}
        <svg
          className="absolute pointer-events-none"
          style={{ width: '10000px', height: '10000px' }}
        >
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
          {pipeline.edges.map((edge) => {
            const isHovered = hoveredEdgeId === edge.id;
            return (
              <g key={edge.id} style={{ cursor: 'pointer' }}>
                {/* Invisible wider hit area for easier clicking */}
                <path
                  d={getEdgePath(edge)}
                  fill="none"
                  stroke="transparent"
                  strokeWidth={16}
                  style={{ pointerEvents: 'stroke' }}
                  onMouseEnter={() => setHoveredEdgeId(edge.id)}
                  onMouseLeave={() => setHoveredEdgeId(null)}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveEdge(edge.id);
                  }}
                />
                {/* Visible edge */}
                <path
                  d={getEdgePath(edge)}
                  fill="none"
                  stroke={isHovered ? '#ff4444' : '#ff6b35'}
                  strokeWidth={2}
                  strokeOpacity={isHovered ? 1 : 0.6}
                  markerEnd="url(#arrowhead)"
                  style={{ pointerEvents: 'none', transition: 'stroke 0.15s, stroke-opacity 0.15s' }}
                />
              </g>
            );
          })}

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
            isInputPortHovered={(hoveredNodeId === node.id || snapTargetNodeId === node.id) && pendingConnection !== null}
            expansion={getNodeExpansion(node.id)}
            onToggleExpansion={(section) => toggleNodeExpansion(node.id, section)}
            onSelect={onSelectNode}
            onDelete={onDeleteNode}
            onDragStart={handleNodeDragStart}
            onConnectionStart={handleConnectionStart}
            onInputPortHover={handleInputPortHover}
          />
        ))}
      </div>

      {/* Zoom controls (fixed position, outside transform) */}
      <div className="absolute bottom-4 right-4 flex items-center gap-2 bg-neutral-800/90 rounded-lg px-3 py-2 shadow-lg">
        <button
          onClick={() => setCanvasState(prev => ({ ...prev, zoom: Math.max(MIN_ZOOM, prev.zoom - 0.1) }))}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-neutral-700 text-gray-300 hover:text-white transition-colors"
          title="Zoom out"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        <span className="text-gray-300 text-sm min-w-[48px] text-center">
          {Math.round(canvasState.zoom * 100)}%
        </span>
        <button
          onClick={() => setCanvasState(prev => ({ ...prev, zoom: Math.min(MAX_ZOOM, prev.zoom + 0.1) }))}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-neutral-700 text-gray-300 hover:text-white transition-colors"
          title="Zoom in"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <div className="w-px h-4 bg-neutral-600 mx-1" />
        <button
          onClick={resetView}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-neutral-700 text-gray-300 hover:text-white transition-colors"
          title="Reset view"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </button>
      </div>

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

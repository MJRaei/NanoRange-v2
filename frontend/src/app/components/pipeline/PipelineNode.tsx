'use client';

/**
 * PipelineNode Component
 * Renders a single tool node in the pipeline canvas with simplified side ports
 * for image/mask connections.
 */

import { useCallback, useMemo, MouseEvent as ReactMouseEvent } from 'react';
import { NodePort } from './NodePort';
import type { PipelineNode as PipelineNodeType, PipelineEdge } from './types';
import {
  getPortConfig,
  getInputSatisfactionStatus,
  isConnectableType,
  type SatisfactionStatus,
} from './utils/connectionUtils';

interface ExpansionState {
  params: boolean;
  outputs: boolean;
}

// Maximum items to show when collapsed
const MAX_VISIBLE_ITEMS = 2;

interface PipelineNodeProps {
  node: PipelineNodeType;
  isSelected: boolean;
  isRunning?: boolean;
  inputConnections: PipelineEdge[];
  outputConnections: PipelineEdge[];
  isInputPortHovered?: boolean;
  expansion: ExpansionState;
  onToggleExpansion: (section: 'params' | 'outputs') => void;
  onSelect: (nodeId: string) => void;
  onDelete: (nodeId: string) => void;
  onDragStart: (nodeId: string, e: ReactMouseEvent) => void;
  onConnectionStart: (nodeId: string, e: ReactMouseEvent) => void;
  onInputPortHover: (nodeId: string | null) => void;
}

const categoryColors: Record<string, string> = {
  io: '#3b82f6',
  preprocessing: '#8b5cf6',
  segmentation: '#ec4899',
  ml_segmentation: '#c026d3',
  measurement: '#10b981',
  ml: '#f59e0b',
  vlm: '#6366f1',
  default: '#6b7280',
};

function SatisfactionIndicator({ status }: { status: SatisfactionStatus }) {
  const colors = {
    satisfied: 'bg-green-500',
    unsatisfied: 'bg-red-500',
    optional: 'bg-gray-500',
  };

  return (
    <div
      className={`w-1.5 h-1.5 rounded-full ${colors[status]}`}
      title={status === 'satisfied' ? 'Has value' : status === 'unsatisfied' ? 'Required' : 'Optional'}
    />
  );
}

export function PipelineNode({
  node,
  isSelected,
  isRunning,
  inputConnections,
  outputConnections,
  isInputPortHovered,
  expansion,
  onToggleExpansion,
  onSelect,
  onDelete,
  onDragStart,
  onConnectionStart,
  onInputPortHover,
}: PipelineNodeProps) {
  const categoryColor = categoryColors[node.tool.category] || categoryColors.default;
  const portConfig = useMemo(() => getPortConfig(node.tool), [node.tool]);

  // Check if the primary input is connected
  const isPrimaryInputConnected = useMemo(() => {
    if (!portConfig.primaryInput) return false;
    return inputConnections.some(e => e.targetInput === portConfig.primaryInput?.name);
  }, [portConfig.primaryInput, inputConnections]);

  // Check if the primary output is connected
  const isPrimaryOutputConnected = useMemo(() => {
    if (!portConfig.primaryOutput) return false;
    return outputConnections.some(e => e.sourceOutput === portConfig.primaryOutput?.name);
  }, [portConfig.primaryOutput, outputConnections]);

  const handleMouseDown = useCallback(
    (e: ReactMouseEvent) => {
      if (e.button !== 0) return;
      e.stopPropagation();
      onSelect(node.id);
      onDragStart(node.id, e);
    },
    [node.id, onSelect, onDragStart]
  );

  const handleDelete = useCallback(
    (e: ReactMouseEvent) => {
      e.stopPropagation();
      onDelete(node.id);
    },
    [node.id, onDelete]
  );

  const handleOutputPortMouseDown = useCallback(
    (e: ReactMouseEvent) => {
      e.stopPropagation();
      onConnectionStart(node.id, e);
    },
    [node.id, onConnectionStart]
  );

  const handleInputPortEnter = useCallback(() => {
    onInputPortHover(node.id);
  }, [node.id, onInputPortHover]);

  const handleInputPortLeave = useCallback(() => {
    onInputPortHover(null);
  }, [onInputPortHover]);

  // Get satisfaction status for each input
  const getStatus = useCallback(
    (inputName: string) => {
      const input = node.tool.inputs.find(i => i.name === inputName);
      if (!input) return 'optional' as SatisfactionStatus;
      return getInputSatisfactionStatus(
        input,
        node.inputs[inputName],
        inputConnections,
        inputName
      );
    },
    [node.tool.inputs, node.inputs, inputConnections]
  );

  // Filter inputs: non-connectable inputs are shown in the node
  const displayInputs = node.tool.inputs.filter(input => !isConnectableType(input.type));

  return (
    <div
      className="absolute select-none group"
      style={{
        left: node.position.x,
        top: node.position.y,
        zIndex: isSelected ? 10 : 1,
      }}
      onMouseDown={handleMouseDown}
    >
      <div
        className={`
          relative rounded-lg shadow-lg transition-all duration-150
          ${isRunning ? 'animate-pulse' : ''}
        `}
        style={{
          backgroundColor: '#1a1a1a',
          border: `2px solid ${isSelected ? categoryColor : 'rgba(255, 255, 255, 0.1)'}`,
          minWidth: '180px',
          boxShadow: isSelected ? `0 0 0 2px ${categoryColor}40` : undefined,
        }}
      >
        {/* Left Port (Input) - positioned on the border */}
        {portConfig.hasInputPort && portConfig.primaryInput && (
          <NodePort
            side="left"
            isConnected={isPrimaryInputConnected}
            isHovered={isInputPortHovered}
            onMouseEnter={handleInputPortEnter}
            onMouseLeave={handleInputPortLeave}
          />
        )}

        {/* Right Port (Output) - positioned on the border */}
        {portConfig.hasOutputPort && portConfig.primaryOutput && (
          <NodePort
            side="right"
            isConnected={isPrimaryOutputConnected}
            onMouseDown={handleOutputPortMouseDown}
          />
        )}

        {/* Header */}
        <div
          className="px-3 py-2 rounded-t-md flex items-center justify-between"
          style={{ backgroundColor: categoryColor }}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-white opacity-70">
              {node.tool.category.toUpperCase()}
            </span>
          </div>
          <button
            onClick={handleDelete}
            className="w-5 h-5 rounded flex items-center justify-center hover:bg-black/20 transition-colors"
          >
            <svg
              className="w-3 h-3 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Tool name */}
        <div className="px-3 py-2 border-b border-white/10">
          <h3 className="text-sm font-semibold text-white">{node.tool.name}</h3>
        </div>

        {/* Connectable input status (if has input port) */}
        {portConfig.hasInputPort && portConfig.primaryInput && (
          <div className="px-3 py-1.5 border-b border-white/5">
            <div className="flex items-center gap-2">
              <SatisfactionIndicator status={getStatus(portConfig.primaryInput.name)} />
              <span className="text-xs text-gray-400">
                {portConfig.primaryInput.name}
              </span>
              <span className="text-[10px] text-gray-600 ml-auto">
                {isPrimaryInputConnected ? 'connected' : 'not connected'}
              </span>
            </div>
          </div>
        )}

        {/* Other Inputs (non-connectable) - Collapsible */}
        {displayInputs.length > 0 && (
          <div className="px-3 py-2 space-y-1">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">
              Parameters
            </span>
            {(expansion.params ? displayInputs : displayInputs.slice(0, MAX_VISIBLE_ITEMS)).map((input) => (
              <div
                key={input.name}
                className="flex items-center gap-2"
              >
                <SatisfactionIndicator status={getStatus(input.name)} />
                <span className="text-xs text-gray-400">
                  {input.name}
                </span>
              </div>
            ))}
            {displayInputs.length > MAX_VISIBLE_ITEMS && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleExpansion('params');
                }}
                className="text-[10px] text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1 mt-1"
              >
                <svg
                  className={`w-3 h-3 transition-transform ${expansion.params ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                {expansion.params ? 'Show less' : `+${displayInputs.length - MAX_VISIBLE_ITEMS} more`}
              </button>
            )}
          </div>
        )}

        {/* Outputs (no circles, just info) - Collapsible */}
        {node.tool.outputs.length > 0 && (
          <div className="px-3 py-2 space-y-1 border-t border-white/5">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">
              Outputs
            </span>
            {(expansion.outputs ? node.tool.outputs : node.tool.outputs.slice(0, MAX_VISIBLE_ITEMS)).map((output) => (
              <div
                key={output.name}
                className="flex items-center gap-2 justify-end"
              >
                <span className="text-xs text-gray-400">{output.name}</span>
              </div>
            ))}
            {node.tool.outputs.length > MAX_VISIBLE_ITEMS && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleExpansion('outputs');
                }}
                className="text-[10px] text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1 mt-1 ml-auto"
              >
                <svg
                  className={`w-3 h-3 transition-transform ${expansion.outputs ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                {expansion.outputs ? 'Show less' : `+${node.tool.outputs.length - MAX_VISIBLE_ITEMS} more`}
              </button>
            )}
          </div>
        )}

        {/* Running indicator */}
        {isRunning && (
          <div
            className="absolute -top-1 -right-1 w-3 h-3 rounded-full"
            style={{ backgroundColor: '#ff6b35' }}
          />
        )}
      </div>
    </div>
  );
}

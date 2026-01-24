'use client';

/**
 * PipelineNode Component
 * Renders a single tool node in the pipeline canvas
 */

import { useCallback, MouseEvent as ReactMouseEvent } from 'react';
import type { PipelineNode as PipelineNodeType, PipelineEdge } from './types';

interface PipelineNodeProps {
  node: PipelineNodeType;
  isSelected: boolean;
  isRunning?: boolean;
  inputConnections: PipelineEdge[];
  onSelect: (nodeId: string) => void;
  onDelete: (nodeId: string) => void;
  onDragStart: (nodeId: string, e: ReactMouseEvent) => void;
  onConnectionStart: (nodeId: string, outputName: string, e: ReactMouseEvent) => void;
  onInputHover: (nodeId: string | null, inputName: string | null) => void;
}

const categoryColors: Record<string, string> = {
  io: '#3b82f6',
  preprocessing: '#8b5cf6',
  segmentation: '#ec4899',
  measurement: '#10b981',
  ml: '#f59e0b',
  vlm: '#6366f1',
  default: '#6b7280',
};

export function PipelineNode({
  node,
  isSelected,
  isRunning,
  inputConnections,
  onSelect,
  onDelete,
  onDragStart,
  onConnectionStart,
  onInputHover,
}: PipelineNodeProps) {
  const categoryColor = categoryColors[node.tool.category] || categoryColors.default;

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

  const handleOutputMouseDown = useCallback(
    (outputName: string, e: ReactMouseEvent) => {
      e.stopPropagation();
      onConnectionStart(node.id, outputName, e);
    },
    [node.id, onConnectionStart]
  );

  const isInputConnected = (inputName: string): boolean => {
    return inputConnections.some((e) => e.targetInput === inputName);
  };

  return (
    <div
      className="absolute select-none"
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

        {/* Inputs */}
        {node.tool.inputs.length > 0 && (
          <div className="px-3 py-2 space-y-1">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">
              Inputs
            </span>
            {node.tool.inputs.map((input) => (
              <div
                key={input.name}
                className="flex items-center gap-2 group"
              >
                <div
                  className={`
                    w-3 h-3 rounded-full border-2 transition-all cursor-pointer
                    ${isInputConnected(input.name)
                      ? 'bg-green-500 border-green-400'
                      : 'bg-transparent border-gray-500 group-hover:border-gray-300'}
                  `}
                  onMouseEnter={() => onInputHover(node.id, input.name)}
                  onMouseLeave={() => onInputHover(null, null)}
                />
                <span className="text-xs text-gray-400">
                  {input.name}
                  {input.required && <span className="text-red-400 ml-0.5">*</span>}
                </span>
                <span className="text-[10px] text-gray-600 ml-auto">
                  {input.type}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Outputs */}
        {node.tool.outputs.length > 0 && (
          <div className="px-3 py-2 space-y-1 border-t border-white/5">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">
              Outputs
            </span>
            {node.tool.outputs.map((output) => (
              <div
                key={output.name}
                className="flex items-center gap-2 group justify-end"
              >
                <span className="text-[10px] text-gray-600">
                  {output.type}
                </span>
                <span className="text-xs text-gray-400">{output.name}</span>
                <div
                  className={`
                    w-3 h-3 rounded-full border-2 transition-all cursor-pointer
                    bg-transparent border-gray-500 group-hover:border-gray-300 group-hover:bg-gray-500
                  `}
                  onMouseDown={(e) => handleOutputMouseDown(output.name, e)}
                />
              </div>
            ))}
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

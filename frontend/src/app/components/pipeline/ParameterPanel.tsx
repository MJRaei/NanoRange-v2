'use client';

/**
 * ParameterPanel Component
 * Displays and allows editing of parameters for the selected node.
 * Connectable inputs (IMAGE/MASK) are shown as connection status.
 * Other inputs are editable via form fields.
 */

import React, { useCallback, useState } from 'react';
import type { PipelineNode, NodeInputValue, DataType, PipelineEdge, PipelineExecutionState } from './types';
import { isConnectableType, getInputSatisfactionStatus } from './utils/connectionUtils';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ParameterPanelProps {
  node: PipelineNode | null;
  inputConnections: PipelineEdge[];
  executionState: PipelineExecutionState;
  onUpdateInput: (nodeId: string, inputName: string, value: NodeInputValue) => void;
  onDeleteNode: (nodeId: string) => void;
}

function InputField({
  name,
  type,
  description,
  required,
  defaultValue,
  currentValue,
  isConnected,
  onChange,
}: {
  name: string;
  type: DataType;
  description: string;
  required: boolean;
  defaultValue?: unknown;
  currentValue?: NodeInputValue;
  isConnected: boolean;
  onChange: (value: NodeInputValue) => void;
}) {
  const value = currentValue?.value ?? defaultValue ?? '';

  const handleChange = useCallback(
    (newValue: unknown) => {
      onChange({ type: 'static', value: newValue });
    },
    [onChange]
  );

  if (isConnected) {
    return (
      <div className="px-3 py-2 rounded text-xs text-gray-400 bg-green-900/20 border border-green-500/30">
        Connected from {currentValue?.sourceNodeId}.{currentValue?.sourceOutput}
      </div>
    );
  }

  // Render different input types based on data type
  switch (type) {
    case 'BOOL':
      return (
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => handleChange(e.target.checked)}
            className="w-4 h-4 rounded border-gray-600 bg-black/30 text-orange-500 focus:ring-orange-500/50"
          />
          <span className="text-xs text-gray-400">{value ? 'True' : 'False'}</span>
        </label>
      );

    case 'INT':
      return (
        <input
          type="number"
          step={1}
          value={value as number}
          onChange={(e) => handleChange(parseInt(e.target.value, 10))}
          className="w-full px-3 py-1.5 rounded text-sm bg-black/30 border text-white focus:outline-none focus:border-orange-500/50"
          style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
        />
      );

    case 'FLOAT':
      return (
        <input
          type="number"
          step={0.1}
          value={value as number}
          onChange={(e) => handleChange(parseFloat(e.target.value))}
          className="w-full px-3 py-1.5 rounded text-sm bg-black/30 border text-white focus:outline-none focus:border-orange-500/50"
          style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
        />
      );

    case 'STRING':
    case 'PATH':
      return (
        <input
          type="text"
          value={value as string}
          onChange={(e) => handleChange(e.target.value)}
          placeholder={description}
          className="w-full px-3 py-1.5 rounded text-sm bg-black/30 border text-white placeholder-gray-500 focus:outline-none focus:border-orange-500/50"
          style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
        />
      );

    default:
      return (
        <div className="px-3 py-2 rounded text-xs text-gray-500 bg-black/20 border border-dashed" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
          {type} type - connect from another node
        </div>
      );
  }
}

/**
 * Helper to convert a file path to a static URL
 *
 * Backend mounts:
 *   /static/data → data/files directory
 *   /static/uploads → uploads directory
 *
 * So paths like:
 *   data/files/sessions/... → /static/data/sessions/...
 *   /absolute/path/data/files/sessions/... → /static/data/sessions/...
 *   uploads/... → /static/uploads/...
 */
function getStaticUrl(filePath: string): string {
  // If it's already a URL, return as-is
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
    return filePath;
  }

  // Handle paths containing data/files/ (both absolute and relative)
  // e.g., "data/files/sessions/..." or "/abs/path/data/files/sessions/..."
  const dataFilesMatch = filePath.match(/data\/files\/(.+)/);
  if (dataFilesMatch) {
    return `${API_BASE}/static/data/${dataFilesMatch[1]}`;
  }

  // Handle uploads paths (both absolute and relative)
  const uploadsMatch = filePath.match(/uploads\/(.+)/);
  if (uploadsMatch) {
    return `${API_BASE}/static/uploads/${uploadsMatch[1]}`;
  }

  // If it's an absolute path that doesn't match our patterns, log warning
  if (filePath.startsWith('/')) {
    console.warn('[getStaticUrl] Unhandled absolute path:', filePath);
    // Try to extract just the filename and serve from static/data
    const filename = filePath.split('/').pop();
    return `${API_BASE}/static/data/${filename}`;
  }

  // Handle relative paths starting with data/
  if (filePath.startsWith('data/')) {
    const relativePath = filePath.replace(/^data\//, '');
    return `${API_BASE}/static/data/${relativePath}`;
  }

  // Fallback: serve from static/data
  return `${API_BASE}/static/data/${filePath}`;
}

/**
 * Check if a value looks like an image path
 */
function isImagePath(value: unknown): value is string {
  if (typeof value !== 'string') return false;
  const lower = value.toLowerCase();
  return lower.endsWith('.png') || lower.endsWith('.jpg') || lower.endsWith('.jpeg') ||
         lower.endsWith('.tiff') || lower.endsWith('.tif') || lower.endsWith('.bmp');
}

export function ParameterPanel({ node, inputConnections, executionState, onUpdateInput, onDeleteNode }: ParameterPanelProps) {
  const [expandedImage, setExpandedImage] = useState<string | null>(null);

  const handleInputChange = useCallback(
    (inputName: string, value: NodeInputValue) => {
      if (node) {
        onUpdateInput(node.id, inputName, value);
      }
    },
    [node, onUpdateInput]
  );

  // Get execution result for this node
  const nodeResult = node ? executionState.nodeResults?.[node.id] : null;

  if (!node) {
    return (
      <div className="h-full flex items-center justify-center p-4" style={{ backgroundColor: '#111' }}>
        <div className="text-center">
          <div
            className="w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center"
            style={{ backgroundColor: 'rgba(255, 107, 53, 0.1)' }}
          >
            <svg
              className="w-6 h-6"
              style={{ color: '#ff6b35' }}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </div>
          <p className="text-gray-500 text-sm">Select a node to edit its parameters</p>
        </div>
      </div>
    );
  }

  // Separate connectable inputs from editable inputs
  const connectableInputs = node.tool.inputs.filter(input => isConnectableType(input.type));
  const editableInputs = node.tool.inputs.filter(input => !isConnectableType(input.type));

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#111' }}>
      {/* Header */}
      <div className="p-3 border-b" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">{node.tool.name}</h3>
          <button
            onClick={() => onDeleteNode(node.id)}
            className="p-1.5 rounded hover:bg-red-500/20 transition-colors"
          >
            <svg
              className="w-4 h-4 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">{node.tool.description}</p>
      </div>

      {/* Parameters */}
      <div className="flex-1 overflow-y-auto p-3">
        {/* Connectable inputs (IMAGE/MASK) - shown as connection status */}
        {connectableInputs.length > 0 && (
          <div className="mb-4">
            <h4 className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">
              Connections
            </h4>
            <div className="space-y-2">
              {connectableInputs.map((input) => {
                const currentValue = node.inputs[input.name];
                const isConnected = currentValue?.type === 'connection';
                const status = getInputSatisfactionStatus(
                  input,
                  currentValue,
                  inputConnections,
                  input.name
                );

                return (
                  <div key={input.name} className="space-y-1">
                    <label className="block text-xs font-medium text-gray-300">
                      {input.name}
                      {input.required && <span className="text-red-400 ml-0.5">*</span>}
                      <span className="text-[10px] text-gray-600 ml-2">{input.type}</span>
                    </label>
                    {isConnected ? (
                      <div className="px-3 py-2 rounded text-xs bg-green-900/20 border border-green-500/30">
                        <span className="text-green-400">Connected</span>
                        <span className="text-gray-500 ml-1">
                          from {currentValue?.sourceNodeId}.{currentValue?.sourceOutput}
                        </span>
                      </div>
                    ) : (
                      <div className={`px-3 py-2 rounded text-xs border border-dashed ${
                        status === 'unsatisfied'
                          ? 'bg-red-900/10 border-red-500/30 text-red-400'
                          : 'bg-black/20 border-gray-600 text-gray-500'
                      }`}>
                        Not connected - drag from another node&apos;s output port
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Editable inputs */}
        {editableInputs.length > 0 ? (
          <div className="space-y-4">
            {connectableInputs.length > 0 && (
              <h4 className="text-[10px] text-gray-500 uppercase tracking-wider">
                Parameters
              </h4>
            )}
            {editableInputs.map((input) => {
              const currentValue = node.inputs[input.name];
              const isConnected = currentValue?.type === 'connection';

              return (
                <div key={input.name}>
                  <label className="block text-xs font-medium text-gray-300 mb-1.5">
                    {input.name}
                    {input.required && <span className="text-red-400 ml-0.5">*</span>}
                    {input.default !== undefined && (
                      <span className="text-gray-600 ml-2 text-[10px]">
                        (default: {String(input.default)})
                      </span>
                    )}
                  </label>
                  <InputField
                    name={input.name}
                    type={input.type}
                    description={input.description}
                    required={input.required}
                    defaultValue={input.default}
                    currentValue={currentValue}
                    isConnected={isConnected}
                    onChange={(value) => handleInputChange(input.name, value)}
                  />
                  <p className="text-[10px] text-gray-600 mt-1">{input.description}</p>
                </div>
              );
            })}
          </div>
        ) : connectableInputs.length === 0 ? (
          <p className="text-xs text-gray-500 text-center py-4">
            This tool has no configurable parameters
          </p>
        ) : null}
      </div>

      {/* Outputs info */}
      {node.tool.outputs.length > 0 && (
        <div className="p-3 border-t" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
          <h4 className="text-xs font-medium text-gray-400 mb-2">Outputs</h4>
          <div className="space-y-2">
            {node.tool.outputs.map((output) => {
              const outputValue = nodeResult?.outputs?.[output.name];
              const hasImageOutput = isImagePath(outputValue);

              return (
                <div key={output.name} className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-300">{output.name}</span>
                    <span className="text-gray-600">{output.type}</span>
                  </div>

                  {/* Show output image if available */}
                  {hasImageOutput && (
                    <div className="relative group">
                      <img
                        src={getStaticUrl(outputValue)}
                        alt={`${output.name} output`}
                        className="w-full rounded border border-gray-700 cursor-pointer hover:border-orange-500/50 transition-colors"
                        onClick={() => setExpandedImage(getStaticUrl(outputValue))}
                      />
                      <div className="absolute bottom-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => setExpandedImage(getStaticUrl(outputValue))}
                          className="p-1 bg-black/70 rounded text-gray-300 hover:text-white"
                          title="Expand image"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Show completion status */}
                  {nodeResult && !hasImageOutput && (
                    <div className={`text-[10px] px-2 py-1 rounded ${
                      nodeResult.status === 'completed' ? 'bg-green-900/20 text-green-400' :
                      nodeResult.status === 'failed' ? 'bg-red-900/20 text-red-400' :
                      nodeResult.status === 'running' ? 'bg-yellow-900/20 text-yellow-400' :
                      'bg-gray-900/20 text-gray-500'
                    }`}>
                      {nodeResult.status === 'completed' && outputValue !== undefined
                        ? `Value: ${typeof outputValue === 'string' ? outputValue : JSON.stringify(outputValue)}`
                        : nodeResult.status}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Expanded image modal */}
      {expandedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={() => setExpandedImage(null)}
        >
          <div className="relative max-w-[90vw] max-h-[90vh]">
            <img
              src={expandedImage}
              alt="Expanded output"
              className="max-w-full max-h-[90vh] object-contain rounded"
            />
            <button
              onClick={() => setExpandedImage(null)}
              className="absolute top-2 right-2 p-2 bg-black/70 rounded-full text-white hover:bg-black/90 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

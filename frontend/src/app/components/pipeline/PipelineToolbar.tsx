'use client';

/**
 * PipelineToolbar Component
 * Provides actions for the pipeline (run, save, clear, etc.)
 */

import React, { useState } from 'react';
import type { PipelineExecutionState } from './types';

interface PipelineToolbarProps {
  pipelineName: string;
  nodeCount: number;
  executionState: PipelineExecutionState;
  adaptiveMode: boolean;
  onRun: () => void;
  onClear: () => void;
  onSave?: () => void;
  onNameChange: (name: string) => void;
  onAdaptiveModeChange: (enabled: boolean) => void;
}

export function PipelineToolbar({
  pipelineName,
  nodeCount,
  executionState,
  adaptiveMode,
  onRun,
  onClear,
  onSave,
  onNameChange,
  onAdaptiveModeChange,
}: PipelineToolbarProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(pipelineName);

  const handleNameSubmit = () => {
    onNameChange(editName);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNameSubmit();
    } else if (e.key === 'Escape') {
      setEditName(pipelineName);
      setIsEditing(false);
    }
  };

  const isRunning = executionState.status === 'running';

  return (
    <div
      className="flex items-center justify-between px-4 py-2 border-b"
      style={{
        backgroundColor: '#0d0d0d',
        borderColor: 'rgba(255, 255, 255, 0.1)',
      }}
    >
      {/* Left side - Pipeline name and info */}
      <div className="flex items-center gap-4">
        {/* Pipeline name */}
        {isEditing ? (
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onBlur={handleNameSubmit}
            onKeyDown={handleKeyDown}
            autoFocus
            className="px-2 py-1 rounded text-sm bg-black/30 border text-white focus:outline-none focus:border-orange-500/50"
            style={{ borderColor: 'rgba(255, 255, 255, 0.2)' }}
          />
        ) : (
          <button
            onClick={() => {
              setEditName(pipelineName);
              setIsEditing(true);
            }}
            className="text-sm font-medium text-white hover:text-orange-400 transition-colors flex items-center gap-1"
          >
            {pipelineName}
            <svg
              className="w-3 h-3 opacity-50"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
              />
            </svg>
          </button>
        )}

        {/* Node count */}
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: nodeCount > 0 ? '#10b981' : '#6b7280' }}
          />
          <span>
            {nodeCount} {nodeCount === 1 ? 'node' : 'nodes'}
          </span>
        </div>

        {/* Status indicator */}
        {executionState.status !== 'idle' && (
          <div
            className={`flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full ${
              executionState.status === 'running'
                ? 'bg-blue-500/20 text-blue-400'
                : executionState.status === 'success'
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400'
            }`}
          >
            {executionState.status === 'running' && (
              <svg
                className="w-3 h-3 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            )}
            <span className="capitalize">{executionState.status}</span>
          </div>
        )}
      </div>

      {/* Right side - Actions */}
      <div className="flex items-center gap-2">
        {/* Adaptive Mode Toggle */}
        <div className="flex items-center gap-2 mr-2">
          <label
            htmlFor="adaptive-mode"
            className="text-xs text-gray-400 cursor-pointer select-none"
            title="Adaptive mode uses AI to review outputs and automatically adjust parameters for better results"
          >
            Adaptive
          </label>
          <button
            id="adaptive-mode"
            onClick={() => onAdaptiveModeChange(!adaptiveMode)}
            disabled={isRunning}
            className={`relative w-9 h-5 rounded-full transition-colors duration-200 ${
              adaptiveMode
                ? 'bg-orange-500/80'
                : 'bg-gray-600'
            } ${isRunning ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
            title={adaptiveMode ? 'Adaptive mode enabled' : 'Enable adaptive mode'}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200 ${
                adaptiveMode ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Clear button */}
        <button
          onClick={onClear}
          disabled={isRunning || nodeCount === 0}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
          style={{ color: '#9ca3af' }}
        >
          <svg
            className="w-3.5 h-3.5"
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
          Clear
        </button>

        {/* Save button */}
        {onSave && (
          <button
            onClick={onSave}
            disabled={isRunning || nodeCount === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
            style={{ color: '#9ca3af' }}
          >
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
              />
            </svg>
            Save
          </button>
        )}

        {/* Run button */}
        <button
          onClick={onRun}
          disabled={isRunning || nodeCount === 0}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded text-xs font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            backgroundColor: isRunning ? 'rgba(255, 107, 53, 0.3)' : 'rgba(255, 107, 53, 0.8)',
            color: '#0a0908',
          }}
        >
          {isRunning ? (
            <>
              <svg
                className="w-3.5 h-3.5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Running...
            </>
          ) : (
            <>
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Run Pipeline
            </>
          )}
        </button>
      </div>
    </div>
  );
}

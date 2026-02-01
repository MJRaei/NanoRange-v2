'use client';

/**
 * PipelineEditor Component
 * Main container that composes all pipeline editing components.
 * Uses PipelineContext for shared state with Chat component.
 */

import React, { useState, useCallback } from 'react';
import { PipelineCanvas } from './PipelineCanvas';
import { ToolPalette } from './ToolPalette';
import { SavedPipelinesPanel } from './SavedPipelinesPanel';
import { ParameterPanel } from './ParameterPanel';
import { PipelineToolbar } from './PipelineToolbar';
import { Toast } from '../ui/Toast';
import { usePipelineContext } from './PipelineContext';
import { pipelineService } from '../../services/pipelineService';
import type { ToolDefinition, Position, Pipeline } from './types';

interface ToastState {
  message: string;
  type: 'success' | 'error' | 'info';
}

type LeftPanelTab = 'tools' | 'saved';

interface PipelineEditorProps {
  className?: string;
}

export function PipelineEditor({ className = '' }: PipelineEditorProps) {
  const {
    pipeline,
    selectedNodeId,
    selectedNode,
    executionState,
    adaptiveMode,
    addNode,
    removeNode,
    updateNodePosition,
    selectNode,
    updateNodeInput,
    addEdge,
    clearPipeline,
    setPipelineName,
    runPipeline,
    loadPipeline,
    setAdaptiveMode,
    getNodeInputConnections,
    getNodeOutputConnections,
  } = usePipelineContext();

  const [leftPanelWidth, setLeftPanelWidth] = useState(220);
  const [rightPanelWidth, setRightPanelWidth] = useState(280);
  const [isLeftCollapsed, setIsLeftCollapsed] = useState(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState(false);
  const [leftPanelTab, setLeftPanelTab] = useState<LeftPanelTab>('tools');
  const [toast, setToast] = useState<ToastState | null>(null);

  const handleDropTool = useCallback(
    (tool: ToolDefinition, position: Position) => {
      const nodeId = addNode(tool, position);
      selectNode(nodeId);
    },
    [addNode, selectNode]
  );

  const toggleLeftPanel = () => setIsLeftCollapsed(!isLeftCollapsed);
  const toggleRightPanel = () => setIsRightCollapsed(!isRightCollapsed);

  const handleSave = useCallback(async () => {
    try {
      await pipelineService.savePipeline(pipeline, pipeline.name);
      setToast({ message: 'Pipeline saved successfully', type: 'success' });
    } catch (error) {
      console.error('Failed to save pipeline:', error);
      setToast({ message: 'Failed to save pipeline', type: 'error' });
    }
  }, [pipeline]);

  const handleLoadPipeline = useCallback((loadedPipeline: Pipeline) => {
    loadPipeline(loadedPipeline);
    // Switch to tools tab after loading
    setLeftPanelTab('tools');
  }, [loadPipeline]);

  return (
    <div className={`flex flex-col h-full ${className}`} style={{ backgroundColor: '#0a0908' }}>
      {/* Toast notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Toolbar */}
      <PipelineToolbar
        pipelineName={pipeline.name}
        nodeCount={pipeline.nodes.length}
        executionState={executionState}
        adaptiveMode={adaptiveMode}
        onRun={runPipeline}
        onClear={clearPipeline}
        onSave={handleSave}
        onNameChange={setPipelineName}
        onAdaptiveModeChange={setAdaptiveMode}
      />

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel - Tool Palette / Saved Pipelines */}
        <div
          className="flex-shrink-0 border-r transition-all duration-200"
          style={{
            width: isLeftCollapsed ? 40 : leftPanelWidth,
            borderColor: 'rgba(255, 255, 255, 0.1)',
          }}
        >
          {isLeftCollapsed ? (
            <button
              onClick={toggleLeftPanel}
              className="w-full h-full flex items-center justify-center hover:bg-white/5 transition-colors"
            >
              <svg
                className="w-4 h-4 text-gray-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 5l7 7-7 7M5 5l7 7-7 7"
                />
              </svg>
            </button>
          ) : (
            <div className="h-full flex flex-col">
              {/* Tab header with collapse button */}
              <div
                className="flex-shrink-0 flex items-center border-b"
                style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
              >
                {/* Tabs */}
                <div className="flex-1 flex">
                  <button
                    onClick={() => setLeftPanelTab('tools')}
                    className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                      leftPanelTab === 'tools'
                        ? 'text-orange-400 border-b-2 border-orange-400'
                        : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    Tools
                  </button>
                  <button
                    onClick={() => setLeftPanelTab('saved')}
                    className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                      leftPanelTab === 'saved'
                        ? 'text-orange-400 border-b-2 border-orange-400'
                        : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    Saved
                  </button>
                </div>
                {/* Collapse button */}
                <button
                  onClick={toggleLeftPanel}
                  className="p-2 flex items-center justify-center hover:bg-white/5 transition-colors"
                >
                  <svg
                    className="w-4 h-4 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                    />
                  </svg>
                </button>
              </div>
              {/* Tab content */}
              <div className="flex-1 overflow-hidden">
                {leftPanelTab === 'tools' ? (
                  <ToolPalette />
                ) : (
                  <SavedPipelinesPanel onLoadPipeline={handleLoadPipeline} />
                )}
              </div>
            </div>
          )}
        </div>

        {/* Center - Canvas */}
        <div className="flex-1 relative overflow-hidden">
          <PipelineCanvas
            pipeline={pipeline}
            selectedNodeId={selectedNodeId}
            executionState={executionState}
            onSelectNode={selectNode}
            onDeleteNode={removeNode}
            onUpdateNodePosition={updateNodePosition}
            onAddEdge={addEdge}
            onDropTool={handleDropTool}
            getNodeInputConnections={getNodeInputConnections}
            getNodeOutputConnections={getNodeOutputConnections}
          />
        </div>

        {/* Right panel - Parameter Panel */}
        <div
          className="flex-shrink-0 border-l transition-all duration-200"
          style={{
            width: isRightCollapsed ? 40 : rightPanelWidth,
            borderColor: 'rgba(255, 255, 255, 0.1)',
          }}
        >
          {isRightCollapsed ? (
            <button
              onClick={toggleRightPanel}
              className="w-full h-full flex items-center justify-center hover:bg-white/5 transition-colors"
            >
              <svg
                className="w-4 h-4 text-gray-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                />
              </svg>
            </button>
          ) : (
            <div className="h-full flex flex-col">
              <button
                onClick={toggleRightPanel}
                className="flex-shrink-0 w-full p-2 flex items-center hover:bg-white/5 transition-colors border-b"
                style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
              >
                <svg
                  className="w-4 h-4 text-gray-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 5l7 7-7 7M5 5l7 7-7 7"
                  />
                </svg>
              </button>
              <div className="flex-1 overflow-hidden">
                <ParameterPanel
                  node={selectedNode}
                  inputConnections={selectedNodeId ? getNodeInputConnections(selectedNodeId) : []}
                  executionState={executionState}
                  onUpdateInput={updateNodeInput}
                  onDeleteNode={removeNode}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

/**
 * PipelineEditor Component
 * Main container that composes all pipeline editing components
 */

import React, { useState, useCallback } from 'react';
import { PipelineCanvas } from './PipelineCanvas';
import { ToolPalette } from './ToolPalette';
import { ParameterPanel } from './ParameterPanel';
import { PipelineToolbar } from './PipelineToolbar';
import { usePipeline } from './hooks/usePipeline';
import { pipelineService } from '../../services/pipelineService';
import type { ToolDefinition, Position } from './types';

interface PipelineEditorProps {
  className?: string;
}

export function PipelineEditor({ className = '' }: PipelineEditorProps) {
  const {
    pipeline,
    selectedNodeId,
    selectedNode,
    executionState,
    addNode,
    removeNode,
    updateNodePosition,
    selectNode,
    updateNodeInput,
    addEdge,
    clearPipeline,
    setPipelineName,
    runPipeline,
    getNodeInputConnections,
    getNodeOutputConnections,
  } = usePipeline();

  const [leftPanelWidth, setLeftPanelWidth] = useState(200);
  const [rightPanelWidth, setRightPanelWidth] = useState(280);
  const [isLeftCollapsed, setIsLeftCollapsed] = useState(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState(false);

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
      const pipelineId = await pipelineService.savePipeline(
        pipeline,
        pipeline.name
      );
      console.log('Pipeline saved successfully:', pipelineId);
      // TODO: Show success toast/notification
    } catch (error) {
      console.error('Failed to save pipeline:', error);
      // TODO: Show error toast/notification
    }
  }, [pipeline]);

  return (
    <div className={`flex flex-col h-full ${className}`} style={{ backgroundColor: '#0a0908' }}>
      {/* Toolbar */}
      <PipelineToolbar
        pipelineName={pipeline.name}
        nodeCount={pipeline.nodes.length}
        executionState={executionState}
        onRun={runPipeline}
        onClear={clearPipeline}
        onSave={handleSave}
        onNameChange={setPipelineName}
      />

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel - Tool Palette */}
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
              <button
                onClick={toggleLeftPanel}
                className="flex-shrink-0 w-full p-2 flex items-center justify-end hover:bg-white/5 transition-colors border-b"
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
                    d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                  />
                </svg>
              </button>
              <div className="flex-1 overflow-hidden">
                <ToolPalette />
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

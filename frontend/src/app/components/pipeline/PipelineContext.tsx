'use client';

/**
 * Pipeline Context
 * Provides shared pipeline state between Chat and PipelineEditor components.
 * This enables the agent-built pipeline to be displayed in the visual editor.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { usePipeline } from './hooks/usePipeline';
import type {
  Pipeline,
  PipelineNode,
  PipelineEdge,
  ToolDefinition,
  Position,
  NodeInputValue,
  PipelineExecutionState,
  RefinementInfo,
} from './types';

interface PipelineContextValue {
  pipeline: Pipeline;
  selectedNodeId: string | null;
  selectedNode: PipelineNode | null;
  executionState: PipelineExecutionState;
  adaptiveMode: boolean;

  // Node operations
  addNode: (tool: ToolDefinition, position: Position) => string;
  removeNode: (nodeId: string) => void;
  updateNodePosition: (nodeId: string, position: Position) => void;
  selectNode: (nodeId: string | null) => void;
  updateNodeInput: (nodeId: string, inputName: string, value: NodeInputValue) => void;

  // Edge operations
  addEdge: (sourceNodeId: string, targetNodeId: string) => string | null;
  removeEdge: (edgeId: string) => void;
  removeEdgesForNode: (nodeId: string) => void;

  // Pipeline operations
  clearPipeline: () => void;
  setPipelineName: (name: string) => void;
  runPipeline: () => Promise<void>;
  loadPipeline: (pipelineData: Pipeline) => void;
  setAdaptiveMode: (enabled: boolean) => void;
  setExecutionResults: (executionResult: {
    status: string;
    adaptive_mode?: boolean;
    step_results?: Array<{
      step_id?: string;
      node_id?: string;
      step_name: string;
      status: string;
      outputs?: Record<string, unknown>;
      error?: string;
      iterations?: Array<{
        iteration: number;
        inputs: Record<string, unknown>;
        outputs: Record<string, unknown>;
        duration_seconds?: number;
        decision?: {
          quality: string;
          action: string;
          assessment?: string;
          reasoning?: string;
        };
        artifacts?: Record<string, string>;
      }>;
      final_iteration?: number;
    }>;
  }) => void;

  // Validation
  canConnect: (sourceNodeId: string, targetNodeId: string) => boolean;
  getNodeInputConnections: (nodeId: string) => PipelineEdge[];
  getNodeOutputConnections: (nodeId: string) => PipelineEdge[];
}

const PipelineContext = createContext<PipelineContextValue | null>(null);

interface PipelineProviderProps {
  children: ReactNode;
}

export function PipelineProvider({ children }: PipelineProviderProps) {
  const pipelineState = usePipeline();

  return (
    <PipelineContext.Provider value={pipelineState}>
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipelineContext(): PipelineContextValue {
  const context = useContext(PipelineContext);
  if (!context) {
    throw new Error('usePipelineContext must be used within a PipelineProvider');
  }
  return context;
}

export { PipelineContext };

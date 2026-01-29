/**
 * Pipeline State Management Hook
 * Manages pipeline nodes, edges, selection, and operations.
 * Uses simplified connection model with auto-detected primary ports.
 */

import { useState, useCallback, useMemo } from 'react';
import type {
  Pipeline,
  PipelineNode,
  PipelineEdge,
  ToolDefinition,
  Position,
  NodeInputValue,
  PipelineExecutionState,
  NodeExecutionResult,
  IterationResult,
  RefinementInfo,
} from '../types';
import { pipelineService } from '../../../services/pipelineService';
import { getPortConfig, areTypesCompatible } from '../utils/connectionUtils';

function generateId(): string {
  return 'node_' + Math.random().toString(36).substr(2, 9);
}

function generateEdgeId(): string {
  return 'edge_' + Math.random().toString(36).substr(2, 9);
}

interface UsePipelineReturn {
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

  // Edge operations (simplified - just source and target node IDs)
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
    step_results?: Array<{
      step_id?: string;
      node_id?: string;
      step_name: string;
      status: string;
      outputs?: Record<string, unknown>;
      error?: string;
    }>;
  }) => void;

  // Validation
  canConnect: (sourceNodeId: string, targetNodeId: string) => boolean;
  getNodeInputConnections: (nodeId: string) => PipelineEdge[];
  getNodeOutputConnections: (nodeId: string) => PipelineEdge[];
}

const initialPipeline: Pipeline = {
  id: 'pipeline_1',
  name: 'New Pipeline',
  nodes: [],
  edges: [],
};

export function usePipeline(): UsePipelineReturn {
  const [pipeline, setPipeline] = useState<Pipeline>(initialPipeline);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [adaptiveMode, setAdaptiveMode] = useState<boolean>(false);
  const [executionState, setExecutionState] = useState<PipelineExecutionState>({
    status: 'idle',
  });

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return pipeline.nodes.find((n) => n.id === selectedNodeId) || null;
  }, [pipeline.nodes, selectedNodeId]);

  const addNode = useCallback((tool: ToolDefinition, position: Position): string => {
    const nodeId = generateId();
    const newNode: PipelineNode = {
      id: nodeId,
      toolId: tool.id,
      tool,
      position,
      inputs: {},
    };

    // Initialize inputs with defaults
    tool.inputs.forEach((input) => {
      if (input.default !== undefined) {
        newNode.inputs[input.name] = {
          type: 'static',
          value: input.default,
        };
      }
    });

    setPipeline((prev) => ({
      ...prev,
      nodes: [...prev.nodes, newNode],
    }));

    return nodeId;
  }, []);

  const removeNode = useCallback((nodeId: string) => {
    setPipeline((prev) => ({
      ...prev,
      nodes: prev.nodes.filter((n) => n.id !== nodeId),
      edges: prev.edges.filter(
        (e) => e.sourceNodeId !== nodeId && e.targetNodeId !== nodeId
      ),
    }));
    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null);
    }
  }, [selectedNodeId]);

  const updateNodePosition = useCallback((nodeId: string, position: Position) => {
    setPipeline((prev) => ({
      ...prev,
      nodes: prev.nodes.map((n) =>
        n.id === nodeId ? { ...n, position } : n
      ),
    }));
  }, []);

  const selectNode = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId);
  }, []);

  const updateNodeInput = useCallback(
    (nodeId: string, inputName: string, value: NodeInputValue) => {
      setPipeline((prev) => ({
        ...prev,
        nodes: prev.nodes.map((n) =>
          n.id === nodeId
            ? { ...n, inputs: { ...n.inputs, [inputName]: value } }
            : n
        ),
      }));
    },
    []
  );

  // Simplified canConnect - just checks if source can connect to target
  const canConnect = useCallback(
    (sourceNodeId: string, targetNodeId: string): boolean => {
      // Can't connect to self
      if (sourceNodeId === targetNodeId) return false;

      // Get source and target nodes
      const sourceNode = pipeline.nodes.find((n) => n.id === sourceNodeId);
      const targetNode = pipeline.nodes.find((n) => n.id === targetNodeId);
      if (!sourceNode || !targetNode) return false;

      // Get port configs
      const sourceConfig = getPortConfig(sourceNode.tool);
      const targetConfig = getPortConfig(targetNode.tool);

      // Source must have output port, target must have input port
      if (!sourceConfig.hasOutputPort || !targetConfig.hasInputPort) return false;
      if (!sourceConfig.primaryOutput || !targetConfig.primaryInput) return false;

      // Check if target's primary input already has a connection
      const existingEdge = pipeline.edges.find(
        (e) =>
          e.targetNodeId === targetNodeId &&
          e.targetInput === targetConfig.primaryInput?.name
      );
      if (existingEdge) return false;

      // Check type compatibility
      return areTypesCompatible(
        sourceConfig.primaryOutput.type,
        targetConfig.primaryInput.type
      );
    },
    [pipeline.edges, pipeline.nodes]
  );

  // Simplified addEdge - auto-detects primary input/output
  const addEdge = useCallback(
    (sourceNodeId: string, targetNodeId: string): string | null => {
      // Get source and target nodes
      const sourceNode = pipeline.nodes.find((n) => n.id === sourceNodeId);
      const targetNode = pipeline.nodes.find((n) => n.id === targetNodeId);
      if (!sourceNode || !targetNode) return null;

      // Get port configs to determine primary input/output
      const sourceConfig = getPortConfig(sourceNode.tool);
      const targetConfig = getPortConfig(targetNode.tool);

      if (!sourceConfig.primaryOutput || !targetConfig.primaryInput) return null;

      // Validate connection
      if (!canConnect(sourceNodeId, targetNodeId)) {
        return null;
      }

      const edgeId = generateEdgeId();
      const newEdge: PipelineEdge = {
        id: edgeId,
        sourceNodeId,
        sourceOutput: sourceConfig.primaryOutput.name,
        targetNodeId,
        targetInput: targetConfig.primaryInput.name,
      };

      setPipeline((prev) => ({
        ...prev,
        edges: [...prev.edges, newEdge],
      }));

      // Update target node input to use connection
      updateNodeInput(targetNodeId, targetConfig.primaryInput.name, {
        type: 'connection',
        sourceNodeId,
        sourceOutput: sourceConfig.primaryOutput.name,
      });

      return edgeId;
    },
    [canConnect, updateNodeInput, pipeline.nodes]
  );

  const removeEdge = useCallback((edgeId: string) => {
    const edge = pipeline.edges.find((e) => e.id === edgeId);
    if (edge) {
      // Reset the input to static
      updateNodeInput(edge.targetNodeId, edge.targetInput, {
        type: 'static',
        value: undefined,
      });
    }
    setPipeline((prev) => ({
      ...prev,
      edges: prev.edges.filter((e) => e.id !== edgeId),
    }));
  }, [pipeline.edges, updateNodeInput]);

  const removeEdgesForNode = useCallback((nodeId: string) => {
    setPipeline((prev) => ({
      ...prev,
      edges: prev.edges.filter(
        (e) => e.sourceNodeId !== nodeId && e.targetNodeId !== nodeId
      ),
    }));
  }, []);

  const getNodeInputConnections = useCallback(
    (nodeId: string): PipelineEdge[] => {
      return pipeline.edges.filter((e) => e.targetNodeId === nodeId);
    },
    [pipeline.edges]
  );

  const getNodeOutputConnections = useCallback(
    (nodeId: string): PipelineEdge[] => {
      return pipeline.edges.filter((e) => e.sourceNodeId === nodeId);
    },
    [pipeline.edges]
  );

  const clearPipeline = useCallback(() => {
    setPipeline(initialPipeline);
    setSelectedNodeId(null);
    setExecutionState({ status: 'idle' });
  }, []);

  const setPipelineName = useCallback((name: string) => {
    setPipeline((prev) => ({ ...prev, name }));
  }, []);

  const loadPipeline = useCallback((pipelineData: Pipeline) => {
    setPipeline(pipelineData);
    setSelectedNodeId(null);
    setExecutionState({ status: 'idle' });
  }, []);

  // Set execution results from external source (e.g., agent execution)
  const setExecutionResults = useCallback((executionResult: {
    status: string;
    step_results?: Array<{
      step_id?: string;
      node_id?: string;
      step_name: string;
      status: string;
      outputs?: Record<string, unknown>;
      error?: string;
    }>;
  }) => {
    const frontendStatus =
      executionResult.status === 'completed' ? 'success' :
      executionResult.status === 'failed' ? 'error' :
      'idle';

    // Build nodeResults map from step_results
    const nodeResults: Record<string, NodeExecutionResult> = {};
    if (executionResult.step_results) {
      for (const stepResult of executionResult.step_results) {
        // Use node_id if available (from agent), otherwise fall back to step_id
        const nodeId = stepResult.node_id || stepResult.step_id || '';
        if (nodeId) {
          nodeResults[nodeId] = {
            stepId: stepResult.step_id || nodeId,
            stepName: stepResult.step_name,
            status: stepResult.status as 'pending' | 'running' | 'completed' | 'failed',
            outputs: stepResult.outputs || {},
            errorMessage: stepResult.error,
          };
        }
      }
    }

    setExecutionState({
      status: frontendStatus as 'idle' | 'running' | 'success' | 'error',
      nodeResults,
    });
  }, []);

  const runPipeline = useCallback(async () => {
    setExecutionState({ status: 'running', adaptiveMode });

    try {
      // Start pipeline execution on backend with adaptive mode flag
      const { execution_id } = await pipelineService.executePipeline(
        pipeline,
        undefined,
        adaptiveMode
      );

      // Poll for status updates
      const pollStatus = async () => {
        try {
          const status = await pipelineService.getExecutionStatus(execution_id);

          // Map backend status to frontend status
          const frontendStatus =
            status.status === 'completed' ? 'success' :
            status.status === 'failed' ? 'error' :
            'running';

          // Build nodeResults map from step_results
          const nodeResults: Record<string, NodeExecutionResult> = {};
          if (status.result?.step_results) {
            for (const stepResult of status.result.step_results) {
              nodeResults[stepResult.step_id] = {
                stepId: stepResult.step_id,
                stepName: stepResult.step_name,
                status: stepResult.status as 'pending' | 'running' | 'completed' | 'failed',
                outputs: stepResult.outputs || {},
                errorMessage: stepResult.error_message,
                iterations: stepResult.iterations?.map(iter => ({
                  iteration: iter.iteration,
                  inputs: iter.inputs,
                  outputs: iter.outputs,
                  durationSeconds: iter.duration_seconds,
                  decision: iter.decision,
                  artifacts: iter.artifacts,
                })),
                finalIteration: stepResult.final_iteration,
              };
            }
          }

          // Map refinement info if available
          let refinementInfo: RefinementInfo | undefined;
          if (status.refinement_info) {
            refinementInfo = {
              totalIterations: status.refinement_info.total_iterations,
              stepsRefined: status.refinement_info.steps_refined,
              toolsRemoved: status.refinement_info.tools_removed,
              stepDetails: {},
            };
            for (const [stepId, details] of Object.entries(status.refinement_info.step_details)) {
              refinementInfo.stepDetails[stepId] = {
                stepName: details.step_name,
                toolId: details.tool_id,
                totalIterations: details.total_iterations,
                finalIteration: details.final_iteration,
                wasRemoved: details.was_removed,
                removalReason: details.removal_reason,
                iterations: details.iterations.map(iter => ({
                  iteration: iter.iteration,
                  inputs: iter.inputs,
                  outputs: iter.outputs,
                  durationSeconds: iter.duration_seconds,
                  decision: iter.decision,
                  artifacts: iter.artifacts,
                })),
              };
            }
          }

          setExecutionState({
            status: frontendStatus as 'idle' | 'running' | 'success' | 'error',
            currentNodeId: status.current_step,
            results: status.result?.final_outputs,
            nodeResults,
            error: status.error,
            adaptiveMode: status.adaptive_mode,
            refinementInfo,
          });

          // Continue polling if still running
          if (status.status === 'running') {
            setTimeout(pollStatus, 1000); // Poll every 1 second
          }
        } catch (error) {
          setExecutionState({
            status: 'error',
            error: error instanceof Error ? error.message : 'Status check failed',
          });
        }
      };

      // Start polling
      pollStatus();
    } catch (error) {
      setExecutionState({
        status: 'error',
        error: error instanceof Error ? error.message : 'Execution failed',
      });
    }
  }, [pipeline, adaptiveMode]);

  return {
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
    removeEdge,
    removeEdgesForNode,
    clearPipeline,
    setPipelineName,
    runPipeline,
    loadPipeline,
    setAdaptiveMode,
    setExecutionResults,
    canConnect,
    getNodeInputConnections,
    getNodeOutputConnections,
  };
}

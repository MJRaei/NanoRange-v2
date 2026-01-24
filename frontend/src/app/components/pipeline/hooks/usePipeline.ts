/**
 * Pipeline State Management Hook
 * Manages pipeline nodes, edges, selection, and operations
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
} from '../types';
import { pipelineService } from '../../../services/pipelineService';

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

  // Node operations
  addNode: (tool: ToolDefinition, position: Position) => string;
  removeNode: (nodeId: string) => void;
  updateNodePosition: (nodeId: string, position: Position) => void;
  selectNode: (nodeId: string | null) => void;
  updateNodeInput: (nodeId: string, inputName: string, value: NodeInputValue) => void;

  // Edge operations
  addEdge: (edge: Omit<PipelineEdge, 'id'>) => string | null;
  removeEdge: (edgeId: string) => void;
  removeEdgesForNode: (nodeId: string) => void;

  // Pipeline operations
  clearPipeline: () => void;
  setPipelineName: (name: string) => void;
  runPipeline: () => Promise<void>;

  // Validation
  canConnect: (sourceNodeId: string, sourceOutput: string, targetNodeId: string, targetInput: string) => boolean;
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

  const canConnect = useCallback(
    (
      sourceNodeId: string,
      sourceOutput: string,
      targetNodeId: string,
      targetInput: string
    ): boolean => {
      // Can't connect to self
      if (sourceNodeId === targetNodeId) return false;

      // Check if connection already exists
      const existingEdge = pipeline.edges.find(
        (e) =>
          e.targetNodeId === targetNodeId && e.targetInput === targetInput
      );
      if (existingEdge) return false;

      // Get source and target nodes
      const sourceNode = pipeline.nodes.find((n) => n.id === sourceNodeId);
      const targetNode = pipeline.nodes.find((n) => n.id === targetNodeId);
      if (!sourceNode || !targetNode) return false;

      // Check that the output and input ports exist
      const output = sourceNode.tool.outputs.find((o) => o.name === sourceOutput);
      const input = targetNode.tool.inputs.find((i) => i.name === targetInput);
      if (!output || !input) return false;

      // Define compatible type groups - types within a group can connect to each other
      const imageTypes = ['IMAGE', 'MASK', 'ARRAY'];
      const numericTypes = ['FLOAT', 'INT'];
      const anyTypes = ['PARAMETERS', 'INSTRUCTIONS']; // These accept anything

      // Check type compatibility
      const outputType = output.type;
      const inputType = input.type;

      // Exact match
      if (outputType === inputType) return true;

      // Input accepts any type
      if (anyTypes.includes(inputType)) return true;

      // Image-like types are compatible with each other
      if (imageTypes.includes(outputType) && imageTypes.includes(inputType)) return true;

      // Numeric types are compatible with each other
      if (numericTypes.includes(outputType) && numericTypes.includes(inputType)) return true;

      // For UI flexibility, allow connections - backend will validate
      // This makes the visual editor more user-friendly
      return true;
    },
    [pipeline.edges, pipeline.nodes]
  );

  const addEdge = useCallback(
    (edge: Omit<PipelineEdge, 'id'>): string | null => {
      if (
        !canConnect(
          edge.sourceNodeId,
          edge.sourceOutput,
          edge.targetNodeId,
          edge.targetInput
        )
      ) {
        return null;
      }

      const edgeId = generateEdgeId();
      const newEdge: PipelineEdge = { ...edge, id: edgeId };

      setPipeline((prev) => ({
        ...prev,
        edges: [...prev.edges, newEdge],
      }));

      // Update target node input to use connection
      updateNodeInput(edge.targetNodeId, edge.targetInput, {
        type: 'connection',
        sourceNodeId: edge.sourceNodeId,
        sourceOutput: edge.sourceOutput,
      });

      return edgeId;
    },
    [canConnect, updateNodeInput]
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

  const runPipeline = useCallback(async () => {
    setExecutionState({ status: 'running' });

    try {
      // Start pipeline execution on backend
      const { execution_id } = await pipelineService.executePipeline(pipeline);

      // Poll for status updates
      const pollStatus = async () => {
        try {
          const status = await pipelineService.getExecutionStatus(execution_id);

          // Map backend status to frontend status
          const frontendStatus =
            status.status === 'completed' ? 'success' :
            status.status === 'failed' ? 'error' :
            'running';

          setExecutionState({
            status: frontendStatus as 'idle' | 'running' | 'success' | 'error',
            currentNodeId: status.current_step,
            results: status.result?.final_outputs,
            error: status.error,
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
  }, [pipeline]);

  return {
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
    removeEdge,
    removeEdgesForNode,
    clearPipeline,
    setPipelineName,
    runPipeline,
    canConnect,
    getNodeInputConnections,
    getNodeOutputConnections,
  };
}

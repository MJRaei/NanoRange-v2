/**
 * Pipeline Editor Types
 * Defines the data structures for visual pipeline editing
 */

export type DataType =
  | 'IMAGE'
  | 'MASK'
  | 'FLOAT'
  | 'INT'
  | 'STRING'
  | 'BOOL'
  | 'LIST'
  | 'DICT'
  | 'PATH'
  | 'ARRAY'
  | 'MEASUREMENTS'
  | 'PARAMETERS'
  | 'INSTRUCTIONS';

export interface ToolInput {
  name: string;
  type: DataType;
  description: string;
  required: boolean;
  default?: unknown;
  constraints?: Record<string, unknown>;
}

export interface ToolOutput {
  name: string;
  type: DataType;
  description: string;
}

export interface ToolDefinition {
  id: string;
  name: string;
  description: string;
  category: string;
  inputs: ToolInput[];
  outputs: ToolOutput[];
}

export interface Position {
  x: number;
  y: number;
}

export interface PipelineNode {
  id: string;
  toolId: string;
  tool: ToolDefinition;
  position: Position;
  inputs: Record<string, NodeInputValue>;
  isSelected?: boolean;
}

export type NodeInputValue = {
  type: 'static' | 'connection' | 'user_input';
  value?: unknown;
  sourceNodeId?: string;
  sourceOutput?: string;
};

export interface PipelineEdge {
  id: string;
  sourceNodeId: string;
  sourceOutput: string;
  targetNodeId: string;
  targetInput: string;
}

export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  nodes: PipelineNode[];
  edges: PipelineEdge[];
}

export interface DragState {
  isDragging: boolean;
  dragType: 'node' | 'tool' | 'edge' | null;
  dragData?: {
    nodeId?: string;
    tool?: ToolDefinition;
    sourceNodeId?: string;
    sourceOutput?: string;
  };
  offset?: Position;
}

export interface CanvasState {
  zoom: number;
  pan: Position;
}

export type PipelineStatus = 'idle' | 'running' | 'success' | 'error';

export interface NodeExecutionResult {
  stepId: string;
  stepName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  outputs: Record<string, unknown>;
  errorMessage?: string;
}

export interface PipelineExecutionState {
  status: PipelineStatus;
  currentNodeId?: string;
  results?: Record<string, unknown>;
  nodeResults?: Record<string, NodeExecutionResult>;
  error?: string;
}

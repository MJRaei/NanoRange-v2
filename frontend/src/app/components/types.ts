/**
 * Shared TypeScript types for the NanOrange frontend
 */

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  images?: MessageImage[];
  csvPath?: string;
  attachedImage?: string;
}

export interface MessageImage {
  key: string;
  url: string;
  title: string;
}

export interface AnalysisImages {
  thresholded_with_shapes?: string;
  size_distribution?: string;
  original?: string;
  colorized?: string;
  thresholded?: string;
  original_with_shapes?: string;
  colorized_with_shapes?: string;
  original_with_shapes_html?: string;
  colorized_with_shapes_html?: string;
  thresholded_with_shapes_html?: string;
  size_distribution_html?: string;
}

export interface AnalysisResult {
  success: boolean;
  message: string;
  images: AnalysisImages;
  csv_path: string | null;
  session_id: string;
  pipeline?: AgentPipeline | null;  // Pipeline built by the agent
}

// Pipeline structure from agent (matches backend format)
export interface AgentPipeline {
  id: string;
  name: string;
  description?: string;
  nodes: AgentPipelineNode[];
  edges: AgentPipelineEdge[];
}

export interface AgentPipelineNode {
  id: string;
  toolId: string;
  tool: AgentToolDefinition;
  position: { x: number; y: number };
  inputs: Record<string, AgentNodeInputValue>;
}

export interface AgentToolDefinition {
  id: string;
  name: string;
  description: string;
  category: string;
  inputs: AgentToolInput[];
  outputs: AgentToolOutput[];
}

export interface AgentToolInput {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: unknown;
  constraints?: Record<string, unknown>;
}

export interface AgentToolOutput {
  name: string;
  type: string;
  description: string;
}

export interface AgentNodeInputValue {
  type: 'static' | 'connection' | 'user_input';
  value?: unknown;
  sourceNodeId?: string;
  sourceOutput?: string;
}

export interface AgentPipelineEdge {
  id: string;
  sourceNodeId: string;
  sourceOutput: string;
  targetNodeId: string;
  targetInput: string;
}

export interface FileInfo {
  name: string;
  path: string;
  type: string;
  interactive_html?: string | null;  // Path to interactive HTML version if available
}

export interface SidebarFiles {
  images: FileInfo[];
  plots: FileInfo[];
  csv_files: FileInfo[];
}


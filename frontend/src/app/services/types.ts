/**
 * API-specific types for pipeline service
 *
 * These types define the contract between frontend and backend API,
 * and may differ from component-level types.
 */

import type { ToolDefinition, Pipeline } from '../components/pipeline/types';

// API Response types
export interface ToolListResponse {
  tools: ToolDefinition[];
  categories: string[];
}

export interface PipelineExecuteResponse {
  execution_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  message?: string;
}

export interface ExecutionStatusResponse {
  execution_id: string;
  status: 'running' | 'completed' | 'failed';
  progress: number; // 0-1
  current_step?: string;
  result?: PipelineResultData;
  error?: string;
  adaptive_mode?: boolean;
  refinement_info?: RefinementInfo;
}

export interface RefinementInfo {
  total_iterations: number;
  steps_refined: number;
  tools_removed: number;
  step_details: Record<string, StepRefinementDetails>;
}

export interface StepRefinementDetails {
  step_name: string;
  tool_id: string;
  total_iterations: number;
  final_iteration: number | null;
  was_removed: boolean;
  removal_reason?: string;
  iterations: IterationData[];
}

export interface IterationData {
  iteration: number;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  duration_seconds?: number;
  decision?: {
    quality: string;
    action: string;
    assessment?: string;
    reasoning?: string;
  };
  artifacts?: Record<string, string>;
}

export interface PipelineResultData {
  step_results: StepResultData[];
  final_outputs: Record<string, any>;
  total_duration_seconds?: number;
}

export interface StepResultData {
  step_id: string;
  step_name: string;
  status: string;
  outputs: Record<string, any>;
  error_message?: string;
  iterations?: IterationData[];
  final_iteration?: number;
}

export interface PipelineSaveResponse {
  pipeline_id: string;
  saved_at: string;
}

export interface PipelineSummary {
  pipeline_id: string;
  name: string;
  description?: string;
  created_at: string;
  modified_at: string;
  step_count: number;
}

export interface SavedPipelinesResponse {
  pipelines: PipelineSummary[];
}

// Error types
export class PipelineApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = 'PipelineApiError';
  }
}

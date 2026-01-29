/**
 * Pipeline Service Layer
 *
 * Provides a clean abstraction over all pipeline-related API calls.
 * Components should use this service instead of calling fetch directly.
 */

import type { ToolDefinition, Pipeline } from '../components/pipeline/types';
import type {
  ToolListResponse,
  PipelineExecuteResponse,
  ExecutionStatusResponse,
  PipelineSaveResponse,
  PipelineSummary,
  SavedPipelinesResponse,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class for pipeline API errors
 */
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

/**
 * Generic API request wrapper with error handling
 */
async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new PipelineApiError(
        error.detail || `API request failed with status ${response.status}`,
        response.status,
        error
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof PipelineApiError) {
      throw error;
    }
    throw new PipelineApiError(
      'Network error: Unable to connect to backend',
      0,
      error
    );
  }
}

/**
 * Pipeline Service API
 *
 * All pipeline-related API operations
 */
export const pipelineService = {
  /**
   * Get all available tools
   *
   * @param category Optional category filter
   * @returns List of tool definitions
   */
  async getTools(category?: string): Promise<ToolDefinition[]> {
    const endpoint = category
      ? `/api/pipeline/tools?category=${encodeURIComponent(category)}`
      : '/api/pipeline/tools';

    const response = await apiRequest<ToolListResponse>(endpoint);
    return response.tools;
  },

  /**
   * Get tools filtered by category
   *
   * @param category Category name
   * @returns List of tool definitions in that category
   */
  async getToolsByCategory(category: string): Promise<ToolDefinition[]> {
    return this.getTools(category);
  },

  /**
   * Execute a pipeline
   *
   * @param pipeline Pipeline to execute
   * @param userInputs Optional user-provided inputs
   * @param adaptiveMode Enable adaptive/refinement mode
   * @returns Execution response with execution_id
   */
  async executePipeline(
    pipeline: Pipeline,
    userInputs?: Record<string, Record<string, any>>,
    adaptiveMode: boolean = false
  ): Promise<PipelineExecuteResponse> {
    return apiRequest('/api/pipeline/execute', {
      method: 'POST',
      body: JSON.stringify({
        pipeline,
        user_inputs: userInputs,
        adaptive_mode: adaptiveMode,
      }),
    });
  },

  /**
   * Get execution status
   *
   * @param executionId Execution identifier
   * @returns Current execution status
   */
  async getExecutionStatus(executionId: string): Promise<ExecutionStatusResponse> {
    return apiRequest(`/api/pipeline/execution/${executionId}/status`);
  },

  /**
   * Save a pipeline to disk
   *
   * @param pipeline Pipeline to save
   * @param name Pipeline name
   * @param description Optional description
   * @returns Pipeline ID
   */
  async savePipeline(
    pipeline: Pipeline,
    name: string,
    description?: string
  ): Promise<string> {
    const response = await apiRequest<PipelineSaveResponse>(
      '/api/pipeline/save',
      {
        method: 'POST',
        body: JSON.stringify({
          pipeline,
          name,
          description,
        }),
      }
    );
    return response.pipeline_id;
  },

  /**
   * Load a saved pipeline
   *
   * @param pipelineId Pipeline identifier
   * @returns Complete pipeline definition
   */
  async loadPipeline(pipelineId: string): Promise<Pipeline> {
    return apiRequest(`/api/pipeline/saved/${pipelineId}`);
  },

  /**
   * List all saved pipelines
   *
   * @returns List of pipeline summaries
   */
  async listSavedPipelines(): Promise<PipelineSummary[]> {
    const response = await apiRequest<SavedPipelinesResponse>(
      '/api/pipeline/saved'
    );
    return response.pipelines;
  },

  /**
   * Delete a saved pipeline
   *
   * @param pipelineId Pipeline identifier
   */
  async deletePipeline(pipelineId: string): Promise<void> {
    await apiRequest(`/api/pipeline/saved/${pipelineId}`, {
      method: 'DELETE',
    });
  },
};

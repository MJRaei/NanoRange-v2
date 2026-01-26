/**
 * useSavedPipelines Hook
 *
 * Manages saved pipeline data fetching from the backend API.
 * Provides loading states, error handling, and CRUD operations.
 */

import { useState, useEffect, useCallback } from 'react';
import { pipelineService } from '../services/pipelineService';
import type { PipelineSummary } from '../services/types';
import type { Pipeline } from '../components/pipeline/types';

interface UseSavedPipelinesReturn {
  pipelines: PipelineSummary[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  loadPipeline: (pipelineId: string) => Promise<Pipeline>;
  deletePipeline: (pipelineId: string) => Promise<void>;
}

/**
 * Hook to fetch and manage saved pipelines from the backend
 *
 * @returns Pipelines data, loading state, error state, and operations
 */
export function useSavedPipelines(): UseSavedPipelinesReturn {
  const [pipelines, setPipelines] = useState<PipelineSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPipelines = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedPipelines = await pipelineService.listSavedPipelines();
      setPipelines(fetchedPipelines);
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : 'Failed to load saved pipelines';
      setError(errorMessage);
      console.error('Failed to fetch saved pipelines:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPipeline = useCallback(async (pipelineId: string): Promise<Pipeline> => {
    return pipelineService.loadPipeline(pipelineId);
  }, []);

  const deletePipeline = useCallback(async (pipelineId: string): Promise<void> => {
    await pipelineService.deletePipeline(pipelineId);
    // Refresh the list after deletion
    await fetchPipelines();
  }, [fetchPipelines]);

  useEffect(() => {
    fetchPipelines();
  }, [fetchPipelines]);

  return {
    pipelines,
    loading,
    error,
    refetch: fetchPipelines,
    loadPipeline,
    deletePipeline,
  };
}

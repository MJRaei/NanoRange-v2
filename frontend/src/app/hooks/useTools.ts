/**
 * useTools Hook
 *
 * Manages tool data fetching from the backend API.
 * Provides loading states, error handling, and refetch capability.
 */

import { useState, useEffect } from 'react';
import { pipelineService } from '../services/pipelineService';
import type { ToolDefinition } from '../components/pipeline/types';

interface UseToolsReturn {
  tools: ToolDefinition[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage tools from the backend
 *
 * @returns Tools data, loading state, error state, and refetch function
 */
export function useTools(): UseToolsReturn {
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTools = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedTools = await pipelineService.getTools();
      setTools(fetchedTools);
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : 'Failed to load tools';
      setError(errorMessage);
      console.error('Failed to fetch tools:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  return {
    tools,
    loading,
    error,
    refetch: fetchTools,
  };
}

'use client';

/**
 * SavedPipelinesPanel Component
 * Displays saved pipelines that can be loaded into the editor
 */

import React, { useState, useCallback } from 'react';
import { useSavedPipelines } from '../../hooks/useSavedPipelines';
import type { PipelineSummary } from '../../services/types';
import type { Pipeline } from './types';

interface SavedPipelinesPanelProps {
  onLoadPipeline: (pipeline: Pipeline) => void;
}

export function SavedPipelinesPanel({ onLoadPipeline }: SavedPipelinesPanelProps) {
  const { pipelines, loading, error, refetch, loadPipeline, deletePipeline } = useSavedPipelines();
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const handleLoad = useCallback(async (pipelineId: string) => {
    try {
      setLoadingId(pipelineId);
      const pipeline = await loadPipeline(pipelineId);
      onLoadPipeline(pipeline);
    } catch (err) {
      console.error('Failed to load pipeline:', err);
    } finally {
      setLoadingId(null);
    }
  }, [loadPipeline, onLoadPipeline]);

  const handleDelete = useCallback(async (pipelineId: string) => {
    try {
      setDeletingId(pipelineId);
      await deletePipeline(pipelineId);
      setConfirmDeleteId(null);
    } catch (err) {
      console.error('Failed to delete pipeline:', err);
    } finally {
      setDeletingId(null);
    }
  }, [deletePipeline]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Filter pipelines based on search
  const filteredPipelines = pipelines.filter(
    (pipeline) =>
      pipeline.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (pipeline.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
  );

  // Loading state
  if (loading) {
    return (
      <div className="h-full flex flex-col" style={{ backgroundColor: '#111' }}>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mb-2"></div>
            <p className="text-sm text-gray-400">Loading pipelines...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex flex-col" style={{ backgroundColor: '#111' }}>
        <div className="flex-1 flex flex-col items-center justify-center p-4">
          <svg
            className="w-12 h-12 text-red-500 mb-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm text-red-400 mb-2 font-medium">Failed to load pipelines</p>
          <p className="text-xs text-gray-500 mb-4 text-center max-w-xs">{error}</p>
          <button
            onClick={refetch}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#111' }}>
      {/* Search */}
      <div className="p-3 border-b" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search pipelines..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-1.5 rounded text-sm bg-black/30 border text-white placeholder-gray-500 focus:outline-none focus:border-orange-500/50"
            style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
          />
          <button
            onClick={refetch}
            className="p-1.5 hover:bg-white/10 rounded transition-colors"
            title="Refresh"
          >
            <svg
              className="w-4 h-4 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Pipeline list */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredPipelines.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4">
            <svg
              className="w-12 h-12 text-gray-600 mb-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <p className="text-sm text-gray-400 mb-1">
              {searchQuery ? 'No matching pipelines' : 'No saved pipelines'}
            </p>
            <p className="text-xs text-gray-500">
              {searchQuery ? 'Try a different search term' : 'Save a pipeline to see it here'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredPipelines.map((pipeline) => (
              <PipelineCard
                key={pipeline.pipeline_id}
                pipeline={pipeline}
                isLoading={loadingId === pipeline.pipeline_id}
                isDeleting={deletingId === pipeline.pipeline_id}
                isConfirmingDelete={confirmDeleteId === pipeline.pipeline_id}
                onLoad={() => handleLoad(pipeline.pipeline_id)}
                onDelete={() => handleDelete(pipeline.pipeline_id)}
                onConfirmDelete={() => setConfirmDeleteId(pipeline.pipeline_id)}
                onCancelDelete={() => setConfirmDeleteId(null)}
                formatDate={formatDate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface PipelineCardProps {
  pipeline: PipelineSummary;
  isLoading: boolean;
  isDeleting: boolean;
  isConfirmingDelete: boolean;
  onLoad: () => void;
  onDelete: () => void;
  onConfirmDelete: () => void;
  onCancelDelete: () => void;
  formatDate: (date: string) => string;
}

function PipelineCard({
  pipeline,
  isLoading,
  isDeleting,
  isConfirmingDelete,
  onLoad,
  onDelete,
  onConfirmDelete,
  onCancelDelete,
  formatDate,
}: PipelineCardProps) {
  return (
    <div
      className="p-3 rounded-lg border transition-colors hover:border-orange-500/30"
      style={{
        backgroundColor: 'rgba(0, 0, 0, 0.3)',
        borderColor: 'rgba(255, 255, 255, 0.1)',
      }}
    >
      {/* Pipeline info */}
      <div className="mb-2">
        <h4 className="text-sm font-medium text-white truncate">{pipeline.name}</h4>
        {pipeline.description && (
          <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{pipeline.description}</p>
        )}
      </div>

      {/* Metadata */}
      <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6z"
            />
          </svg>
          {pipeline.step_count} {pipeline.step_count === 1 ? 'step' : 'steps'}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          {formatDate(pipeline.modified_at)}
        </span>
      </div>

      {/* Actions */}
      {isConfirmingDelete ? (
        <div className="flex items-center gap-2">
          <span className="text-xs text-red-400 flex-1">Delete this pipeline?</span>
          <button
            onClick={onCancelDelete}
            disabled={isDeleting}
            className="px-2 py-1 text-xs rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="px-2 py-1 text-xs rounded bg-red-600 hover:bg-red-700 text-white transition-colors flex items-center gap-1"
          >
            {isDeleting && (
              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            )}
            Delete
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <button
            onClick={onLoad}
            disabled={isLoading}
            className="flex-1 px-3 py-1.5 text-xs rounded font-medium transition-colors flex items-center justify-center gap-1.5"
            style={{
              backgroundColor: 'rgba(255, 107, 53, 0.2)',
              color: '#ff6b35',
            }}
          >
            {isLoading ? (
              <>
                <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Loading...
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                  />
                </svg>
                Load Pipeline
              </>
            )}
          </button>
          <button
            onClick={onConfirmDelete}
            disabled={isLoading}
            className="p-1.5 rounded hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-colors"
            title="Delete pipeline"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

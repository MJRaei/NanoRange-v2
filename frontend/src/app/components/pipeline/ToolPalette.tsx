'use client';

/**
 * ToolPalette Component
 * Displays available tools that can be dragged onto the canvas
 */

import React, { useState, useCallback } from 'react';
import type { ToolDefinition } from './types';
import { useTools } from '../../hooks/useTools';

const categoryColors: Record<string, string> = {
  io: '#3b82f6',
  preprocessing: '#8b5cf6',
  segmentation: '#ec4899',
  ml_segmentation: '#c026d3',
  measurement: '#10b981',
  ml: '#f59e0b',
  vlm: '#6366f1',
};

const categoryLabels: Record<string, string> = {
  io: 'I/O',
  preprocessing: 'Preprocessing',
  segmentation: 'Segmentation',
  ml_segmentation: 'ML Segmentation',
  measurement: 'Measurement',
  ml: 'Machine Learning',
  vlm: 'Vision-Language',
};

interface ToolPaletteProps {
  onToolSelect?: (tool: ToolDefinition) => void;
}

export function ToolPalette({ onToolSelect }: ToolPaletteProps) {
  const { tools, loading, error, refetch } = useTools();
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(['io', 'preprocessing', 'segmentation'])
  );

  const toggleCategory = useCallback((category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }, []);

  const handleDragStart = useCallback(
    (e: React.DragEvent, tool: ToolDefinition) => {
      e.dataTransfer.setData('tool', JSON.stringify(tool));
      e.dataTransfer.effectAllowed = 'copy';
    },
    []
  );

  // Group tools by category
  const toolsByCategory = tools.reduce<Record<string, ToolDefinition[]>>(
    (acc, tool) => {
      if (!acc[tool.category]) {
        acc[tool.category] = [];
      }
      acc[tool.category].push(tool);
      return acc;
    },
    {}
  );

  // Filter tools based on search
  const filteredCategories = Object.entries(toolsByCategory)
    .map(([category, tools]) => ({
      category,
      tools: tools.filter(
        (tool) =>
          tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tool.description.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    }))
    .filter(({ tools }) => tools.length > 0);

  // Loading state
  if (loading) {
    return (
      <div className="h-full flex flex-col" style={{ backgroundColor: '#111' }}>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mb-2"></div>
            <p className="text-sm text-gray-400">Loading tools...</p>
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
          <p className="text-sm text-red-400 mb-2 font-medium">Failed to load tools</p>
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
        <input
          type="text"
          placeholder="Search tools..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-3 py-1.5 rounded text-sm bg-black/30 border text-white placeholder-gray-500 focus:outline-none focus:border-orange-500/50"
          style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}
        />
      </div>

      {/* Tool list */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredCategories.map(({ category, tools }) => (
          <div key={category} className="mb-2">
            {/* Category header */}
            <button
              onClick={() => toggleCategory(category)}
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 transition-colors"
            >
              <svg
                className={`w-3 h-3 text-gray-400 transition-transform ${
                  expandedCategories.has(category) ? 'rotate-90' : ''
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: categoryColors[category] }}
              />
              <span className="text-xs font-medium text-gray-300">
                {categoryLabels[category] || category}
              </span>
            </button>

            {/* Tools in category */}
            {expandedCategories.has(category) && (
              <div className="mt-1 ml-4 space-y-1">
                {tools.map((tool) => (
                  <div
                    key={tool.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, tool)}
                    onClick={() => onToolSelect?.(tool)}
                    className="flex items-center gap-2 px-2 py-1.5 rounded cursor-grab active:cursor-grabbing hover:bg-white/5 transition-colors group"
                    style={{
                      borderLeft: `2px solid ${categoryColors[category]}`,
                    }}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-200 truncate">
                        {tool.name}
                      </p>
                      <p className="text-[10px] text-gray-500 truncate">
                        {tool.description}
                      </p>
                    </div>
                    <svg
                      className="w-3 h-3 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                      />
                    </svg>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

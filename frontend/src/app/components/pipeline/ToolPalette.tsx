'use client';

/**
 * ToolPalette Component
 * Displays available tools that can be dragged onto the canvas
 */

import React, { useState, useCallback } from 'react';
import type { ToolDefinition } from './types';

// Mock tools for initial UI - will be replaced with API call
const mockTools: ToolDefinition[] = [
  {
    id: 'load_image',
    name: 'Load Image',
    description: 'Load an image from file path',
    category: 'io',
    inputs: [
      { name: 'path', type: 'PATH', description: 'Image file path', required: true },
    ],
    outputs: [
      { name: 'image', type: 'IMAGE', description: 'Loaded image' },
    ],
  },
  {
    id: 'save_image',
    name: 'Save Image',
    description: 'Save an image to file',
    category: 'io',
    inputs: [
      { name: 'image', type: 'IMAGE', description: 'Image to save', required: true },
      { name: 'path', type: 'PATH', description: 'Output file path', required: true },
    ],
    outputs: [
      { name: 'path', type: 'PATH', description: 'Saved file path' },
    ],
  },
  {
    id: 'gaussian_blur',
    name: 'Gaussian Blur',
    description: 'Apply Gaussian blur to reduce noise',
    category: 'preprocessing',
    inputs: [
      { name: 'image', type: 'IMAGE', description: 'Input image', required: true },
      { name: 'sigma', type: 'FLOAT', description: 'Blur strength', required: false, default: 1.0 },
    ],
    outputs: [
      { name: 'image', type: 'IMAGE', description: 'Blurred image' },
    ],
  },
  {
    id: 'normalize',
    name: 'Normalize',
    description: 'Normalize image intensity',
    category: 'preprocessing',
    inputs: [
      { name: 'image', type: 'IMAGE', description: 'Input image', required: true },
    ],
    outputs: [
      { name: 'image', type: 'IMAGE', description: 'Normalized image' },
    ],
  },
  {
    id: 'threshold',
    name: 'Threshold',
    description: 'Apply thresholding to create binary mask',
    category: 'segmentation',
    inputs: [
      { name: 'image', type: 'IMAGE', description: 'Input image', required: true },
      { name: 'method', type: 'STRING', description: 'Thresholding method', required: false, default: 'otsu' },
    ],
    outputs: [
      { name: 'mask', type: 'MASK', description: 'Binary mask' },
    ],
  },
  {
    id: 'morphological_ops',
    name: 'Morphological Ops',
    description: 'Apply morphological operations',
    category: 'segmentation',
    inputs: [
      { name: 'mask', type: 'MASK', description: 'Input mask', required: true },
      { name: 'operation', type: 'STRING', description: 'Operation type', required: false, default: 'open' },
    ],
    outputs: [
      { name: 'mask', type: 'MASK', description: 'Processed mask' },
    ],
  },
  {
    id: 'measure_area',
    name: 'Measure Area',
    description: 'Measure areas of detected objects',
    category: 'measurement',
    inputs: [
      { name: 'mask', type: 'MASK', description: 'Binary mask', required: true },
      { name: 'pixel_size', type: 'FLOAT', description: 'Pixel size in nm', required: false, default: 1.0 },
    ],
    outputs: [
      { name: 'measurements', type: 'MEASUREMENTS', description: 'Area measurements' },
    ],
  },
  {
    id: 'count_objects',
    name: 'Count Objects',
    description: 'Count objects in mask',
    category: 'measurement',
    inputs: [
      { name: 'mask', type: 'MASK', description: 'Binary mask', required: true },
    ],
    outputs: [
      { name: 'count', type: 'INT', description: 'Object count' },
    ],
  },
  {
    id: 'cellpose_segmentation',
    name: 'Cellpose',
    description: 'Deep learning segmentation with Cellpose',
    category: 'ml',
    inputs: [
      { name: 'image', type: 'IMAGE', description: 'Input image', required: true },
      { name: 'model', type: 'STRING', description: 'Model type', required: false, default: 'cyto2' },
      { name: 'diameter', type: 'FLOAT', description: 'Expected object diameter', required: false, default: 30.0 },
    ],
    outputs: [
      { name: 'mask', type: 'MASK', description: 'Segmentation mask' },
      { name: 'outlines', type: 'IMAGE', description: 'Object outlines' },
    ],
  },
];

const categoryColors: Record<string, string> = {
  io: '#3b82f6',
  preprocessing: '#8b5cf6',
  segmentation: '#ec4899',
  measurement: '#10b981',
  ml: '#f59e0b',
  vlm: '#6366f1',
};

const categoryLabels: Record<string, string> = {
  io: 'I/O',
  preprocessing: 'Preprocessing',
  segmentation: 'Segmentation',
  measurement: 'Measurement',
  ml: 'Machine Learning',
  vlm: 'Vision-Language',
};

interface ToolPaletteProps {
  onToolSelect?: (tool: ToolDefinition) => void;
}

export function ToolPalette({ onToolSelect }: ToolPaletteProps) {
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
  const toolsByCategory = mockTools.reduce<Record<string, ToolDefinition[]>>(
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

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: '#111' }}>
      {/* Header */}
      <div className="p-3 border-b" style={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
        <h3 className="text-sm font-semibold text-white mb-2">Tools</h3>
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
              <span className="text-xs text-gray-500 ml-auto">{tools.length}</span>
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

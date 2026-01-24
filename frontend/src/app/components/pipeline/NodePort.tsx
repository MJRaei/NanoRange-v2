'use client';

/**
 * NodePort Component
 * Renders a connection port on the left or right side of a node.
 * Left ports receive connections, right ports send connections.
 * Ports are positioned exactly on the border of the node.
 */

import { MouseEvent as ReactMouseEvent } from 'react';

interface NodePortProps {
  side: 'left' | 'right';
  isConnected: boolean;
  isHovered?: boolean;
  onMouseDown?: (e: ReactMouseEvent) => void;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

export function NodePort({
  side,
  isConnected,
  isHovered,
  onMouseDown,
  onMouseEnter,
  onMouseLeave,
}: NodePortProps) {
  const isLeft = side === 'left';

  return (
    <div
      className={`
        absolute top-1/2 -translate-y-1/2 z-10
        ${isLeft ? 'left-0 -translate-x-1/2' : 'right-0 translate-x-1/2'}
      `}
    >
      {/* Port connector - positioned exactly on the border */}
      <div
        className={`
          w-3 h-3 rounded-full border-2 cursor-pointer
          transition-all duration-150
          ${isConnected
            ? 'bg-green-500 border-green-400 shadow-[0_0_6px_rgba(34,197,94,0.5)]'
            : isHovered
              ? 'bg-orange-400 border-orange-300 shadow-[0_0_6px_rgba(251,146,60,0.5)]'
              : 'bg-gray-700 border-gray-500 hover:border-orange-400 hover:bg-gray-600'
          }
        `}
        onMouseDown={onMouseDown}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      />
    </div>
  );
}

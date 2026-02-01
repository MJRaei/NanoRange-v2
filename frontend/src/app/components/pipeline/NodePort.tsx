'use client';

/**
 * NodePort Component
 * Renders a connection port on the left or right side of a node.
 * Left ports receive connections, right ports send connections.
 * Ports are positioned exactly on the border of the node.
 * Includes an expanded hit area for easier interaction.
 */

import { useState, MouseEvent as ReactMouseEvent } from 'react';

interface NodePortProps {
  side: 'left' | 'right';
  isConnected: boolean;
  isHovered?: boolean;
  onMouseDown?: (e: ReactMouseEvent) => void;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

// Expanded hit area size (pixels)
const HIT_AREA_SIZE = 32;

export function NodePort({
  side,
  isConnected,
  isHovered,
  onMouseDown,
  onMouseEnter,
  onMouseLeave,
}: NodePortProps) {
  const isLeft = side === 'left';
  const [isLocalHover, setIsLocalHover] = useState(false);

  const handleMouseEnter = () => {
    setIsLocalHover(true);
    onMouseEnter?.();
  };

  const handleMouseLeave = () => {
    setIsLocalHover(false);
    onMouseLeave?.();
  };

  const showHoverState = isHovered || isLocalHover;

  return (
    <div
      className={`
        absolute top-1/2 -translate-y-1/2 z-10
        ${isLeft ? 'left-0 -translate-x-1/2' : 'right-0 translate-x-1/2'}
      `}
    >
      {/* Expanded invisible hit area for easier clicking/hovering */}
      <div
        className="absolute cursor-pointer"
        style={{
          width: HIT_AREA_SIZE,
          height: HIT_AREA_SIZE,
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
        }}
        onMouseDown={onMouseDown}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      />
      {/* Visible port connector - positioned exactly on the border */}
      <div
        className={`
          w-3 h-3 rounded-full border-2 pointer-events-none
          transition-all duration-150
          ${isConnected
            ? 'bg-green-500 border-green-400 shadow-[0_0_6px_rgba(34,197,94,0.5)]'
            : showHoverState
              ? 'bg-orange-400 border-orange-300 shadow-[0_0_6px_rgba(251,146,60,0.5)]'
              : 'bg-gray-700 border-gray-500'
          }
        `}
      />
    </div>
  );
}

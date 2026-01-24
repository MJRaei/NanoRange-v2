/**
 * Connection Utilities
 * Provides utilities for determining port visibility, type compatibility,
 * and input satisfaction status for pipeline nodes.
 */

import type { ToolDefinition, ToolInput, ToolOutput, DataType, NodeInputValue, PipelineEdge } from '../types';

// Types that flow through visual node connections (ports)
export const CONNECTABLE_TYPES: DataType[] = ['IMAGE', 'MASK', 'ARRAY'];

// Types that are set via ParameterPanel (not through connections)
export const STATIC_TYPES: DataType[] = ['PATH', 'STRING', 'FLOAT', 'INT', 'BOOL', 'LIST', 'DICT'];

/**
 * Check if a data type is connectable (flows through node ports)
 */
export function isConnectableType(type: DataType): boolean {
  return CONNECTABLE_TYPES.includes(type);
}

/**
 * Get the primary connectable input for a tool (first IMAGE or MASK input)
 */
export function getPrimaryConnectableInput(tool: ToolDefinition): ToolInput | null {
  return tool.inputs.find(input => isConnectableType(input.type)) || null;
}

/**
 * Get the primary connectable output for a tool (first IMAGE or MASK output)
 */
export function getPrimaryConnectableOutput(tool: ToolDefinition): ToolOutput | null {
  return tool.outputs.find(output => isConnectableType(output.type)) || null;
}

/**
 * Determine if a tool should have a left (input) port
 */
export function hasInputPort(tool: ToolDefinition): boolean {
  return getPrimaryConnectableInput(tool) !== null;
}

/**
 * Determine if a tool should have a right (output) port
 */
export function hasOutputPort(tool: ToolDefinition): boolean {
  return getPrimaryConnectableOutput(tool) !== null;
}

/**
 * Port configuration for a tool
 */
export interface PortConfig {
  hasInputPort: boolean;
  hasOutputPort: boolean;
  primaryInput: ToolInput | null;
  primaryOutput: ToolOutput | null;
}

/**
 * Get port configuration for a tool
 */
export function getPortConfig(tool: ToolDefinition): PortConfig {
  return {
    hasInputPort: hasInputPort(tool),
    hasOutputPort: hasOutputPort(tool),
    primaryInput: getPrimaryConnectableInput(tool),
    primaryOutput: getPrimaryConnectableOutput(tool),
  };
}

/**
 * Input satisfaction status
 */
export type SatisfactionStatus = 'satisfied' | 'unsatisfied' | 'optional';

/**
 * Check if an input is satisfied (has a value, connection, or default)
 */
export function getInputSatisfactionStatus(
  input: ToolInput,
  nodeInputValue: NodeInputValue | undefined,
  inputConnections: PipelineEdge[],
  inputName: string
): SatisfactionStatus {
  // Check if connected via edge
  const hasEdgeConnection = inputConnections.some(e => e.targetInput === inputName);
  if (hasEdgeConnection) return 'satisfied';

  // Check if has connection value (redundant with edge check, but for safety)
  if (nodeInputValue?.type === 'connection') {
    return 'satisfied';
  }

  // Check if has static value that is not empty
  if (nodeInputValue?.type === 'static' && nodeInputValue.value !== undefined && nodeInputValue.value !== '') {
    return 'satisfied';
  }

  // Check if has default value in the tool schema
  if (input.default !== undefined) {
    return 'satisfied';
  }

  // If not required, it's optional (can proceed without it)
  if (!input.required) {
    return 'optional';
  }

  // Required with no value
  return 'unsatisfied';
}

/**
 * Check if all required inputs are satisfied for a node
 */
export function areAllRequiredInputsSatisfied(
  tool: ToolDefinition,
  nodeInputs: Record<string, NodeInputValue>,
  inputConnections: PipelineEdge[]
): boolean {
  return tool.inputs.every(input => {
    const status = getInputSatisfactionStatus(
      input,
      nodeInputs[input.name],
      inputConnections,
      input.name
    );
    return status !== 'unsatisfied';
  });
}

/**
 * Check if two types are compatible for connection
 */
export function areTypesCompatible(outputType: DataType, inputType: DataType): boolean {
  // Exact match
  if (outputType === inputType) return true;

  // IMAGE and MASK are compatible with each other (and ARRAY)
  const imageTypes: DataType[] = ['IMAGE', 'MASK', 'ARRAY'];
  if (imageTypes.includes(outputType) && imageTypes.includes(inputType)) {
    return true;
  }

  // Numeric types are compatible
  const numericTypes: DataType[] = ['FLOAT', 'INT'];
  if (numericTypes.includes(outputType) && numericTypes.includes(inputType)) {
    return true;
  }

  return false;
}

/**
 * Shared TypeScript types for the NanOrange frontend
 */

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  images?: MessageImage[];
  csvPath?: string;
  attachedImage?: string;
}

export interface MessageImage {
  key: string;
  url: string;
  title: string;
}

export interface AnalysisImages {
  thresholded_with_shapes?: string;
  size_distribution?: string;
  original?: string;
  colorized?: string;
  thresholded?: string;
  original_with_shapes?: string;
  colorized_with_shapes?: string;
  original_with_shapes_html?: string;
  colorized_with_shapes_html?: string;
  thresholded_with_shapes_html?: string;
  size_distribution_html?: string;
}

export interface AnalysisResult {
  success: boolean;
  message: string;
  images: AnalysisImages;
  csv_path: string | null;
  session_id: string;
}

export interface FileInfo {
  name: string;
  path: string;
  type: string;
  interactive_html?: string | null;  // Path to interactive HTML version if available
}

export interface SidebarFiles {
  images: FileInfo[];
  plots: FileInfo[];
  csv_files: FileInfo[];
}


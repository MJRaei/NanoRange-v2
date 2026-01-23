/**
 * API client for communicating with the NanOrange backend
 */

import { AnalysisResult, SidebarFiles } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Upload an image for analysis
 */
export async function uploadImage(file: File): Promise<{ success: boolean; file_path: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/chat/upload-image`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload image");
  }

  return response.json();
}

/**
 * Run analysis on an uploaded image
 */
export async function analyzeImage(
  message: string,
  imagePath: string | null,
  sessionId: string | null = null
): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("message", message);
  if (imagePath) {
    formData.append("image_path", imagePath);
  }
  if (sessionId) {
    formData.append("session_id", sessionId);
  }

  const response = await fetch(`${API_BASE_URL}/api/chat/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to analyze image");
  }

  return response.json();
}

/**
 * List all available output files
 */
export async function listFiles(sessionId?: string): Promise<SidebarFiles> {
  const url = sessionId 
    ? `${API_BASE_URL}/api/files/list?session_id=${encodeURIComponent(sessionId)}`
    : `${API_BASE_URL}/api/files/list`;
  
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error("Failed to list files");
  }

  return response.json();
}

/**
 * Get full URL for an image
 */
export function getImageUrl(path: string): string {
  return `${API_BASE_URL}/api/files/image/${encodeURIComponent(path)}`;
}

/**
 * Get full URL for an HTML file (interactive plot)
 */
export function getHtmlUrl(path: string): string {
  return `${API_BASE_URL}/api/files/html/${encodeURIComponent(path)}`;
}

/**
 * Get download URL for a CSV file
 */
export function getCsvUrl(path: string): string {
  return `${API_BASE_URL}/api/files/csv/${encodeURIComponent(path)}`;
}

/**
 * Get static URL for output files
 */
export function getStaticUrl(path: string): string {
  // Remove leading path components (data/files/ or ./data/files/)
  const cleanPath = path.replace(/^(\.\/)?data\/files\//, "");
  return `${API_BASE_URL}/static/data/${cleanPath}`;
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/health`);
    return response.ok;
  } catch {
    return false;
  }
}


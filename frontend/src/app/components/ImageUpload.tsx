"use client";

import { useRef, useState, useCallback } from "react";
import { uploadImage } from "./api";

interface ImageUploadProps {
  onImageUploaded: (path: string, previewUrl: string) => void;
  disabled?: boolean;
}

export function ImageUpload({ onImageUploaded, disabled }: ImageUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileSelect = async (file: File) => {
    if (!file) return;

    // Validate file type
    const validTypes = ["image/jpeg", "image/png", "image/jpg", "image/tiff"];
    if (!validTypes.includes(file.type)) {
      alert("Please upload a valid image file (JPEG, PNG, or TIFF)");
      return;
    }

    setIsUploading(true);

    try {
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);

      // Upload to backend
      const result = await uploadImage(file);

      if (result.success) {
        onImageUploaded(result.file_path, previewUrl);
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      console.error("Error uploading image:", error);
      alert("Failed to upload image. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleClick = () => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !isUploading) {
      setIsDragging(true);
    }
  }, [disabled, isUploading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled || isUploading) return;

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [disabled, isUploading]);

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/jpg,image/tiff"
        onChange={handleChange}
        className="hidden"
      />
      <button
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        disabled={disabled || isUploading}
        className={`shrink-0 p-2 rounded-lg transition-colors ${
          isDragging ? "upload-button-dragging" : ""
        } ${disabled ? "opacity-30 cursor-not-allowed" : "hover:bg-white/5"}`}
        style={{ color: isDragging ? "#ff6b35" : "#6a655d" }}
        title="Attach image for analysis"
      >
        {isUploading ? (
          <div className="w-5 h-5 upload-spinner" />
        ) : (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
            />
          </svg>
        )}
      </button>
    </>
  );
}

interface AttachedImagePreviewProps {
  previewUrl: string;
  onRemove: () => void;
}

export function AttachedImagePreview({ previewUrl, onRemove }: AttachedImagePreviewProps) {
  return (
    <div className="relative inline-block mr-2 mb-2">
      <img
        src={previewUrl}
        alt="Attached image"
        className="h-20 w-20 object-cover rounded-lg"
        style={{ border: "1px solid rgba(255, 107, 53, 0.3)" }}
      />
      <button
        onClick={onRemove}
        className="absolute -top-2 -right-2 w-5 h-5 rounded-full flex items-center justify-center"
        style={{ backgroundColor: "#ff6b35", color: "#0a0908" }}
      >
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}


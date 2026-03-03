import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { X, AlertCircle, Loader2 } from 'lucide-react';
import api from '../api/axios';

/**
 * Camera Preview Modal
 * 
 * Fetches an MJPEG stream from the Central Server using the Axios instance
 * (which adds Authorization: Bearer header automatically).
 * 
 * We cannot use <img src="..."> because it can't send custom headers.
 * Instead we use fetch() to read the multipart/x-mixed-replace stream,
 * parse JPEG frames, and draw them on a <canvas> element.
 */
const CameraPreviewModal = ({ isOpen, onClose, cameraId, cameraRtsp }) => {
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const canvasRef = useRef(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    if (!isOpen || !cameraId) return;

    setHasError(false);
    setIsLoading(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const streamMjpeg = async () => {
      try {
        // Build the URL — path is relative to api.defaults.baseURL
        const baseUrl = api.defaults.baseURL || '/api';
        const previewPath = `/hardware/cameras/${cameraId}/preview`;

        const response = await fetch(`${baseUrl}${previewPath}`, {
          headers: {
            // Token is in-memory in AuthContext — always fresh in axios defaults
            Authorization: api.defaults.headers.common['Authorization'] || '',
          },
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        setIsLoading(false);

        // Read the raw bytes of the multipart stream
        const reader = response.body.getReader();
        let buffer = new Uint8Array(0);

        // JPEG SOI (start of image) and EOI (end of image) markers
        const SOI = [0xFF, 0xD8];
        const EOI = [0xFF, 0xD9];

        const findSequence = (arr, seq, fromIndex = 0) => {
          outer: for (let i = fromIndex; i <= arr.length - seq.length; i++) {
            for (let j = 0; j < seq.length; j++) {
              if (arr[i + j] !== seq[j]) continue outer;
            }
            return i;
          }
          return -1;
        };

        const canvas = canvasRef.current;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Append new data to buffer
          const newBuffer = new Uint8Array(buffer.length + value.length);
          newBuffer.set(buffer);
          newBuffer.set(value, buffer.length);
          buffer = newBuffer;

          // Look for JPEG frames: find SOI..EOI pairs
          let soiIndex;
          while ((soiIndex = findSequence(buffer, SOI)) !== -1) {
            const eoiIndex = findSequence(buffer, EOI, soiIndex + 2);
            if (eoiIndex === -1) break; // frame not complete yet

            const jpegData = buffer.slice(soiIndex, eoiIndex + 2);
            buffer = buffer.slice(eoiIndex + 2); // consume frame from buffer

            // Draw JPEG frame on canvas
            const blob = new Blob([jpegData], { type: 'image/jpeg' });
            const url = URL.createObjectURL(blob);
            const img = new Image();
            img.onload = () => {
              if (canvas) {
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                canvas.getContext('2d').drawImage(img, 0, 0);
              }
              URL.revokeObjectURL(url);
            };
            img.src = url;
          }
        }
      } catch (err) {
        if (err.name === 'AbortError') return; // intentional close
        console.error('[CameraPreview] Stream error:', err);
        setHasError(true);
        setIsLoading(false);
      }
    };

    streamMjpeg();

    return () => {
      abortController.abort();
    };
  }, [isOpen, cameraId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-background/90 backdrop-blur-md"
      />
      <motion.div
        initial={{ scale: 0.95, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 20 }}
        className="relative w-full max-w-4xl bg-card border border-border rounded-3xl overflow-hidden shadow-2xl flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-border bg-secondary/30 flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold">Live Camera Preview</h3>
            <p className="text-xs text-muted-foreground font-mono mt-1">{cameraRtsp}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
          >
            <X size={20} />
          </button>
        </div>

        {/* Video Area */}
        <div className="relative bg-black aspect-video flex items-center justify-center overflow-hidden">
          {isLoading && !hasError && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-white/70 z-10 bg-black/50 backdrop-blur-sm">
              <Loader2 className="animate-spin mb-4" size={40} />
              <p className="font-medium animate-pulse">Connecting to Edge Node tunnel...</p>
            </div>
          )}

          {hasError ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-destructive z-10 bg-black">
              <AlertCircle size={48} className="mb-4 opacity-80" />
              <p className="font-bold text-lg">Stream Unavailable</p>
              <p className="text-sm opacity-80 mt-1 max-w-sm text-center">
                The Edge Node might be offline or the camera is unreachable.
              </p>
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              className="w-full h-full object-contain"
            />
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default CameraPreviewModal;

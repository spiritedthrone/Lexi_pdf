import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
  Download,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { uploadPdf, simplifyPdf, downloadPdf } from '../services/api';

const MAX_FILE_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;


export default function PdfUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  
  // Progress & Status Tracking
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isSimplifying, setIsSimplifying] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  
  // Data State
  const [uploadedData, setUploadedData] = useState(null);
  const [simplifiedData, setSimplifiedData] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const fileInputRef = useRef(null);

  const validateFile = (selectedFile) => {
    if (!selectedFile) return 'No file selected.';
    if (
      selectedFile.type !== 'application/pdf' &&
      !selectedFile.name.toLowerCase().endsWith('.pdf')
    ) {
      return 'Invalid file type. Only PDF files are supported.';
    }
    if (selectedFile.size === 0) {
      return 'Selected file is empty.';
    }
    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      return `File size exceeds the limit of ${MAX_FILE_SIZE_MB}MB.`;
    }
    return null;
  };

  const handleFileSelect = (selectedFile) => {
    setError(null);
    setUploadedData(null);
    setSimplifiedData(null);
    setUploadProgress(0);
    setStatusMessage('');

    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const startProcess = async () => {
    if (!file) return;

    setError(null);
    setIsUploading(true);
    setUploadProgress(0);
    setStatusMessage('Uploading and extracting PDF text...');

    try {
      // Step 1: Upload & Chunk PDF
      const uploadRes = await uploadPdf(file, (percent) => {
        setUploadProgress(percent);
      });

      setUploadedData(uploadRes);
      setIsUploading(false);

      // Step 2: AI Simplification
      setIsSimplifying(true);
      setStatusMessage('Rewriting document into simpler English...');

      const simplifyRes = await simplifyPdf(uploadRes.id);
      setSimplifiedData(simplifyRes);
      setStatusMessage('Simplification complete! Your document is ready for download.');
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'An error occurred during processing.';
      setError(msg);
    } finally {
      setIsUploading(false);
      setIsSimplifying(false);
    }
  };

  const handleDownload = async () => {
    if (!uploadedData?.id) return;
    setIsDownloading(true);
    setError(null);

    try {
      const downloadName = `simplified_${file?.name || 'document.pdf'}`;
      await downloadPdf(uploadedData.id, downloadName);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Download failed.');
    } finally {
      setIsDownloading(false);
    }
  };

  const resetAll = () => {
    setFile(null);
    setError(null);
    setUploadProgress(0);
    setIsUploading(false);
    setIsSimplifying(false);
    setStatusMessage('');
    setUploadedData(null);
    setSimplifiedData(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full space-y-5">
      {/* Step Indicators */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs font-medium">
        <div
          className={`py-2 px-3 rounded-lg border transition ${
            isUploading
              ? 'bg-indigo-950/60 border-indigo-500 text-indigo-300 animate-pulse'
              : uploadedData
              ? 'bg-slate-900/80 border-slate-700 text-slate-300'
              : 'bg-slate-900/30 border-slate-800 text-slate-400'
          }`}
        >
          1. Upload & Extract
        </div>
        <div
          className={`py-2 px-3 rounded-lg border transition ${
            isSimplifying
              ? 'bg-indigo-950/60 border-indigo-500 text-indigo-300 animate-pulse'
              : simplifiedData
              ? 'bg-slate-900/80 border-slate-700 text-slate-300'
              : 'bg-slate-900/30 border-slate-800 text-slate-400'
          }`}
        >
          2. AI Simplification
        </div>
        <div
          className={`py-2 px-3 rounded-lg border transition ${
            simplifiedData
              ? 'bg-emerald-950/50 border-emerald-600 text-emerald-300'
              : 'bg-slate-900/30 border-slate-800 text-slate-400'
          }`}
        >
          3. Download Output
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && !isUploading && !isSimplifying && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-6 md:p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-indigo-400 bg-indigo-950/50 scale-[1.01]'
            : file
            ? 'border-slate-700 bg-slate-900/70'
            : 'border-slate-700 hover:border-slate-500 bg-slate-900/40 hover:bg-slate-900/80'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
          className="hidden"
          disabled={isUploading || isSimplifying}
        />

        {!file ? (
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="p-3.5 bg-indigo-500/10 rounded-full border border-indigo-500/20 text-indigo-400">
              <UploadCloud className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200">
                Drag & drop your PDF here, or{' '}
                <span className="text-indigo-400 underline underline-offset-2">browse file</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">Maximum file size: {MAX_FILE_SIZE_MB}MB</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between p-3.5 bg-slate-800/80 rounded-xl border border-slate-700">
            <div className="flex items-center space-x-3 truncate">
              <FileText className="w-8 h-8 text-indigo-400 shrink-0" />
              <div className="truncate text-left">
                <p className="text-sm font-medium text-slate-200 truncate">{file.name}</p>
                <p className="text-xs text-slate-400">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
            {!isUploading && !isSimplifying && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  resetAll();
                }}
                className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-slate-200 transition"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Error Message Box */}
      {error && (
        <div className="flex items-start justify-between p-4 bg-rose-950/50 border border-rose-800/60 rounded-xl text-rose-200 text-xs sm:text-sm">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-300">Processing Error</p>
              <p className="mt-0.5 text-rose-200/90">{error}</p>
            </div>
          </div>
          {file && (
            <button
              onClick={startProcess}
              className="ml-3 px-3 py-1.5 bg-rose-900/60 hover:bg-rose-800 border border-rose-700 text-white font-medium rounded-lg text-xs shrink-0 flex items-center space-x-1"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          )}
        </div>
      )}


      {/* Progress & Processing Status Bar */}
      {(isUploading || isSimplifying) && (
        <div className="space-y-2.5 p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
          <div className="flex justify-between text-xs text-slate-300 font-medium">
            <span className="flex items-center">
              <Loader2 className="w-4 h-4 mr-2 animate-spin text-indigo-400" />
              {statusMessage}
            </span>
            {isUploading && <span>{uploadProgress}%</span>}
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ease-out ${
                isSimplifying ? 'bg-indigo-400 animate-pulse w-full' : 'bg-indigo-500'
              }`}
              style={{ width: isUploading ? `${uploadProgress}%` : '100%' }}
            />
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {file && !simplifiedData && !isUploading && !isSimplifying && (
        <button
          type="button"
          onClick={startProcess}
          className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl text-sm transition flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/25 active:scale-[0.99]"
        >
          <Sparkles className="w-4 h-4 text-indigo-200" />
          <span>Start AI Simplification</span>
        </button>
      )}

      {/* Simplified Output Ready & Download Button */}
      {simplifiedData && (
        <div className="space-y-3 p-5 bg-emerald-950/30 border border-emerald-800/60 rounded-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <span className="font-semibold text-emerald-200 text-sm">
                Document Simplified Successfully!
              </span>
            </div>
            <button
              onClick={resetAll}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          </div>

          <div className="text-xs text-slate-300 grid grid-cols-2 gap-2 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div>Total Chunks: <span className="font-semibold text-white">{simplifiedData.total_chunks}</span></div>
            <div>Total Words: <span className="font-semibold text-white">{simplifiedData.total_words}</span></div>
            <div>Paragraphs: <span className="font-semibold text-white">{simplifiedData.total_paragraphs}</span></div>
            <div>Chapters: <span className="font-semibold text-white">{simplifiedData.chapters_found?.length || 0}</span></div>
          </div>

          <button
            type="button"
            onClick={handleDownload}
            disabled={isDownloading}
            className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl text-sm transition flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/25 active:scale-[0.99] disabled:opacity-50"
          >
            {isDownloading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Preparing PDF Download...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Download Rewritten PDF</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

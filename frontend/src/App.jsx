import React, { useEffect, useState } from 'react';
import { FileText, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { checkHealth } from './services/api';
import PdfUploader from './components/PdfUploader';
import './App.css';

export default function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const verifyBackend = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkHealth();
      setHealthStatus(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    verifyBackend();
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">
      <div className="w-full max-w-2xl glass-panel p-6 sm:p-8 rounded-2xl shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <FileText className="w-8 h-8 text-indigo-400 shrink-0" />
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">PDF Summarizer & Simplifier</h1>
          </div>
          <div className="flex items-center text-xs shrink-0">
            {loading ? (
              <span className="flex items-center text-amber-400">
                <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" /> Checking
              </span>
            ) : error ? (
              <span className="flex items-center text-rose-400">
                <AlertCircle className="w-3.5 h-3.5 mr-1" /> Offline
              </span>
            ) : (
              <span className="flex items-center text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> System Ready
              </span>
            )}
          </div>
        </div>

        <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
          Upload any PDF document to extract text, simplify difficult phrasing into clear English, and download a cleanly formatted PDF output.
        </p>

        {/* PDF Uploader Component */}
        <PdfUploader />
      </div>
    </div>
  );
}



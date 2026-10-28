import React, { useState, useEffect } from 'react';
import {
  getStoredApiBaseUrl,
  setStoredApiBaseUrl,
  isSimulatorForced,
  setSimulatorForced,
  apiClient,
} from '../services/api';
import { X, Server, CheckCircle2, AlertTriangle, RefreshCw, Cpu } from 'lucide-react';

interface ConnectionSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnectionChanged?: () => void;
}

export const ConnectionSettingsModal: React.FC<ConnectionSettingsModalProps> = ({
  isOpen,
  onClose,
  onConnectionChanged,
}) => {
  const [url, setUrl] = useState<string>('');
  const [useSimulator, setUseSimulator] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setUrl(getStoredApiBaseUrl());
      setUseSimulator(isSimulatorForced());
      setTestResult(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    // Temporarily save to test target url
    setStoredApiBaseUrl(url);

    try {
      const result = await apiClient.checkHealth();
      if (result.ok) {
        setTestResult({
          ok: true,
          message: `Connected successfully! Status: ${result.data?.status || 'ok'} (FastAPI Backend)`,
        });
      } else {
        setTestResult({
          ok: false,
          message: `Connection failed: ${result.error || 'Server unreachable at this address'}`,
        });
      }
    } catch (err: any) {
      setTestResult({
        ok: false,
        message: err.message || 'Connection failed',
      });
    } finally {
      setIsTesting(false);
      onConnectionChanged?.();
    }
  };

  const handleSave = () => {
    setStoredApiBaseUrl(url);
    setSimulatorForced(useSimulator);
    onConnectionChanged?.();
    onClose();
  };

  return (
    <div
      className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="connection-modal-title"
    >
      <div className="modal-panel bg-surface rounded-2xl max-w-lg w-full shadow-pop">
        <div className="flex items-center justify-between px-7 pt-6 pb-5 border-b border-line">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
              <Server size={17} />
            </div>
            <h3 id="connection-modal-title" className="text-base font-semibold text-ink">
              Backend connection
            </h3>
          </div>
          <button onClick={onClose} aria-label="Close modal" className="icon-btn -mr-2">
            <X size={18} />
          </button>
        </div>

        <div className="px-7 py-6 space-y-6">
          <div>
            <label htmlFor="api-base-url" className="label">
              FastAPI base URL
            </label>
            <div className="flex gap-2">
              <input
                id="api-base-url"
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="input flex-1 font-mono text-[13px]"
              />
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={isTesting || !url.trim()}
                className="btn btn-secondary"
              >
                {isTesting ? <RefreshCw size={14} className="animate-spin" /> : <Server size={14} />}
                Test
              </button>
            </div>
            <p className="hint">Default: http://localhost:8000 (from VITE_API_BASE_URL)</p>
          </div>

          {testResult && (
            <div
              role="status"
              className={`p-4 rounded-lg border text-[13px] flex items-start gap-3 ${
                testResult.ok
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : 'bg-rose-50 border-rose-200 text-rose-900'
              }`}
            >
              {testResult.ok ? (
                <CheckCircle2 size={16} className="text-emerald-700 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle size={16} className="text-rose-700 shrink-0 mt-0.5" />
              )}
              <div className="leading-relaxed">{testResult.message}</div>
            </div>
          )}

          {/* Local simulator toggle */}
          <label className="flex items-start justify-between gap-4 p-4 bg-subtle border border-line rounded-xl cursor-pointer">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
                <Cpu size={17} />
              </div>
              <div>
                <span className="font-medium text-ink block text-sm">Local simulation mode</span>
                <p className="text-[13px] text-muted leading-relaxed mt-1">
                  Use deterministic sample data with full task replanning and report verification.
                  This also applies automatically when the FastAPI backend is offline.
                </p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={useSimulator}
              onChange={(e) => setUseSimulator(e.target.checked)}
              className="mt-1 h-4 w-4 shrink-0 rounded border-line-strong accent-brand-600 cursor-pointer"
            />
          </label>
        </div>

        <div className="flex items-center justify-end gap-3 px-7 py-5 bg-subtle border-t border-line rounded-b-2xl">
          <button type="button" onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button type="button" onClick={handleSave} className="btn btn-primary">
            Save settings
          </button>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  details?: string | null;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  details,
  onRetry,
}) => {
  return (
    <div
      role="alert"
      className="p-6 border border-rose-200 bg-rose-50 rounded-xl"
    >
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
          <AlertTriangle size={18} />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-rose-900">{title}</h4>
          <p className="text-sm text-rose-800 mt-1 leading-relaxed">{message}</p>
          {details && (
            <pre className="mt-3 text-xs font-mono bg-white p-3 rounded-lg border border-rose-200 text-rose-800 overflow-x-auto whitespace-pre-wrap">
              {details}
            </pre>
          )}
          {onRetry && (
            <button onClick={onRetry} className="btn btn-sm btn-secondary mt-4">
              <RefreshCw size={13} />
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

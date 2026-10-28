import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subtext?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading data…',
  subtext,
}) => {
  return (
    <div
      className="flex flex-col items-center justify-center py-24 text-center"
      role="status"
    >
      <Loader2 size={28} className="animate-spin text-brand-600 mb-4" />
      <span className="text-sm font-medium text-ink">{message}</span>
      {subtext && <span className="text-[13px] text-muted mt-1">{subtext}</span>}
    </div>
  );
};

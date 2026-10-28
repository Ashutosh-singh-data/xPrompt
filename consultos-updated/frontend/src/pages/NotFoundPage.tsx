import React from 'react';
import { ArrowLeft, Search } from 'lucide-react';

interface NotFoundPageProps {
  onBackToDashboard: () => void;
  investigationId?: string;
}

export const NotFoundPage: React.FC<NotFoundPageProps> = ({
  onBackToDashboard,
  investigationId,
}) => {
  return (
    <div className="card flex flex-col items-center justify-center px-10 py-14 text-center max-w-md mx-auto my-12">
      <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center text-brand-600 mb-5">
        <Search size={22} />
      </div>
      <h2 className="text-lg font-semibold text-ink mb-2">Investigation not found</h2>
      <p className="text-sm text-muted mb-8 leading-relaxed">
        {investigationId
          ? `We couldn’t find an investigation with the ID “${investigationId}” in the backend database.`
          : 'The page or record you’re looking for doesn’t exist.'}
      </p>
      <button onClick={onBackToDashboard} className="btn btn-primary">
        <ArrowLeft size={15} />
        Back to dashboard
      </button>
    </div>
  );
};

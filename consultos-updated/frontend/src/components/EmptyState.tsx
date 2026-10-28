import React from 'react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center px-8 py-14 text-center border border-dashed border-line-strong rounded-xl bg-surface">
      <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center text-brand-600 mb-5">
        <Icon size={22} />
      </div>
      <h3 className="text-base font-semibold text-ink mb-2">{title}</h3>
      <p className="text-sm text-muted max-w-md leading-relaxed">{description}</p>
      {action && (
        <button onClick={action.onClick} className="btn btn-primary mt-6">
          {action.label}
        </button>
      )}
    </div>
  );
};

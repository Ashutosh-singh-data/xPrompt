import React from 'react';

interface SectionHeaderProps {
  title: string;
  count?: number;
  icon?: React.ReactNode;
  description?: string;
  action?: React.ReactNode;
}

/** Consistent heading used above every content block. */
export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  count,
  icon,
  description,
  action,
}) => {
  return (
    <div className="flex items-start justify-between gap-4 mb-5">
      <div className="min-w-0">
        <h3 className="text-base font-semibold text-ink flex items-center gap-2">
          {icon && <span className="text-brand-600 shrink-0">{icon}</span>}
          <span>{title}</span>
          {count !== undefined && (
            <span className="text-xs font-medium text-muted bg-slate-100 rounded-full px-2 py-0.5 tabular-nums">
              {count}
            </span>
          )}
        </h3>
        {description && <p className="text-[13px] text-muted mt-1">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
};

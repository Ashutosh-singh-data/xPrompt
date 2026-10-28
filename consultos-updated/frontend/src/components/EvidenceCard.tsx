import React from 'react';
import { Evidence } from '../types';
import { Database, FileText, Calculator, Table, ChevronRight } from 'lucide-react';

interface EvidenceCardProps {
  evidence: Evidence;
  isSelected?: boolean;
  onSelect?: (evidence: Evidence) => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  isSelected = false,
  onSelect,
}) => {
  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onClick={() => onSelect?.(evidence)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect?.(evidence);
        }
      }}
      className={`p-5 rounded-xl border text-left transition-all cursor-pointer ${
        isSelected
          ? 'bg-brand-50/60 border-brand-600 ring-2 ring-brand-600/15'
          : 'bg-surface border-line shadow-card hover:border-line-strong hover:shadow-raised'
      }`}
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-[13px] font-medium text-brand-700">{evidence.id}</span>
          <span className="inline-flex items-center gap-1.5 text-xs text-muted bg-slate-100 px-2 py-0.5 rounded-md">
            <Database size={12} className="text-faint" />
            {evidence.source_type}
          </span>
        </div>
        <ChevronRight size={16} className="text-faint shrink-0" />
      </div>

      <p className="text-sm font-medium text-ink leading-relaxed mb-4">{evidence.finding}</p>

      <div className="space-y-2 text-xs font-mono text-muted bg-subtle p-3 rounded-lg border border-line mb-4">
        <div className="flex items-start gap-2">
          <FileText size={13} className="text-faint mt-0.5 shrink-0" />
          <span className="truncate text-body" title={evidence.source_reference}>
            {evidence.source_reference}
          </span>
        </div>

        {evidence.calculation && (
          <div className="flex items-start gap-2">
            <Calculator size={13} className="text-brand-600 mt-0.5 shrink-0" />
            <span className="truncate text-brand-700" title={evidence.calculation}>
              {evidence.calculation}
            </span>
          </div>
        )}

        {evidence.relevant_columns && evidence.relevant_columns.length > 0 && (
          <div className="flex items-center gap-2">
            <Table size={13} className="text-faint shrink-0" />
            <span className="truncate">Columns: {evidence.relevant_columns.join(', ')}</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        <span>
          From task <span className="font-mono">{evidence.task_id}</span>
        </span>
        {evidence.units_or_period && <span>{evidence.units_or_period}</span>}
      </div>
    </div>
  );
};

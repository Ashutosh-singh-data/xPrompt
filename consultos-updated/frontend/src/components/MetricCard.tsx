import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  indicator?: 'neutral' | 'positive' | 'negative' | 'warning';
  icon?: React.ReactNode;
}

const TONES = {
  neutral: { tile: 'bg-brand-50 text-brand-600', text: 'text-muted' },
  positive: { tile: 'bg-emerald-50 text-emerald-700', text: 'text-emerald-700' },
  negative: { tile: 'bg-rose-50 text-rose-700', text: 'text-rose-700' },
  warning: { tile: 'bg-amber-50 text-amber-700', text: 'text-amber-700' },
} as const;

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  indicator = 'neutral',
  icon,
}) => {
  const tone = TONES[indicator];

  return (
    <div className="card p-4 sm:p-6 flex items-start justify-between gap-4">
      <div className="min-w-0">
        <span className="text-sm font-medium text-muted block">{label}</span>
        <span className="mt-2 block text-2xl sm:text-3xl font-semibold tracking-tight text-ink tabular-nums leading-none">
          {value}
        </span>
        {subtext && <div className={`mt-2 sm:mt-3 text-xs sm:text-[13px] ${tone.text}`}>{subtext}</div>}
      </div>
      {icon && (
        <div
          className={`hidden sm:flex w-10 h-10 rounded-lg items-center justify-center shrink-0 ${tone.tile}`}
          aria-hidden="true"
        >
          {icon}
        </div>
      )}
    </div>
  );
};

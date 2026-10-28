import React from 'react';
import {
  Clock,
  Play,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  MinusCircle,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import {
  getInvestigationStatusConfig,
  getTaskStatusConfig,
  getHypothesisStatusConfig,
} from '../utils/status';

interface StatusBadgeProps {
  type: 'investigation' | 'task' | 'hypothesis';
  status: string;
  size?: 'sm' | 'md';
  showDescription?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  type,
  status,
  size = 'md',
  showDescription = false,
}) => {
  const config =
    type === 'investigation'
      ? getInvestigationStatusConfig(status)
      : type === 'task'
      ? getTaskStatusConfig(status)
      : getHypothesisStatusConfig(status);

  const renderIcon = () => {
    const iconSize = size === 'sm' ? 12 : 14;
    switch (status) {
      case 'running':
        return <Loader2 size={iconSize} className="animate-spin" />;
      case 'replanning':
        return <RefreshCw size={iconSize} className="animate-spin" />;
      case 'completed':
      case 'supported':
        return <CheckCircle2 size={iconSize} />;
      case 'failed':
      case 'contradicted':
        return <AlertCircle size={iconSize} />;
      case 'blocked':
        return <ShieldAlert size={iconSize} />;
      case 'cancelled':
      case 'skipped':
        return <MinusCircle size={iconSize} />;
      case 'ready':
        return <Play size={iconSize} />;
      case 'pending':
      case 'draft':
      case 'queued':
      default:
        return <Clock size={iconSize} />;
    }
  };

  const isSmall = size === 'sm';

  return (
    <div className="inline-flex flex-col">
      <div
        className={`inline-flex items-center gap-1.5 font-medium border rounded-full whitespace-nowrap ${
          isSmall ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-[13px]'
        } ${config.bgClass} ${config.textClass} ${config.borderClass}`}
        role="status"
        aria-label={`${type} status: ${config.label}`}
      >
        <span className="shrink-0" aria-hidden="true">
          {renderIcon()}
        </span>
        <span>{config.label}</span>
      </div>
      {showDescription && config.description && (
        <span className="text-xs text-muted mt-1.5">{config.description}</span>
      )}
    </div>
  );
};

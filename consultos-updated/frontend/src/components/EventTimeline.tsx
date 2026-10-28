import React from 'react';
import { InvestigationEvent } from '../types';
import { formatTimeRelative } from '../utils/formatters';
import {
  GitBranch,
  Play,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  RefreshCw,
  Clock,
  Radio,
} from 'lucide-react';

interface EventTimelineProps {
  events: InvestigationEvent[];
  isStreaming?: boolean;
}

const humanize = (type: string) => {
  const t = type.replace(/_/g, ' ');
  return t.charAt(0).toUpperCase() + t.slice(1);
};

export const EventTimeline: React.FC<EventTimelineProps> = ({
  events,
  isStreaming = false,
}) => {
  if (events.length === 0) {
    return (
      <div className="px-4 py-8 text-center text-muted text-sm">
        No execution events recorded yet.
      </div>
    );
  }

  // Newest event first
  const sortedEvents = [...events].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'plan_created':
        return <GitBranch size={13} className="text-brand-600" />;
      case 'replanning_triggered':
      case 'plan_revised':
        return <RefreshCw size={13} className="text-amber-700" />;
      case 'task_started':
        return <Play size={13} className="text-sky-700" />;
      case 'task_completed':
        return <CheckCircle2 size={13} className="text-emerald-700" />;
      case 'task_failed':
        return <AlertCircle size={13} className="text-rose-700" />;
      case 'evidence_recorded':
        return <FileCheck size={13} className="text-teal-700" />;
      case 'report_generated':
        return <CheckCircle2 size={13} className="text-brand-600" />;
      default:
        return <Clock size={13} className="text-muted" />;
    }
  };

  return (
    <div className="space-y-4">
      {isStreaming && (
        <div className="flex items-center justify-between text-[13px] text-brand-700 bg-brand-50 border border-brand-100 px-3.5 py-2.5 rounded-lg">
          <span className="flex items-center gap-2 font-medium">
            <Radio size={14} className="animate-pulse" />
            Live updates on
          </span>
          <span className="text-xs text-muted tabular-nums">{events.length} events</span>
        </div>
      )}

      <ol className="relative space-y-5 pl-8 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-px before:bg-line-strong">
        {sortedEvents.map((evt) => {
          const isReplan = evt.event_type === 'replanning_triggered';
          const detailsString =
            typeof evt.details === 'string' ? evt.details : JSON.stringify(evt.details, null, 1);

          return (
            <li key={evt.id} className="relative">
              <div
                className={`absolute -left-8 top-3 w-6 h-6 rounded-full flex items-center justify-center border bg-surface ${
                  isReplan ? 'border-amber-400' : 'border-line-strong'
                }`}
              >
                {getEventIcon(evt.event_type)}
              </div>

              <div
                className={`px-4 py-3 rounded-lg border text-[13px] ${
                  isReplan ? 'bg-amber-50 border-amber-200' : 'bg-subtle border-line'
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-1">
                  <span
                    className={`font-medium ${isReplan ? 'text-amber-900' : 'text-ink'}`}
                  >
                    {humanize(evt.event_type)}
                  </span>
                  <span className="text-xs text-muted shrink-0">
                    {formatTimeRelative(evt.created_at)}
                  </span>
                </div>

                {evt.task_id && (
                  <div className="text-xs text-muted mb-1.5">
                    Task <span className="font-mono text-body">{evt.task_id}</span>
                  </div>
                )}

                {typeof evt.details === 'object' && evt.details ? (
                  <div className="text-[13px] text-body space-y-1 leading-relaxed">
                    {evt.details.reason && (
                      <div className="text-amber-900 font-medium">{evt.details.reason}</div>
                    )}
                    {evt.details.finding_summary && (
                      <div className="text-teal-800">{evt.details.finding_summary}</div>
                    )}
                    {evt.details.strategy && <div className="text-muted">{evt.details.strategy}</div>}
                    {evt.details.added_tasks && (
                      <div className="text-xs font-mono text-amber-800 pt-1">
                        Added: {evt.details.added_tasks.join(', ')}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-muted font-mono break-words">{detailsString}</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
};

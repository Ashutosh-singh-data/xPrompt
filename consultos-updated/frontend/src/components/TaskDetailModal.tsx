import React, { useEffect } from 'react';
import { Task } from '../types';
import { StatusBadge } from './StatusBadge';
import { formatDuration, formatTimestamp } from '../utils/formatters';
import { X, GitBranch, RefreshCw, AlertCircle } from 'lucide-react';

interface TaskDetailModalProps {
  task: Task | null;
  onClose: () => void;
  onRetry?: (taskId: string) => void;
  onNavigateToEvidence?: (evidenceId: string) => void;
}

export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  task,
  onClose,
  onRetry,
}) => {
  useEffect(() => {
    if (!task) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [task, onClose]);

  if (!task) return null;

  const isReplan = task.is_replan_addition || (task.plan_version && task.plan_version > 1);
  const isFailed = task.status === 'failed';

  return (
    <div
      className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="task-detail-title"
      onClick={onClose}
    >
      <div
        className="modal-panel bg-surface rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-pop"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-7 pt-6 pb-5 border-b border-line flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <span className="id-chip">{task.id}</span>
              <span className="text-[13px] text-brand-700 font-medium">{task.task_type}</span>
              {isReplan && (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                  <GitBranch size={11} />
                  Added in plan revision {task.plan_version || 2}
                </span>
              )}
            </div>
            <h3 id="task-detail-title" className="text-lg font-semibold text-ink leading-snug">
              {task.title}
            </h3>
          </div>
          <button onClick={onClose} aria-label="Close task detail" className="icon-btn -mr-2 -mt-1">
            <X size={18} />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="px-7 py-6 overflow-y-auto space-y-6">
          {/* Status + timing */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-5 bg-subtle p-5 rounded-xl border border-line">
            <div>
              <span className="meta-label">Status</span>
              <StatusBadge type="task" status={task.status} size="sm" />
            </div>
            <div>
              <span className="meta-label">Duration</span>
              <span className="text-sm text-ink font-medium tabular-nums">
                {formatDuration(task.duration)}
              </span>
            </div>
            <div>
              <span className="meta-label">Attempts</span>
              <span className="text-sm text-ink font-medium tabular-nums">{task.attempts}</span>
            </div>
            <div>
              <span className="meta-label">Last updated</span>
              <span className="text-[13px] text-body block">{formatTimestamp(task.updated_at)}</span>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-ink mb-2">Objective & method</h4>
            <p className="text-sm text-body leading-relaxed">{task.description}</p>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-ink mb-2">Depends on</h4>
            {task.dependencies && task.dependencies.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {task.dependencies.map((dep) => (
                  <span key={dep} className="id-chip">
                    {dep}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted">None. This is a root task.</p>
            )}
          </div>

          {isFailed && task.error && (
            <div className="border border-rose-200 bg-rose-50 p-4 rounded-xl">
              <div className="flex items-center gap-2 text-rose-900 font-medium text-sm mb-2">
                <AlertCircle size={16} />
                <span>Task failed</span>
              </div>
              <pre className="text-xs font-mono text-rose-800 whitespace-pre-wrap break-all leading-relaxed">
                {task.error}
              </pre>
            </div>
          )}

          {task.result && (
            <div>
              <h4 className="text-sm font-semibold text-ink mb-2">Output</h4>
              <pre className="code-block max-h-64">
                {typeof task.result === 'string' ? task.result : JSON.stringify(task.result, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-7 py-5 border-t border-line flex items-center justify-between gap-3 bg-subtle rounded-b-2xl">
          <span className="text-[13px] text-muted">Plan version {task.plan_version || 1}</span>
          <div className="flex items-center gap-3">
            {isFailed && onRetry && (
              <button onClick={() => onRetry(task.id)} className="btn btn-danger">
                <RefreshCw size={14} />
                Retry task
              </button>
            )}
            <button onClick={onClose} className="btn btn-secondary">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

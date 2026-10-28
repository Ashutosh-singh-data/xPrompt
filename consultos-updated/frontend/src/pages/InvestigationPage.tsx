import React, { useState } from 'react';
import { useInvestigation } from '../hooks/useInvestigation';
import { Task, Evidence } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { SectionHeader } from '../components/SectionHeader';
import { TaskGraph } from '../components/TaskGraph';
import { TaskList } from '../components/TaskList';
import { HypothesisPanel } from '../components/HypothesisPanel';
import { EventTimeline } from '../components/EventTimeline';
import { TaskDetailModal } from '../components/TaskDetailModal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { formatTimestamp } from '../utils/formatters';
import {
  Play,
  XCircle,
  RefreshCw,
  GitBranch,
  Layers,
  FileText,
  Network,
  List,
  Activity,
  Lightbulb,
  Radio,
  Database,
} from 'lucide-react';

interface InvestigationPageProps {
  investigationId: string;
  onNavigateToEvidence: (investigationId: string, evidenceId?: string) => void;
  onNavigateToReport: (investigationId: string) => void;
}

export const InvestigationPage: React.FC<InvestigationPageProps> = ({
  investigationId,
  onNavigateToEvidence,
  onNavigateToReport,
}) => {
  const {
    investigation,
    tasks,
    evidence,
    hypotheses,
    events,
    report,
    isLoading,
    error,
    isExecutingAction,
    streamStatus,
    refresh,
    runInvestigation,
    cancelInvestigation,
    retryTask,
  } = useInvestigation(investigationId);

  const [activeViewMode, setActiveViewMode] = useState<'graph' | 'table'>('graph');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isCancelConfirmOpen, setIsCancelConfirmOpen] = useState<boolean>(false);

  if (isLoading && !investigation) {
    return <LoadingState message="Loading investigation workspace…" />;
  }

  if (error && !investigation) {
    return (
      <ErrorState
        title="Couldn’t load this investigation"
        message={error}
        onRetry={refresh}
      />
    );
  }

  if (!investigation) {
    return (
      <div className="px-8 py-14 text-center text-muted border border-dashed border-line-strong rounded-xl bg-surface">
        Investigation not found.
      </div>
    );
  }

  const isRunning = investigation.status === 'running' || investigation.status === 'replanning';
  const isDraft = investigation.status === 'draft' || investigation.status === 'queued';
  const isCompleted = investigation.status === 'completed';

  const completedCount = tasks.filter((t) => t.status === 'completed').length;
  const progressPercent = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;

  return (
    <div className="space-y-10">
      {/* Workspace header */}
      <div className="card">
        <div className="p-7 flex flex-col xl:flex-row xl:items-start justify-between gap-6">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3 flex-wrap mb-4">
              <StatusBadge type="investigation" status={investigation.status} size="sm" />
              <span className="id-chip">Plan v{investigation.current_plan_version}</span>
              <span className="id-chip max-w-[220px] truncate" title={investigation.id}>
                {investigation.id}
              </span>
              <span className="text-[13px] text-muted">
                Created {formatTimestamp(investigation.created_at)}
              </span>
            </div>

            <h2 className="text-xl font-semibold text-ink leading-snug tracking-tight">
              {investigation.business_question}
            </h2>

            {investigation.dataset_filename && (
              <div className="flex items-center gap-2 text-[13px] text-muted mt-4">
                <Database size={14} className="text-brand-600" />
                <span className="font-mono text-xs">{investigation.dataset_filename}</span>
                {investigation.dataset_rows_count && (
                  <span className="tabular-nums">
                    · {investigation.dataset_rows_count.toLocaleString()} rows
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Primary actions */}
          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            {isDraft && (
              <button
                onClick={runInvestigation}
                disabled={isExecutingAction}
                className="btn btn-primary"
              >
                <Play size={15} />
                <span>Start analysis</span>
              </button>
            )}

            {isRunning && (
              <button
                onClick={() => setIsCancelConfirmOpen(true)}
                disabled={isExecutingAction}
                className="btn btn-danger-soft"
              >
                <XCircle size={15} />
                <span>Cancel run</span>
              </button>
            )}

            {isCompleted && (
              <button
                onClick={() => onNavigateToReport(investigation.id)}
                className="btn btn-success"
              >
                <FileText size={15} />
                <span>View report</span>
              </button>
            )}

            <button
              onClick={() => onNavigateToEvidence(investigation.id)}
              className="btn btn-secondary"
            >
              <Layers size={15} />
              <span>Evidence ({evidence.length})</span>
            </button>
          </div>
        </div>

        {/* Progress + stream status */}
        <div className="px-7 py-5 border-t border-line bg-subtle rounded-b-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-1 max-w-xl">
            <span className="text-[13px] text-body font-medium tabular-nums whitespace-nowrap">
              {completedCount} of {tasks.length} tasks complete
            </span>
            <div
              className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden"
              role="progressbar"
              aria-valuenow={progressPercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Task progress"
            >
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  investigation.status === 'replanning'
                    ? 'bg-amber-500'
                    : isCompleted
                    ? 'bg-emerald-600'
                    : 'bg-brand-600'
                }`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span className="text-[13px] text-muted tabular-nums w-10">{progressPercent}%</span>
          </div>

          <div className="flex items-center gap-2 text-[13px]">
            {streamStatus === 'connected' ? (
              <span className="flex items-center gap-2 text-emerald-700 font-medium">
                <Radio size={14} className="animate-pulse" />
                Live updates on
              </span>
            ) : streamStatus === 'reconnecting' ? (
              <span className="flex items-center gap-2 text-amber-700 font-medium">
                <RefreshCw size={14} className="animate-spin" />
                Reconnecting…
              </span>
            ) : (
              <span className="text-muted">Updates on refresh</span>
            )}
          </div>
        </div>
      </div>

      {/* Task pipeline (full width so every phase is visible) */}
      <section className="min-w-0">
          <SectionHeader
            title="Analysis pipeline"
            description="Tasks run in phases; each phase unlocks once the previous one finishes."
            action={
              <div className="inline-flex rounded-lg bg-slate-100 p-1">
                <button
                  type="button"
                  onClick={() => setActiveViewMode('graph')}
                  aria-pressed={activeViewMode === 'graph'}
                  className={`inline-flex items-center gap-2 px-3 h-8 text-[13px] font-medium rounded-md transition-colors ${
                    activeViewMode === 'graph'
                      ? 'bg-surface text-ink shadow-card'
                      : 'text-muted hover:text-ink'
                  }`}
                >
                  <Network size={14} />
                  <span>Graph</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveViewMode('table')}
                  aria-pressed={activeViewMode === 'table'}
                  className={`inline-flex items-center gap-2 px-3 h-8 text-[13px] font-medium rounded-md transition-colors ${
                    activeViewMode === 'table'
                      ? 'bg-surface text-ink shadow-card'
                      : 'text-muted hover:text-ink'
                  }`}
                >
                  <List size={14} />
                  <span>List</span>
                </button>
              </div>
            }
          />

          {investigation.current_plan_version > 1 && (
            <div className="mb-5 inline-flex items-center gap-2 text-[13px] font-medium text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-full">
              <GitBranch size={13} />
              Plan revised to v{investigation.current_plan_version} after new evidence
            </div>
          )}

          {activeViewMode === 'graph' ? (
            <TaskGraph
              tasks={tasks}
              onSelectTask={setSelectedTask}
              onRetryTask={retryTask}
              selectedTaskId={selectedTask?.id}
            />
          ) : (
            <TaskList
              tasks={tasks}
              onSelectTask={setSelectedTask}
              onRetryTask={retryTask}
              selectedTaskId={selectedTask?.id}
            />
          )}

          {tasks.some((t) => t.status === 'failed') && (
            <div
              role="alert"
              className="mt-5 p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-sm leading-relaxed"
            >
              <span className="font-semibold block mb-0.5">Some tasks failed</span>
              Completed tasks and their evidence are preserved. Open a failed task to inspect the
              error, then retry it.
            </div>
          )}
      </section>

      {/* Hypotheses + events */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 items-start">
          <section className="min-w-0">
            <SectionHeader
              title="Working hypotheses"
              count={hypotheses.length}
              icon={<Lightbulb size={17} />}
            />
            <HypothesisPanel
              hypotheses={hypotheses}
              onSelectEvidence={(evId) => onNavigateToEvidence(investigation.id, evId)}
            />
          </section>

          <section className="min-w-0">
            <SectionHeader
              title="Event timeline"
              icon={<Activity size={17} />}
            />
            <div className="card p-5 max-h-[520px] overflow-y-auto">
              <EventTimeline events={events} isStreaming={streamStatus === 'connected'} />
            </div>
          </section>
      </div>

      <TaskDetailModal
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
        onRetry={retryTask}
      />

      <ConfirmDialog
        isOpen={isCancelConfirmOpen}
        title="Cancel this investigation?"
        message="This stops all running workers and aborts pending tasks. Evidence already collected is kept in its current partial state."
        confirmLabel="Cancel investigation"
        cancelLabel="Keep running"
        isDestructive
        onConfirm={async () => {
          setIsCancelConfirmOpen(false);
          await cancelInvestigation();
        }}
        onCancel={() => setIsCancelConfirmOpen(false)}
      />
    </div>
  );
};

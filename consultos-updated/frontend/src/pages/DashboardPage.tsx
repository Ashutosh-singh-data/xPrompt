import React, { useState, useEffect, useCallback } from 'react';
import { investigationsService } from '../services/investigations';
import { Investigation, InvestigationEvent } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { EventTimeline } from '../components/EventTimeline';
import { SectionHeader } from '../components/SectionHeader';
import { formatTimeRelative } from '../utils/formatters';
import {
  FileText,
  PlusCircle,
  PlayCircle,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  Layers,
  Activity,
} from 'lucide-react';

interface DashboardPageProps {
  onNavigateToNew: () => void;
  onOpenInvestigation: (id: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigateToNew,
  onOpenInvestigation,
}) => {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [recentEvents, setRecentEvents] = useState<InvestigationEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const invs = await investigationsService.listInvestigations();
      setInvestigations(invs);

      // If we have an active or recent investigation, pull recent events for the feed
      if (invs.length > 0) {
        try {
          const events = await investigationsService.getEvents(invs[0].id);
          setRecentEvents(events.slice(0, 8));
        } catch {
          setRecentEvents([]);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard investigations from API.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Derived counts from backend data
  const totalCount = investigations.length;
  const runningCount = investigations.filter(
    (i) => i.status === 'running' || i.status === 'replanning'
  ).length;
  const completedCount = investigations.filter((i) => i.status === 'completed').length;
  const failedCount = investigations.filter((i) => i.status === 'failed').length;

  if (isLoading) {
    return <LoadingState message="Loading investigations…" />;
  }

  if (error && investigations.length === 0) {
    return (
      <ErrorState
        title="Couldn’t load investigations"
        message={error}
        onRetry={loadData}
      />
    );
  }

  return (
    <div className="space-y-10">
      {/* Intro + primary action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5">
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold text-ink tracking-tight">
            Business investigation hub
          </h2>
          <p className="text-sm text-muted mt-2 leading-relaxed">
            Ask a diagnostic question, let ConsultOS run the analysis with replanning, and review
            findings backed by verified evidence.
          </p>
        </div>
        <button onClick={onNavigateToNew} className="btn btn-primary shrink-0">
          <PlusCircle size={16} />
          New investigation
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-5">
        <MetricCard
          label="Total investigations"
          value={totalCount}
          subtext="Stored in database"
          icon={<Layers size={19} />}
        />
        <MetricCard
          label="Running now"
          value={runningCount}
          subtext={runningCount > 0 ? 'Analysis in progress' : 'No active workers'}
          indicator={runningCount > 0 ? 'warning' : 'neutral'}
          icon={<PlayCircle size={19} />}
        />
        <MetricCard
          label="Completed"
          value={completedCount}
          subtext="Final report available"
          indicator="positive"
          icon={<CheckCircle2 size={19} />}
        />
        <MetricCard
          label="Failed"
          value={failedCount}
          subtext={failedCount > 0 ? 'Needs attention' : 'No unrecovered failures'}
          indicator={failedCount > 0 ? 'negative' : 'neutral'}
          icon={<AlertTriangle size={19} />}
        />
      </div>

      {/* Investigations + activity */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <section className="xl:col-span-2" aria-labelledby="recent-investigations">
          <SectionHeader title="Recent investigations" count={investigations.length} />

          {investigations.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No investigations yet"
              description="Create your first business question and attach a CSV dataset to start an autonomous analysis."
              action={{
                label: 'Create investigation',
                onClick: onNavigateToNew,
              }}
            />
          ) : (
            <div className="space-y-4">
              {investigations.map((inv) => {
                const progressPct =
                  inv.tasks_count && inv.tasks_count > 0 && inv.completed_tasks_count !== undefined
                    ? Math.round((inv.completed_tasks_count / inv.tasks_count) * 100)
                    : null;

                return (
                  <div
                    key={inv.id}
                    role="link"
                    tabIndex={0}
                    onClick={() => onOpenInvestigation(inv.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') onOpenInvestigation(inv.id);
                    }}
                    className="card card-interactive p-6 group"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-3 mb-3 flex-wrap">
                          <StatusBadge type="investigation" status={inv.status} size="sm" />
                          <span className="text-xs text-muted">
                            Plan v{inv.current_plan_version}
                          </span>
                          <span className="text-xs text-muted">
                            {formatTimeRelative(inv.created_at)}
                          </span>
                        </div>
                        <h4 className="text-[15px] font-semibold text-ink leading-snug group-hover:text-brand-700 transition-colors line-clamp-2">
                          {inv.business_question}
                        </h4>
                      </div>
                      <span className="hidden sm:inline-flex items-center gap-1.5 text-[13px] font-medium text-brand-600 shrink-0 pt-0.5">
                        Open
                        <ArrowRight
                          size={14}
                          className="transition-transform group-hover:translate-x-0.5"
                        />
                      </span>
                    </div>

                    {(inv.dataset_filename || progressPct !== null) && (
                      <div className="mt-5 pt-5 border-t border-line flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-[13px] text-muted">
                        <div className="flex items-center gap-2 min-w-0">
                          {inv.dataset_filename && (
                            <>
                              <Database size={14} className="text-faint shrink-0" />
                              <span className="font-mono text-xs truncate">{inv.dataset_filename}</span>
                            </>
                          )}
                          {inv.dataset_rows_count && (
                            <span className="tabular-nums shrink-0">
                              · {inv.dataset_rows_count.toLocaleString()} rows
                            </span>
                          )}
                        </div>

                        {progressPct !== null && (
                          <div className="flex items-center gap-3 sm:w-56">
                            <div
                              className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden"
                              role="progressbar"
                              aria-valuenow={progressPct}
                              aria-valuemin={0}
                              aria-valuemax={100}
                              aria-label="Task progress"
                            >
                              <div
                                className={`h-full rounded-full ${
                                  inv.status === 'completed' ? 'bg-emerald-600' : 'bg-brand-600'
                                }`}
                                style={{ width: `${progressPct}%` }}
                              />
                            </div>
                            <span className="text-xs tabular-nums text-body font-medium w-24 text-right">
                              {inv.completed_tasks_count}/{inv.tasks_count} tasks
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section aria-labelledby="latest-events">
          <SectionHeader
            title="Latest activity"
            icon={<Activity size={17} />}
            description="Most recent events from your latest investigation"
          />
          <div className="card p-5">
            <EventTimeline events={recentEvents} />
          </div>
        </section>
      </div>
    </div>
  );
};

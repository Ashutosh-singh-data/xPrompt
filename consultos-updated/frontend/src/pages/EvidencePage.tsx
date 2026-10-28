import React, { useState, useEffect, useMemo } from 'react';
import { investigationsService } from '../services/investigations';
import { Evidence, Investigation } from '../types';
import { EvidenceCard } from '../components/EvidenceCard';
import { EmptyState } from '../components/EmptyState';
import { LoadingState } from '../components/LoadingState';
import { formatTimestamp } from '../utils/formatters';
import { Layers, Search, Database } from 'lucide-react';

interface EvidencePageProps {
  investigationId: string;
  initialSelectedEvidenceId?: string | null;
  onNavigateToInvestigation: (id: string) => void;
  onNavigateToReport: (id: string) => void;
}

export const EvidencePage: React.FC<EvidencePageProps> = ({
  investigationId,
  initialSelectedEvidenceId,
  onNavigateToInvestigation,
  onNavigateToReport,
}) => {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sourceFilter, setSourceFilter] = useState<string>('all');

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setIsLoading(true);
      try {
        const [evs, inv] = await Promise.all([
          investigationsService.getEvidence(investigationId),
          investigationsService.getInvestigation(investigationId).catch(() => null),
        ]);
        if (!isMounted) return;
        setEvidenceList(evs);
        setInvestigation(inv);

        if (initialSelectedEvidenceId) {
          const match = evs.find((e) => e.id === initialSelectedEvidenceId);
          if (match) setSelectedEvidence(match);
          else if (evs.length > 0) setSelectedEvidence(evs[0]);
        } else if (evs.length > 0) {
          setSelectedEvidence(evs[0]);
        }
      } catch (err) {
        console.error('Failed to load evidence', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [investigationId, initialSelectedEvidenceId]);

  const [taskFilter, setTaskFilter] = useState<string>('all');

  // Unique sources & producing tasks for filter controls
  const availableSources = useMemo(() => {
    const set = new Set<string>();
    evidenceList.forEach((e) => {
      if (e.source_type) set.add(e.source_type);
    });
    return Array.from(set);
  }, [evidenceList]);

  const availableTasks = useMemo(() => {
    const set = new Set<string>();
    evidenceList.forEach((e) => {
      if (e.task_id) set.add(e.task_id);
    });
    return Array.from(set);
  }, [evidenceList]);

  // Filtered evidence items
  const filteredEvidence = useMemo(() => {
    return evidenceList.filter((e) => {
      const matchesSearch =
        searchQuery.trim() === '' ||
        e.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.finding.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.source_reference.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.task_id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesSource =
        sourceFilter === 'all' || e.source_type.toLowerCase() === sourceFilter.toLowerCase();

      const matchesTask =
        taskFilter === 'all' || e.task_id.toLowerCase() === taskFilter.toLowerCase();

      return matchesSearch && matchesSource && matchesTask;
    });
  }, [evidenceList, searchQuery, sourceFilter, taskFilter]);

  if (isLoading) {
    return <LoadingState message="Loading evidence records…" />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="card p-7 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="min-w-0">
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <span className="id-chip">{investigationId}</span>
            <span className="text-[13px] text-muted">
              {evidenceList.length} verified {evidenceList.length === 1 ? 'record' : 'records'}
            </span>
          </div>
          <h2 className="text-xl font-semibold text-ink leading-snug tracking-tight">
            {investigation ? investigation.business_question : 'Evidence explorer'}
          </h2>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => onNavigateToInvestigation(investigationId)}
            className="btn btn-secondary"
          >
            Workspace
          </button>
          <button onClick={() => onNavigateToReport(investigationId)} className="btn btn-primary">
            Final report
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-5 space-y-4">
        <div className="relative">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-faint" />
          <input
            type="text"
            aria-label="Search evidence"
            placeholder="Search by ID, finding, source or task…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10"
          />
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          {availableTasks.length > 0 && (
            <div className="flex items-center gap-2.5">
              <label htmlFor="task-filter" className="text-[13px] font-medium text-muted">
                Task
              </label>
              <select
                id="task-filter"
                value={taskFilter}
                onChange={(e) => setTaskFilter(e.target.value)}
                className="input h-9 py-0 w-auto font-mono text-[13px]"
              >
                <option value="all">All tasks ({evidenceList.length})</option>
                {availableTasks.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div
            className="flex flex-wrap items-center gap-2"
            role="group"
            aria-label="Filter by source"
          >
            <span className="text-[13px] font-medium text-muted mr-1">Source</span>
            <button
              type="button"
              onClick={() => setSourceFilter('all')}
              aria-pressed={sourceFilter === 'all'}
              className={`h-8 px-3.5 text-[13px] font-medium rounded-full transition-colors ${
                sourceFilter === 'all'
                  ? 'bg-brand-600 text-white'
                  : 'text-body bg-slate-100 hover:bg-slate-200'
              }`}
            >
              All
            </button>
            {availableSources.map((source) => (
              <button
                type="button"
                key={source}
                onClick={() => setSourceFilter(source)}
                aria-pressed={sourceFilter === source}
                className={`h-8 px-3.5 text-[13px] font-medium rounded-full transition-colors ${
                  sourceFilter === source
                    ? 'bg-brand-600 text-white'
                    : 'text-body bg-slate-100 hover:bg-slate-200'
                }`}
              >
                {source}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Split view */}
      {evidenceList.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No evidence yet"
          description="Evidence is recorded as analytical tasks finish. Check back once the investigation has run."
          action={{
            label: 'Go to workspace',
            onClick: () => onNavigateToInvestigation(investigationId),
          }}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* List */}
          <div className="lg:col-span-5 space-y-4 lg:max-h-[calc(100vh-15rem)] lg:overflow-y-auto lg:pr-2 lg:-mr-2">
            {filteredEvidence.length === 0 ? (
              <div className="px-6 py-10 text-center text-muted border border-dashed border-line-strong rounded-xl bg-surface text-sm">
                No evidence matches your search.
              </div>
            ) : (
              filteredEvidence.map((ev) => (
                <EvidenceCard
                  key={ev.id}
                  evidence={ev}
                  isSelected={selectedEvidence?.id === ev.id}
                  onSelect={setSelectedEvidence}
                />
              ))
            )}
          </div>

          {/* Detail */}
          <div className="lg:col-span-7 min-w-0">
            {selectedEvidence ? (
              <div className="card p-7 space-y-7 lg:sticky lg:top-24">
                <div className="pb-5 border-b border-line">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <span className="font-mono text-base font-semibold text-brand-700">
                      {selectedEvidence.id}
                    </span>
                    <span className="inline-flex items-center gap-1.5 text-xs text-muted bg-slate-100 px-2 py-0.5 rounded-md">
                      <Database size={12} className="text-faint" />
                      {selectedEvidence.source_type}
                    </span>
                  </div>
                  <span className="text-[13px] text-muted">
                    Recorded {formatTimestamp(selectedEvidence.created_at)}
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-ink mb-3">Finding</h4>
                  <p className="text-[15px] font-medium text-ink leading-relaxed bg-brand-50/60 p-5 rounded-xl border border-brand-100">
                    {selectedEvidence.finding}
                  </p>
                </div>

                <div className="space-y-5 bg-subtle p-5 rounded-xl border border-line">
                  <div>
                    <span className="meta-label">Source reference</span>
                    <span className="font-mono text-[13px] text-ink break-all select-all">
                      {selectedEvidence.source_reference}
                    </span>
                  </div>

                  {selectedEvidence.calculation && (
                    <div>
                      <span className="meta-label">Calculation</span>
                      <code className="block font-mono text-[13px] text-brand-700 bg-surface p-3 rounded-lg border border-line break-words">
                        {selectedEvidence.calculation}
                      </code>
                    </div>
                  )}

                  {selectedEvidence.relevant_columns && selectedEvidence.relevant_columns.length > 0 && (
                    <div>
                      <span className="meta-label">Columns used</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {selectedEvidence.relevant_columns.map((c) => (
                          <span key={c} className="id-chip">
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedEvidence.units_or_period && (
                    <div>
                      <span className="meta-label">Period / units</span>
                      <span className="text-sm text-body">{selectedEvidence.units_or_period}</span>
                    </div>
                  )}
                </div>

                {selectedEvidence.supporting_data && (
                  <div>
                    <h4 className="text-sm font-semibold text-ink mb-3">Supporting data</h4>
                    <pre className="code-block max-h-64">
                      {JSON.stringify(selectedEvidence.supporting_data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="px-8 py-14 text-center border border-dashed border-line-strong rounded-xl text-muted text-sm bg-surface">
                Select a record to see where it came from.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

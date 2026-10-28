import React, { useState, useEffect } from 'react';
import { investigationsService } from '../services/investigations';
import { FinalReport, Investigation } from '../types';
import { ReportSection } from '../components/ReportSection';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { ArrowLeft, Layers } from 'lucide-react';

interface ReportPageProps {
  investigationId: string;
  onNavigateToInvestigation: (id: string) => void;
  onNavigateToEvidence: (id: string, evidenceId?: string) => void;
}

export const ReportPage: React.FC<ReportPageProps> = ({
  investigationId,
  onNavigateToInvestigation,
  onNavigateToEvidence,
}) => {
  const [report, setReport] = useState<FinalReport | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [rep, inv] = await Promise.all([
        investigationsService.getReport(investigationId),
        investigationsService.getInvestigation(investigationId).catch(() => null),
      ]);
      setReport(rep);
      setInvestigation(inv);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch executive report from backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [investigationId]);

  if (isLoading) {
    return <LoadingState message="Fetching executive report…" />;
  }

  if (error) {
    return (
      <ErrorState
        title="Couldn’t load the report"
        message={error}
        onRetry={loadData}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Navigation */}
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={() => onNavigateToInvestigation(investigationId)}
          className="inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink transition-colors"
        >
          <ArrowLeft size={16} />
          Back to workspace
        </button>

        <button onClick={() => onNavigateToEvidence(investigationId)} className="btn btn-secondary">
          <Layers size={15} />
          <span>View evidence</span>
        </button>
      </div>

      <ReportSection
        report={report}
        onSelectEvidence={(evId) => onNavigateToEvidence(investigationId, evId)}
      />
    </div>
  );
};

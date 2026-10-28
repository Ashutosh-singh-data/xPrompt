import React from 'react';
import { Hypothesis } from '../types';
import { StatusBadge } from './StatusBadge';
import { formatPercent } from '../utils/formatters';
import { Check, X, HelpCircle, ArrowRight } from 'lucide-react';

interface HypothesisPanelProps {
  hypotheses: Hypothesis[];
  onSelectEvidence?: (evidenceId: string) => void;
}

export const HypothesisPanel: React.FC<HypothesisPanelProps> = ({
  hypotheses,
  onSelectEvidence,
}) => {
  if (hypotheses.length === 0) {
    return (
      <div className="px-6 py-8 text-center text-muted border border-dashed border-line-strong rounded-xl bg-surface text-sm">
        No hypotheses have been formed yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {hypotheses.map((hyp) => {
        const isSupported = hyp.status === 'supported';
        const isContradicted = hyp.status === 'contradicted';

        return (
          <div
            key={hyp.id}
            className={`card p-5 border-l-4 ${
              isSupported
                ? 'border-l-emerald-600'
                : isContradicted
                ? 'border-l-rose-600'
                : 'border-l-line-strong'
            }`}
          >
            <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
              <StatusBadge type="hypothesis" status={hyp.status} size="sm" />
              <span className="text-xs text-muted tabular-nums">
                Confidence {formatPercent(hyp.confidence)}
              </span>
            </div>

            <p className="text-sm font-medium text-ink leading-relaxed">{hyp.statement}</p>

            {hyp.notes && (
              <p className="text-[13px] text-muted leading-relaxed mt-3 pl-3 border-l-2 border-line-strong">
                {hyp.notes}
              </p>
            )}

            <div className="mt-4 pt-4 border-t border-line space-y-3 text-[13px]">
              {hyp.supporting_evidence_ids && hyp.supporting_evidence_ids.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-emerald-700 flex items-center gap-1.5 font-medium">
                    <Check size={14} />
                    Supported by
                  </span>
                  {hyp.supporting_evidence_ids.map((evId) => (
                    <button
                      key={evId}
                      onClick={() => onSelectEvidence?.(evId)}
                      className="font-mono text-xs text-emerald-800 bg-emerald-50 hover:bg-emerald-100 px-2 py-0.5 rounded-md border border-emerald-200 transition-colors inline-flex items-center gap-1"
                    >
                      <span>{evId}</span>
                      <ArrowRight size={11} />
                    </button>
                  ))}
                </div>
              )}

              {hyp.contradicting_evidence_ids && hyp.contradicting_evidence_ids.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-rose-700 flex items-center gap-1.5 font-medium">
                    <X size={14} />
                    Contradicted by
                  </span>
                  {hyp.contradicting_evidence_ids.map((evId) => (
                    <button
                      key={evId}
                      onClick={() => onSelectEvidence?.(evId)}
                      className="font-mono text-xs text-rose-800 bg-rose-50 hover:bg-rose-100 px-2 py-0.5 rounded-md border border-rose-200 transition-colors inline-flex items-center gap-1"
                    >
                      <span>{evId}</span>
                      <ArrowRight size={11} />
                    </button>
                  ))}
                </div>
              )}

              {(!hyp.supporting_evidence_ids || hyp.supporting_evidence_ids.length === 0) &&
                (!hyp.contradicting_evidence_ids || hyp.contradicting_evidence_ids.length === 0) && (
                  <span className="text-muted flex items-center gap-1.5">
                    <HelpCircle size={14} />
                    Waiting for evidence to be evaluated
                  </span>
                )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

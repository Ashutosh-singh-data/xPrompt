import { InvestigationStatus, TaskStatus, HypothesisStatus } from '../types';

export interface StatusConfig {
  label: string;
  description: string;
  bgClass: string;
  textClass: string;
  borderClass: string;
  dotClass: string;
}

export function getInvestigationStatusConfig(status: InvestigationStatus | string): StatusConfig {
  switch (status) {
    case 'draft':
      return {
        label: 'Draft',
        description: 'Investigation drafted, awaiting start.',
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-700',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-400',
      };
    case 'queued':
    case 'pending':
      return {
        label: 'Queued',
        description: 'Waiting in execution queue.',
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-700',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-400',
      };
    case 'running':
    case 'ready':
      return {
        label: 'Executing',
        description: 'Analytical tasks are actively running.',
        bgClass: 'bg-brand-50',
        textClass: 'text-brand-700',
        borderClass: 'border-brand-200',
        dotClass: 'bg-brand-600',
      };
    case 'replanning':
      return {
        label: 'Replanning',
        description: 'New evidence altered hypotheses; generating revised plan.',
        bgClass: 'bg-amber-50',
        textClass: 'text-amber-800',
        borderClass: 'border-amber-200',
        dotClass: 'bg-amber-500',
      };
    case 'completed':
      return {
        label: 'Completed',
        description: 'All tasks and synthesis successfully finished.',
        bgClass: 'bg-emerald-50',
        textClass: 'text-emerald-800',
        borderClass: 'border-emerald-200',
        dotClass: 'bg-emerald-600',
      };
    case 'failed':
      return {
        label: 'Failed',
        description: 'One or more non-recoverable task failures occurred.',
        bgClass: 'bg-rose-50',
        textClass: 'text-rose-800',
        borderClass: 'border-rose-200',
        dotClass: 'bg-rose-600',
      };
    case 'cancelled':
      return {
        label: 'Cancelled',
        description: 'Investigation was terminated by user or operator.',
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-700',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-400',
      };
    default:
      return {
        label: status || 'Unknown',
        description: 'Status not recognized by current schema.',
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-700',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-400',
      };
  }
}

export function getTaskStatusConfig(status: TaskStatus | string): StatusConfig {
  switch (status) {
    case 'pending':
      return {
        label: 'Pending',
        description: 'Awaiting execution order.',
        bgClass: 'bg-slate-50',
        textClass: 'text-slate-500',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-300',
      };
    case 'ready':
      return {
        label: 'Ready',
        description: 'Dependencies satisfied; waiting for runner worker.',
        bgClass: 'bg-sky-50',
        textClass: 'text-sky-800',
        borderClass: 'border-sky-200',
        dotClass: 'bg-sky-500',
      };
    case 'running':
      return {
        label: 'Running',
        description: 'Task is executing in Python analytical environment.',
        bgClass: 'bg-brand-50',
        textClass: 'text-brand-700',
        borderClass: 'border-brand-200',
        dotClass: 'bg-brand-600',
      };
    case 'completed':
      return {
        label: 'Completed',
        description: 'Task executed successfully with verified outputs.',
        bgClass: 'bg-emerald-50',
        textClass: 'text-emerald-800',
        borderClass: 'border-emerald-200',
        dotClass: 'bg-emerald-600',
      };
    case 'failed':
      return {
        label: 'Failed',
        description: 'Execution encountered an error.',
        bgClass: 'bg-rose-50',
        textClass: 'text-rose-800',
        borderClass: 'border-rose-200',
        dotClass: 'bg-rose-600',
      };
    case 'blocked':
      return {
        label: 'Blocked',
        description: 'Waiting for upstream prerequisite tasks to finish.',
        bgClass: 'bg-amber-50',
        textClass: 'text-amber-800',
        borderClass: 'border-amber-200',
        dotClass: 'bg-amber-500',
      };
    case 'skipped':
      return {
        label: 'Skipped',
        description: 'Task rendered redundant by upstream replan revision.',
        bgClass: 'bg-slate-50',
        textClass: 'text-slate-500',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-300',
      };
    default:
      return {
        label: status || 'Unknown',
        description: 'Status not specified.',
        bgClass: 'bg-slate-50',
        textClass: 'text-slate-500',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-300',
      };
  }
}

export function getHypothesisStatusConfig(status: HypothesisStatus | string): StatusConfig {
  switch (status) {
    case 'pending':
      return {
        label: 'Evaluating',
        description: 'Under active evaluation against collected data.',
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-700',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-400',
      };
    case 'supported':
      return {
        label: 'Supported',
        description: 'Empirical evidence validates this hypothesis.',
        bgClass: 'bg-emerald-50',
        textClass: 'text-emerald-800',
        borderClass: 'border-emerald-200',
        dotClass: 'bg-emerald-600',
      };
    case 'contradicted':
      return {
        label: 'Contradicted',
        description: 'Evidence disproved this hypothesis; triggered replan.',
        bgClass: 'bg-rose-50',
        textClass: 'text-rose-800',
        borderClass: 'border-rose-200',
        dotClass: 'bg-rose-600',
      };
    case 'revised':
      return {
        label: 'Revised',
        description: 'Hypothesis reformulated based on secondary evidence.',
        bgClass: 'bg-amber-50',
        textClass: 'text-amber-800',
        borderClass: 'border-amber-200',
        dotClass: 'bg-amber-500',
      };
    case 'inconclusive':
      return {
        label: 'Inconclusive',
        description: 'Dataset lacks statistical power to verify or reject.',
        bgClass: 'bg-slate-100',
        textClass: 'text-slate-700',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-400',
      };
    default:
      return {
        label: status,
        description: '',
        bgClass: 'bg-slate-50',
        textClass: 'text-slate-500',
        borderClass: 'border-slate-200',
        dotClass: 'bg-slate-300',
      };
  }
}

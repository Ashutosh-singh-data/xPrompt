/**
 * ConsultOS Type Definitions & Contracts
 * Aligned with FastAPI Pydantic models and Section 7 specifications
 */

export type InvestigationStatus =
  | 'draft'
  | 'queued'
  | 'pending'
  | 'running'
  | 'ready'
  | 'replanning'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type TaskStatus =
  | 'pending'
  | 'ready'
  | 'running'
  | 'completed'
  | 'failed'
  | 'blocked'
  | 'skipped';

export type HypothesisStatus =
  | 'pending'
  | 'supported'
  | 'contradicted'
  | 'revised'
  | 'inconclusive';

export interface Investigation {
  id: string;
  business_question: string;
  status: InvestigationStatus;
  current_plan_version: number;
  created_at: string;
  updated_at: string;
  dataset_filename?: string;
  dataset_size_bytes?: number;
  dataset_rows_count?: number;
  tasks_count?: number;
  completed_tasks_count?: number;
  error_message?: string | null;
}

export interface Task {
  id: string;
  investigation_id: string;
  title: string;
  description: string;
  task_type: string;
  status: TaskStatus;
  dependencies: string[];
  attempts: number;
  duration?: number; // seconds
  result?: Record<string, any> | string | null;
  error?: string | null;
  blocked_reason?: string | null;
  plan_version?: number;
  is_replan_addition?: boolean;
  can_retry?: boolean;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  id: string;
  investigation_id: string;
  task_id: string;
  source_type: string;
  source_reference: string;
  finding: string;
  supporting_data?: Record<string, any> | null;
  relevant_columns?: string[];
  calculation?: string;
  units_or_period?: string;
  created_at: string;
}

export interface Hypothesis {
  id: string;
  investigation_id: string;
  statement: string;
  status: HypothesisStatus;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  confidence: number; // 0.0 - 1.0
  created_at: string;
  notes?: string;
}

export interface InvestigationEvent {
  id: string;
  investigation_id: string;
  task_id?: string | null;
  event_type:
    | 'plan_created'
    | 'plan_revised'
    | 'task_started'
    | 'task_completed'
    | 'task_failed'
    | 'evidence_recorded'
    | 'hypothesis_updated'
    | 'replanning_triggered'
    | 'report_generated'
    | 'investigation_cancelled'
    | string;
  details: Record<string, any> | string;
  created_at: string;
}

export interface ReportFinding {
  title: string;
  claim: string;
  fact_type: 'observed_fact' | 'interpretation' | 'recommendation';
  evidence_ids: string[];
  impact?: string;
}

export interface ReportCalculation {
  metric: string;
  formula: string;
  result: string;
  evidence_id?: string;
}

export interface FinalReport {
  id: string;
  investigation_id: string;
  business_question: string;
  status: 'ready' | 'generating' | 'partial' | 'failed' | 'not_ready';
  executive_summary: string;
  methodology?: string;
  findings: ReportFinding[];
  calculations?: ReportCalculation[];
  recommendations: string[];
  assumptions?: string[];
  contradictory_evidence?: string[];
  limitations: string[];
  unresolved_questions: string[];
  execution_summary?: {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    plan_revisions: number;
    total_duration_sec: number;
    evidence_count: number;
  };
  created_at: string;
}

export interface BackendHealthResponse {
  status: string;
  version?: string;
  database?: string;
  timestamp?: string;
}

export interface EvaluationItem {
  id: string;
  name: string;
  category: string;
  status: 'passed' | 'failed' | 'running' | 'pending';
  dataset: string;
  question: string;
  duration_sec?: number;
  expected_verdict: string;
  actual_verdict?: string;
  replan_tested: boolean;
  error_recovery_tested: boolean;
  score?: number;
}

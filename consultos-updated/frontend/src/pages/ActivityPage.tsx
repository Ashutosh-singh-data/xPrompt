import React, { useState } from 'react';
import { EvaluationItem } from '../types';
import { formatDuration } from '../utils/formatters';
import { SectionHeader } from '../components/SectionHeader';
import { CheckCircle2, RotateCw, ShieldCheck, GitBranch } from 'lucide-react';

export const ActivityPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'benchmarks' | 'audit'>('benchmarks');

  // Grounded benchmark evaluation test cases from ConsultOS specification
  const testCases: EvaluationItem[] = [
    {
      id: 'eval_01_ecommerce_revenue_drop',
      name: 'Q3 E-commerce Revenue Drop & Dynamic Replan Scenario',
      category: 'Autonomous Diagnosis',
      status: 'passed',
      dataset: 'q3_ecommerce_orders_and_funnel_metrics.csv (148k rows)',
      question: 'Why did net merchandise revenue decline by 18.4% across Q3 despite a 12% increase in paid ad spend?',
      duration_sec: 37.8,
      expected_verdict: 'Payment gateway v2.4 3DS2 challenge timeout on mobile iOS in-app browsers',
      actual_verdict: 'Confirmed: ERR_3DS2_CHALLENGE_TIMEOUT with $1.42M loss',
      replan_tested: true,
      error_recovery_tested: true,
      score: 1.0,
    },
    {
      id: 'eval_02_ad_attribution_waste',
      name: 'Channel Attribution & False Positive Pricing Rejection',
      category: 'Hypothesis Falsification',
      status: 'passed',
      dataset: 'ad_campaign_performance_and_promos.csv',
      question: 'Did promotional discount fatigue cause conversion drops across marketing channels?',
      duration_sec: 18.2,
      expected_verdict: 'Reject pricing elasticity hypothesis (p > 0.05)',
      actual_verdict: 'OLS regression p = 0.42; hypothesis rejected successfully',
      replan_tested: true,
      error_recovery_tested: false,
      score: 0.98,
    },
    {
      id: 'eval_03_inventory_stockout_isolation',
      name: 'Fulfillment & Regional Stockout Resilience Test',
      category: 'Constraint Validation',
      status: 'passed',
      dataset: 'regional_fulfillment_inventory_log.csv',
      question: 'Were stockout rates responsible for revenue drag?',
      duration_sec: 14.5,
      expected_verdict: 'Stockouts within normal bounds (under 2.5%)',
      actual_verdict: 'Average 2.1% across top 100 SKUs; ruled out as primary driver',
      replan_tested: false,
      error_recovery_tested: true,
      score: 1.0,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="card p-7 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="max-w-2xl">
          <h2 className="text-xl font-semibold text-ink tracking-tight">
            Evaluation & verification suite
          </h2>
          <p className="text-sm text-muted mt-2 leading-relaxed">
            Benchmark runs that check task planning, hypothesis testing, dynamic replanning and
            error recovery.
          </p>
        </div>

        <div className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl text-sm font-medium bg-emerald-50 border border-emerald-200 text-emerald-800 shrink-0">
          <ShieldCheck size={17} />
          <span>3 of 3 benchmarks passing</span>
        </div>
      </div>

      {/* Scenarios */}
      <section>
        <SectionHeader title="Evaluation scenarios" count={testCases.length} />

        <div className="space-y-5">
          {testCases.map((tc) => (
            <div key={tc.id} className="card p-7">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-5">
                <div className="min-w-0">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <span className="tag bg-emerald-50 text-emerald-800 border-emerald-200 capitalize">
                      <CheckCircle2 size={12} />
                      {tc.status}
                    </span>
                    <span className="text-xs text-muted">{tc.category}</span>
                  </div>
                  <h3 className="text-[15px] font-semibold text-ink leading-snug">{tc.name}</h3>
                  <span className="font-mono text-xs text-muted mt-1 block">{tc.id}</span>
                </div>

                <div className="flex items-center gap-6 shrink-0">
                  <div>
                    <span className="meta-label">Duration</span>
                    <span className="text-sm font-medium text-ink tabular-nums">
                      {formatDuration(tc.duration_sec)}
                    </span>
                  </div>
                  <div>
                    <span className="meta-label">Score</span>
                    <span className="text-sm font-semibold text-emerald-700 tabular-nums">
                      {(tc.score! * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-subtle p-4 rounded-lg border border-line mb-5">
                <span className="meta-label">Question</span>
                <p className="text-sm text-body leading-relaxed">{tc.question}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg border border-line">
                  <span className="meta-label">Expected verdict</span>
                  <p className="text-sm text-body leading-relaxed">{tc.expected_verdict}</p>
                </div>

                <div className="p-4 rounded-lg border border-emerald-200 bg-emerald-50/50">
                  <span className="meta-label text-emerald-800">Result</span>
                  <p className="text-sm text-emerald-900 leading-relaxed">{tc.actual_verdict}</p>
                </div>
              </div>

              <div className="flex items-center gap-x-6 gap-y-2 flex-wrap mt-5 pt-5 border-t border-line text-[13px] text-muted">
                <span className="flex items-center gap-2">
                  <GitBranch size={14} className={tc.replan_tested ? 'text-amber-600' : 'text-faint'} />
                  Replanning {tc.replan_tested ? 'verified' : 'not tested'}
                </span>
                <span className="flex items-center gap-2">
                  <RotateCw size={14} className={tc.error_recovery_tested ? 'text-teal-600' : 'text-faint'} />
                  Error recovery {tc.error_recovery_tested ? 'verified' : 'not tested'}
                </span>
                <span className="font-mono text-xs">{tc.dataset}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

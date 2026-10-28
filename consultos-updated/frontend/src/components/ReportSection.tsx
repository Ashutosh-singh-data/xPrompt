import React from 'react';
import { FinalReport } from '../types';
import { formatTimestamp, formatDuration } from '../utils/formatters';
import {
  FileText,
  Download,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  ShieldCheck,
  TrendingDown,
} from 'lucide-react';

interface ReportSectionProps {
  report: FinalReport | null;
  onSelectEvidence?: (evidenceId: string) => void;
}

export const ReportSection: React.FC<ReportSectionProps> = ({
  report,
  onSelectEvidence,
}) => {
  if (!report || report.status === 'not_ready') {
    return (
      <div className="px-8 py-16 text-center border border-dashed border-line-strong rounded-xl bg-surface">
        <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-5">
          <FileText size={22} />
        </div>
        <h4 className="text-base font-semibold text-ink">Report not ready yet</h4>
        <p className="text-sm text-muted max-w-md mx-auto mt-2 leading-relaxed">
          The verified report is generated automatically once the final synthesis task completes.
        </p>
      </div>
    );
  }

  const isPartial = report.status === 'partial';

  // Export handlers: downloads real Markdown or HTML files
  const downloadMarkdown = () => {
    let md = `# ConsultOS Business Investigation Report\n\n`;
    md += `**Investigation ID:** ${report.investigation_id}\n`;
    md += `**Date:** ${formatTimestamp(report.created_at)}\n`;
    md += `**Question:** ${report.business_question}\n`;
    md += `**Status:** ${report.status.toUpperCase()}\n\n`;
    md += `## Executive Summary\n\n${report.executive_summary}\n\n`;

    if (report.methodology) {
      md += `## Methodology\n\n${report.methodology}\n\n`;
    }

    md += `## Verified Findings\n\n`;
    report.findings.forEach((f, idx) => {
      md += `### ${idx + 1}. ${f.title} (${f.fact_type.replace(/_/g, ' ')})\n`;
      md += `${f.claim}\n\n`;
      if (f.impact) md += `- **Financial Impact:** ${f.impact}\n`;
      if (f.evidence_ids && f.evidence_ids.length > 0) {
        md += `- **Citations:** ${f.evidence_ids.join(', ')}\n`;
      }
      md += `\n`;
    });

    if (report.calculations && report.calculations.length > 0) {
      md += `## Quantitative Calculations\n\n`;
      report.calculations.forEach((c) => {
        md += `- **${c.metric}:** ${c.result} (Formula: \`${c.formula}\`)\n`;
      });
      md += `\n`;
    }

    md += `## Actionable Recommendations\n\n`;
    report.recommendations.forEach((rec, idx) => {
      md += `${idx + 1}. ${rec}\n`;
    });

    if (report.limitations && report.limitations.length > 0) {
      md += `\n## Analytical Limitations\n\n`;
      report.limitations.forEach((l) => {
        md += `- ${l}\n`;
      });
    }

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `consultos_report_${report.investigation_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadHTML = () => {
    let html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ConsultOS Report - ${report.investigation_id}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 860px; margin: 40px auto; padding: 0 20px; color: #1e293b; background: #fff; }
  h1 { font-size: 24px; border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 8px; }
  h2 { font-size: 18px; margin-top: 32px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }
  h3 { font-size: 15px; margin-top: 20px; }
  .meta { color: #64748b; font-size: 13px; font-family: monospace; margin-bottom: 24px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; text-transform: uppercase; font-weight: bold; background: #f1f5f9; color: #334155; }
  .finding-box { border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: #f8fafc; }
  .impact { color: #e11d48; font-weight: bold; margin-top: 8px; font-size: 13px; }
  .calc-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
  .calc-item { border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; background: #fff; }
</style>
</head>
<body>
<h1>ConsultOS Business Investigation Report</h1>
<div class="meta">
  Investigation ID: ${report.investigation_id} | Date: ${formatTimestamp(report.created_at)} | Status: ${report.status.toUpperCase()}
</div>
<h2>Inquiry Question</h2>
<p style="font-weight: 600; font-size: 16px;">${report.business_question}</p>
<h2>Executive Summary</h2>
<p>${report.executive_summary}</p>
${report.methodology ? `<h2>Methodology</h2><p>${report.methodology}</p>` : ''}
<h2>Verified Empirical Findings</h2>
${report.findings.map((f, i) => `
  <div class="finding-box">
    <h3>${i + 1}. ${f.title} <span class="badge">${f.fact_type.replace(/_/g, ' ')}</span></h3>
    <p>${f.claim}</p>
    ${f.impact ? `<div class="impact">Impact: ${f.impact}</div>` : ''}
    ${f.evidence_ids && f.evidence_ids.length ? `<div style="font-size:12px; color:#64748b; margin-top:8px;">Citations: ${f.evidence_ids.join(', ')}</div>` : ''}
  </div>
`).join('')}
${report.calculations && report.calculations.length ? `
  <h2>Quantitative Calculations</h2>
  <div class="calc-grid">
    ${report.calculations.map(c => `
      <div class="calc-item">
        <strong>${c.metric}</strong><br>
        <code style="font-size:11px; color:#475569;">${c.formula}</code><br>
        <span style="font-size:16px; font-weight:bold; color:#0f172a;">${c.result}</span>
      </div>
    `).join('')}
  </div>
` : ''}
<h2>Actionable Recommendations</h2>
<ol>
  ${report.recommendations.map(r => `<li>${r}</li>`).join('')}
</ol>
</body>
</html>`;

    const blob = new Blob([html], { type: 'text/html;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `consultos_report_${report.investigation_id}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const factTypeClass = (t: string) =>
    t === 'observed_fact'
      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
      : t === 'interpretation'
      ? 'bg-brand-50 text-brand-700 border-brand-200'
      : 'bg-amber-50 text-amber-800 border-amber-200';

  const sectionTitle = 'text-base font-semibold text-ink';

  return (
    <div className="space-y-10">
      {isPartial && (
        <div
          role="status"
          className="p-5 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-4 text-amber-900 text-sm"
        >
          <AlertCircle size={19} className="shrink-0 text-amber-700 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold block">Partial report</span>
            Some tasks failed or didn’t produce conclusive data, so these findings reflect only the
            completed work.
          </div>
        </div>
      )}

      {/* Title + export */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
        <div className="min-w-0">
          <div className="flex items-center gap-3 mb-4 flex-wrap">
            <span className="tag bg-brand-50 text-brand-700 border-brand-200">
              <ShieldCheck size={13} />
              Verified report
            </span>
            <span className="text-[13px] text-muted">{formatTimestamp(report.created_at)}</span>
          </div>
          <h2 className="text-2xl font-semibold text-ink leading-snug tracking-tight">
            {report.business_question}
          </h2>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button onClick={downloadMarkdown} className="btn btn-secondary">
            <Download size={15} />
            <span>Markdown</span>
          </button>
          <button onClick={downloadHTML} className="btn btn-secondary">
            <Download size={15} />
            <span>HTML</span>
          </button>
        </div>
      </div>

      {/* Execution summary */}
      {report.execution_summary && (
        <div className="card grid grid-cols-2 sm:grid-cols-4 divide-x divide-line">
          {[
            {
              label: 'Tasks completed',
              value: `${report.execution_summary.completed_tasks} / ${report.execution_summary.total_tasks}`,
            },
            { label: 'Plan revisions', value: `v${report.execution_summary.plan_revisions}` },
            { label: 'Evidence cited', value: `${report.execution_summary.evidence_count}` },
            {
              label: 'Total duration',
              value: formatDuration(report.execution_summary.total_duration_sec),
            },
          ].map((m) => (
            <div key={m.label} className="px-6 py-5">
              <span className="text-[13px] text-muted block">{m.label}</span>
              <span className="text-2xl font-semibold text-ink tabular-nums mt-1 block">
                {m.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Executive summary */}
      <section className="card p-8 border-l-4 border-l-brand-600">
        <h3 className={`${sectionTitle} mb-4`}>Executive summary</h3>
        <p className="text-[15px] text-ink leading-[1.75] max-w-[68ch]">
          {report.executive_summary}
        </p>
      </section>

      {/* Methodology */}
      {report.methodology && (
        <section>
          <h3 className={`${sectionTitle} mb-3`}>Methodology</h3>
          <p className="text-sm text-body leading-[1.75] max-w-[72ch]">{report.methodology}</p>
        </section>
      )}

      {/* Findings */}
      <section>
        <h3 className={`${sectionTitle} mb-5`}>
          Verified findings
          <span className="ml-2 text-xs font-medium text-muted bg-slate-100 rounded-full px-2 py-0.5 tabular-nums align-middle">
            {report.findings.length}
          </span>
        </h3>
        <div className="space-y-4">
          {report.findings.map((f, idx) => (
            <div key={idx} className="card p-6">
              <div className="flex items-start justify-between gap-4 mb-3">
                <h4 className="text-[15px] font-semibold text-ink leading-snug flex items-start gap-3">
                  <span className="text-brand-600 tabular-nums">{idx + 1}.</span>
                  <span>{f.title}</span>
                </h4>
                <span className={`tag shrink-0 capitalize ${factTypeClass(f.fact_type)}`}>
                  {f.fact_type.replace(/_/g, ' ')}
                </span>
              </div>

              <p className="text-sm text-body leading-relaxed pl-[26px]">{f.claim}</p>

              {f.impact && (
                <div className="ml-[26px] mt-4 flex items-center gap-3 text-sm text-rose-900 bg-rose-50 px-4 py-3 rounded-lg border border-rose-200">
                  <TrendingDown size={16} className="shrink-0 text-rose-700" />
                  <span>
                    <span className="font-medium">Financial impact:</span> {f.impact}
                  </span>
                </div>
              )}

              {f.evidence_ids && f.evidence_ids.length > 0 && (
                <div className="ml-[26px] flex items-center gap-2 flex-wrap mt-4 pt-4 border-t border-line">
                  <span className="text-[13px] text-muted">Evidence</span>
                  {f.evidence_ids.map((evId) => (
                    <button
                      key={evId}
                      onClick={() => onSelectEvidence?.(evId)}
                      className="font-mono text-xs text-brand-700 bg-brand-50 hover:bg-brand-100 px-2 py-0.5 rounded-md border border-brand-200 transition-colors inline-flex items-center gap-1.5"
                    >
                      <span>{evId}</span>
                      <ExternalLink size={10} />
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Calculations */}
      {report.calculations && report.calculations.length > 0 && (
        <section>
          <h3 className={`${sectionTitle} mb-5`}>Calculations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.calculations.map((calc, idx) => (
              <div key={idx} className="card p-5 flex flex-col justify-between gap-4">
                <div>
                  <span className="text-sm font-medium text-ink block mb-1.5">{calc.metric}</span>
                  <code className="text-xs font-mono text-muted block break-words">
                    {calc.formula}
                  </code>
                </div>
                <div className="pt-4 border-t border-line flex items-center justify-between gap-3">
                  <span className="text-lg font-semibold text-ink tabular-nums">{calc.result}</span>
                  {calc.evidence_id && onSelectEvidence && (
                    <button
                      onClick={() => onSelectEvidence(calc.evidence_id!)}
                      className="font-mono text-xs text-brand-700 hover:underline"
                    >
                      {calc.evidence_id}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recommendations */}
      <section>
        <h3 className={`${sectionTitle} mb-5`}>Recommendations</h3>
        <ol className="space-y-3">
          {report.recommendations.map((rec, idx) => (
            <li key={idx} className="card flex items-start gap-4 px-5 py-4">
              <span className="w-7 h-7 rounded-full bg-brand-600 text-white text-[13px] font-semibold flex items-center justify-center shrink-0 tabular-nums">
                {idx + 1}
              </span>
              <p className="text-sm text-ink leading-relaxed pt-0.5">{rec}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Limitations & open questions */}
      {((report.limitations && report.limitations.length > 0) ||
        (report.unresolved_questions && report.unresolved_questions.length > 0)) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {report.limitations && report.limitations.length > 0 && (
            <div className="p-6 bg-subtle border border-line rounded-xl">
              <h4 className="text-sm font-semibold text-ink mb-3 flex items-center gap-2">
                <AlertCircle size={15} className="text-muted" />
                Limitations
              </h4>
              <ul className="list-disc pl-5 text-sm text-body space-y-2 leading-relaxed marker:text-faint">
                {report.limitations.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
            </div>
          )}

          {report.unresolved_questions && report.unresolved_questions.length > 0 && (
            <div className="p-6 bg-subtle border border-line rounded-xl">
              <h4 className="text-sm font-semibold text-ink mb-3 flex items-center gap-2">
                <HelpCircle size={15} className="text-muted" />
                Open questions
              </h4>
              <ul className="list-disc pl-5 text-sm text-body space-y-2 leading-relaxed marker:text-faint">
                {report.unresolved_questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

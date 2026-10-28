import React, { useState } from 'react';
import { investigationsService } from '../services/investigations';
import { FileDropzone } from '../components/FileDropzone';
import { ErrorState } from '../components/ErrorState';
import { ArrowLeft, Loader2, AlertCircle, Lightbulb } from 'lucide-react';

interface NewInvestigationPageProps {
  onBackToDashboard: () => void;
  onCreated: (investigationId: string) => void;
}

export const NewInvestigationPage: React.FC<NewInvestigationPageProps> = ({
  onBackToDashboard,
  onCreated,
}) => {
  const [question, setQuestion] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const samplePrompts = [
    'Why did net merchandise revenue decline by 18.4% across Q3 despite a 12% increase in paid ad spend?',
    'What caused the checkout abandonment spike on iOS Safari devices following the latest release?',
    'Which product categories exhibit the highest margin decay and inventory turnover slowdown?',
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setApiError(null);

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setValidationError('Business investigation question is required. Please specify a clear analytical question.');
      return;
    }

    if (trimmedQuestion.length < 15) {
      setValidationError('Please provide a sufficiently detailed business question (at least 15 characters).');
      return;
    }

    setIsSubmitting(true);

    try {
      const created = await investigationsService.createInvestigation(trimmedQuestion, file);
      onCreated(created.id);
    } catch (err: any) {
      setApiError(err.message || 'Failed to submit investigation to backend API.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Back + intro */}
      <div>
        <button
          onClick={onBackToDashboard}
          className="inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink transition-colors mb-5"
          aria-label="Back to dashboard"
        >
          <ArrowLeft size={16} />
          Back to dashboard
        </button>
        <h2 className="text-2xl font-semibold text-ink tracking-tight">New investigation</h2>
        <p className="text-sm text-muted mt-2 leading-relaxed max-w-xl">
          Describe the business question you want answered. Optionally attach a CSV dataset so the
          analysis can work from your own data.
        </p>
      </div>

      {apiError && (
        <ErrorState
          title="Couldn’t create the investigation"
          message={apiError}
          onRetry={() => setApiError(null)}
        />
      )}

      <form onSubmit={handleSubmit} className="card divide-y divide-line">
        {/* Question */}
        <div className="p-8">
          <label htmlFor="business-question-input" className="label">
            Business question <span className="text-rose-600">*</span>
          </label>
          <textarea
            id="business-question-input"
            rows={4}
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="e.g. Why did net merchandise revenue decline by 18.4% across Q3 despite a 12% increase in paid ad spend?"
            className="input leading-relaxed resize-y"
          />
          <p className="hint">Be specific about the metric, the time period and what you expected.</p>

          {/* Example questions (do not submit) */}
          <div className="mt-6">
            <span className="flex items-center gap-2 text-[13px] font-medium text-ink mb-3">
              <Lightbulb size={15} className="text-amber-600" />
              Example questions
            </span>
            <div className="flex flex-col gap-2.5">
              {samplePrompts.map((p, i) => (
                <button
                  type="button"
                  key={i}
                  onClick={() => {
                    setQuestion(p);
                    if (validationError) setValidationError(null);
                  }}
                  className="text-left text-[13px] leading-relaxed text-body hover:text-brand-700 bg-subtle hover:bg-brand-50 px-4 py-3 rounded-lg border border-line hover:border-brand-200 transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Dataset */}
        <div className="p-8">
          <label className="label">
            Supporting dataset <span className="font-normal text-muted">(optional)</span>
          </label>
          <FileDropzone selectedFile={file} onFileSelect={setFile} />
          <p className="hint">
            Standard comma-delimited tables work best: orders, funnel events, customer cohorts.
          </p>
        </div>

        {validationError && (
          <div className="px-8 pt-6">
            <div
              role="alert"
              className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm flex items-start gap-3"
            >
              <AlertCircle size={17} className="shrink-0 mt-0.5 text-rose-600" />
              <span>{validationError}</span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="px-8 py-5 bg-subtle rounded-b-xl flex items-center justify-between gap-3">
          <button type="button" onClick={onBackToDashboard} className="btn btn-secondary">
            Cancel
          </button>

          <button type="submit" disabled={isSubmitting} className="btn btn-primary">
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Creating plan…</span>
              </>
            ) : (
              <span>Create investigation</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

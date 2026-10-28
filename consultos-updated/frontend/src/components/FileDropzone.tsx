import React, { useRef, useState } from 'react';
import { UploadCloud, FileSpreadsheet, X, AlertCircle, CheckCircle2 } from 'lucide-react';
import { formatBytes } from '../utils/formatters';

interface FileDropzoneProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
  maxSizeBytes?: number; // e.g. 25MB
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  selectedFile,
  onFileSelect,
  maxSizeBytes = 25 * 1024 * 1024,
}) => {
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);

    // Validate extension / mime type
    const isCsv = file.name.toLowerCase().endsWith('.csv') || file.type === 'text/csv' || file.type === 'application/vnd.ms-excel';
    if (!isCsv) {
      setValidationError('Unsupported file format. The backend currently accepts CSV files only (.csv).');
      return;
    }

    if (file.size > maxSizeBytes) {
      setValidationError(`File exceeds maximum size threshold of ${formatBytes(maxSizeBytes)}.`);
      return;
    }

    onFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    onFileSelect(null);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-3">
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {!selectedFile ? (
        <div
          role="button"
          tabIndex={0}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          className={`border-2 border-dashed rounded-xl px-6 py-10 text-center cursor-pointer transition-colors ${
            isDragOver
              ? 'border-brand-600 bg-brand-50'
              : 'border-line-strong bg-subtle hover:border-brand-500 hover:bg-brand-50/60'
          }`}
        >
          <div className="w-11 h-11 rounded-xl bg-white border border-line shadow-card mx-auto mb-4 flex items-center justify-center text-brand-600">
            <UploadCloud size={20} />
          </div>
          <p className="text-sm font-medium text-ink mb-1">
            Drop a CSV file here, or <span className="text-brand-600">browse</span>
          </p>
          <p className="text-[13px] text-muted">
            .csv only · up to {formatBytes(maxSizeBytes)}
          </p>
        </div>
      ) : (
        <div className="bg-surface border border-line-strong rounded-xl p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0">
            <div className="w-11 h-11 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center shrink-0">
              <FileSpreadsheet size={20} />
            </div>
            <div className="min-w-0">
              <span className="text-sm font-medium text-ink block truncate" title={selectedFile.name}>
                {selectedFile.name}
              </span>
              <div className="flex items-center gap-2 text-xs text-muted mt-0.5">
                <span className="tabular-nums">{formatBytes(selectedFile.size)}</span>
                <span aria-hidden="true">·</span>
                <span className="text-emerald-700 flex items-center gap-1 font-medium">
                  <CheckCircle2 size={12} /> Valid CSV
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn btn-sm btn-secondary"
            >
              Replace
            </button>
            <button
              type="button"
              onClick={removeFile}
              aria-label="Remove attached file"
              className="icon-btn hover:text-rose-600"
            >
              <X size={17} />
            </button>
          </div>
        </div>
      )}

      {validationError && (
        <div
          role="alert"
          className="flex items-start gap-3 p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-[13px]"
        >
          <AlertCircle size={15} className="shrink-0 mt-0.5 text-rose-600" />
          <span>{validationError}</span>
        </div>
      )}
    </div>
  );
};

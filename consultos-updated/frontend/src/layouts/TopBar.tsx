import React from 'react';
import { ConnectionState, getStoredApiBaseUrl, isSimulatorForced } from '../services/api';
import { WifiOff, RefreshCw, Cpu, Settings2 } from 'lucide-react';

interface TopBarProps {
  currentPageTitle: string;
  subtitle?: string;
  connectionState: ConnectionState;
  onOpenSettings: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  currentPageTitle,
  subtitle,
  connectionState,
  onOpenSettings,
  onRefresh,
  isRefreshing = false,
}) => {
  const isSim = isSimulatorForced();
  const baseUrl = getStoredApiBaseUrl();

  const pill =
    'inline-flex items-center gap-2 h-8 px-3 rounded-full text-[13px] font-medium border transition-colors';

  const getConnectionBadge = () => {
    if (isSim) {
      return (
        <button
          onClick={onOpenSettings}
          className={`${pill} bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100`}
          title="Sandbox simulation mode is active"
        >
          <Cpu size={13} />
          <span>Simulation mode</span>
        </button>
      );
    }

    switch (connectionState) {
      case 'connected':
        return (
          <button
            onClick={onOpenSettings}
            className={`${pill} bg-emerald-50 border-emerald-200 text-emerald-800 hover:bg-emerald-100`}
            title={`Connected to ${baseUrl}`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-600" />
            <span>Connected</span>
          </button>
        );
      case 'reconnecting':
        return (
          <button
            onClick={onOpenSettings}
            className={`${pill} bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100`}
            title="Reconnecting to backend stream"
          >
            <RefreshCw size={12} className="animate-spin" />
            <span>Reconnecting</span>
          </button>
        );
      case 'offline':
      default:
        return (
          <button
            onClick={onOpenSettings}
            className={`${pill} bg-rose-50 border-rose-200 text-rose-800 hover:bg-rose-100`}
            title={`FastAPI backend offline (${baseUrl})`}
          >
            <WifiOff size={12} />
            <span>Offline</span>
          </button>
        );
    }
  };

  return (
    <header className="h-16 border-b border-line bg-surface/90 backdrop-blur-md px-4 sm:px-6 lg:px-10 flex items-center justify-between gap-6 sticky top-0 z-30">
      <div className="min-w-0">
        <h1 className="text-lg font-semibold text-ink tracking-tight truncate leading-tight">
          {currentPageTitle}
        </h1>
        {subtitle && (
          <p className="text-[13px] text-muted hidden sm:block truncate">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {getConnectionBadge()}

        <span className="hidden sm:block w-px h-5 bg-line mx-1" aria-hidden="true" />

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            aria-label="Refresh data"
            className="icon-btn hidden sm:inline-flex"
            title="Refresh backend state"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
          </button>
        )}

        <button
          onClick={onOpenSettings}
          aria-label="Open backend settings"
          className="icon-btn"
          title="Configure backend host & integration"
        >
          <Settings2 size={17} />
        </button>
      </div>
    </header>
  );
};

import React, { useState, useEffect } from 'react';
import { Sidebar, NavItemKey } from './Sidebar';
import { TopBar } from './TopBar';
import { ConnectionSettingsModal } from '../components/ConnectionSettingsModal';
import { apiClient, ConnectionState } from '../services/api';
import { Menu } from 'lucide-react';

interface AppShellProps {
  currentNav: NavItemKey;
  onNavigate: (key: NavItemKey, investigationId?: string) => void;
  activeInvestigationId?: string | null;
  currentPageTitle: string;
  subtitle?: string;
  children: React.ReactNode;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentNav,
  onNavigate,
  activeInvestigationId,
  currentPageTitle,
  subtitle,
  children,
  onRefresh,
  isRefreshing,
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    apiClient.getConnectionState()
  );

  useEffect(() => {
    // Initial health ping
    apiClient.checkHealth();

    const unsub = apiClient.subscribeConnection((st) => {
      setConnectionState(st);
    });

    const handleSimulatorChange = () => {
      setConnectionState(apiClient.getConnectionState());
    };

    window.addEventListener('consultos_simulator_changed', handleSimulatorChange);

    return () => {
      unsub();
      window.removeEventListener('consultos_simulator_changed', handleSimulatorChange);
    };
  }, []);

  return (
    <div className="min-h-screen bg-canvas text-body flex">
      {/* Sidebar Navigation */}
      <Sidebar
        currentNav={currentNav}
        onNavigate={onNavigate}
        activeInvestigationId={activeInvestigationId}
        isOpenMobile={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center md:hidden bg-navy-900 px-4 h-14">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="Open navigation menu"
            className="p-2 -ml-2 text-slate-300 hover:text-white rounded-lg"
          >
            <Menu size={20} />
          </button>
          <span className="font-semibold text-[15px] ml-2 text-white">ConsultOS</span>
        </div>

        <TopBar
          currentPageTitle={currentPageTitle}
          subtitle={subtitle}
          connectionState={connectionState}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onRefresh={onRefresh}
          isRefreshing={isRefreshing}
        />

        <main className="flex-1 w-full max-w-[1320px] mx-auto px-4 sm:px-6 lg:px-10 py-8 lg:py-10">
          {children}
        </main>
      </div>

      {/* Connection & Configuration Settings Modal */}
      <ConnectionSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onConnectionChanged={() => {
          setConnectionState(apiClient.getConnectionState());
        }}
      />
    </div>
  );
};

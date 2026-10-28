import React, { useState, useEffect } from 'react';
import { useRouter } from './router';
import { AppShell } from '../layouts/AppShell';
import { NavItemKey } from '../layouts/Sidebar';
import { DashboardPage } from '../pages/DashboardPage';
import { NewInvestigationPage } from '../pages/NewInvestigationPage';
import { InvestigationPage } from '../pages/InvestigationPage';
import { EvidencePage } from '../pages/EvidencePage';
import { ReportPage } from '../pages/ReportPage';
import { ActivityPage } from '../pages/ActivityPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { isSimulatorForced, apiClient, getStoredApiBaseUrl } from '../services/api';
import { Cpu, Server } from 'lucide-react';

export default function App() {
  const { route, navigate } = useRouter();
  const [activeInvestigationId, setActiveInvestigationId] = useState<string | null>(
    route.investigationId || 'inv_ecommerce_rev_q3'
  );
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isOfflineWarningVisible, setIsOfflineWarningVisible] = useState<boolean>(true);

  // Keep active investigation synced with route
  useEffect(() => {
    if (route.investigationId) {
      setActiveInvestigationId(route.investigationId);
    }
  }, [route.investigationId]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await apiClient.checkHealth();
    setTimeout(() => {
      setIsRefreshing(false);
      window.location.reload();
    }, 400);
  };

  const getPageTitleAndSubtitle = (): { title: string; subtitle?: string } => {
    switch (route.page) {
      case 'dashboard':
        return {
          title: 'Investigations Dashboard',
          subtitle: 'Overview of autonomous diagnostics, run statuses, and causal synthesis',
        };
      case 'new-investigation':
        return {
          title: 'Create Investigation',
          subtitle: 'Define business query and upload dataset for DAG task generation',
        };
      case 'investigations':
        return {
          title: 'Investigation Workspace',
          subtitle: `Causal DAG Pipeline · ${activeInvestigationId || 'No active inquiry'}`,
        };
      case 'evidence':
        return {
          title: 'Evidence Explorer',
          subtitle: 'Verifiable empirical citations and quantitative transformations',
        };
      case 'report':
        return {
          title: 'Executive Report',
          subtitle: 'Synthesized findings, business impact, and prescriptive recommendations',
        };
      case 'activity':
        return {
          title: 'Evaluation & Benchmarks',
          subtitle: 'Automated test harness for causal DAG reasoning and replan resilience',
        };
      default:
        return { title: 'ConsultOS' };
    }
  };

  const { title, subtitle } = getPageTitleAndSubtitle();

  const isSim = isSimulatorForced();
  const isConnOffline = apiClient.getConnectionState() === 'offline';
  const showOfflineBanner = (isSim || isConnOffline) && isOfflineWarningVisible;

  return (
    <AppShell
      currentNav={route.page === 'not-found' ? 'dashboard' : (route.page as NavItemKey)}
      onNavigate={(key, invId) => navigate(key, invId || activeInvestigationId)}
      activeInvestigationId={activeInvestigationId}
      currentPageTitle={title}
      subtitle={subtitle}
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
    >
      {/* Non-alarming informational banner if FastAPI backend is offline or sandbox simulation is active */}
      {showOfflineBanner && (
        <div
          role="status"
          className="mb-8 px-5 py-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start justify-between gap-4"
        >
          <div className="flex items-start gap-3.5">
            <div className="w-9 h-9 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
              {isSim ? <Cpu size={17} /> : <Server size={17} />}
            </div>
            <div>
              <span className="text-sm font-semibold text-amber-900 block">
                {isSim
                  ? 'Local simulation mode is active'
                  : `FastAPI backend offline (${getStoredApiBaseUrl()})`}
              </span>
              <p className="text-[13px] text-amber-800 mt-1 leading-relaxed">
                {isSim
                  ? 'ConsultOS is running on deterministic local sample data for review and verification.'
                  : `Could not reach ${getStoredApiBaseUrl()}. Running in local simulation mode. Start your FastAPI server (uvicorn app.main:app --port 8000) to connect to live services.`}
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsOfflineWarningVisible(false)}
            className="btn btn-sm btn-ghost text-amber-800 hover:text-amber-950 hover:bg-amber-100 shrink-0"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Routed Pages */}
      {route.page === 'dashboard' && (
        <DashboardPage
          onNavigateToNew={() => navigate('new-investigation')}
          onOpenInvestigation={(id) => {
            setActiveInvestigationId(id);
            navigate('investigations', id);
          }}
        />
      )}

      {route.page === 'new-investigation' && (
        <NewInvestigationPage
          onBackToDashboard={() => navigate('dashboard')}
          onCreated={(id) => {
            setActiveInvestigationId(id);
            navigate('investigations', id);
          }}
        />
      )}

      {route.page === 'investigations' && activeInvestigationId && (
        <InvestigationPage
          investigationId={activeInvestigationId}
          onNavigateToEvidence={(invId, evId) => navigate('evidence', invId, evId)}
          onNavigateToReport={(invId) => navigate('report', invId)}
        />
      )}

      {route.page === 'evidence' && activeInvestigationId && (
        <EvidencePage
          investigationId={activeInvestigationId}
          initialSelectedEvidenceId={route.evidenceId}
          onNavigateToInvestigation={(invId) => navigate('investigations', invId)}
          onNavigateToReport={(invId) => navigate('report', invId)}
        />
      )}

      {route.page === 'report' && activeInvestigationId && (
        <ReportPage
          investigationId={activeInvestigationId}
          onNavigateToInvestigation={(invId) => navigate('investigations', invId)}
          onNavigateToEvidence={(invId, evId) => navigate('evidence', invId, evId)}
        />
      )}

      {route.page === 'activity' && <ActivityPage />}

      {route.page === 'not-found' && (
        <NotFoundPage
          onBackToDashboard={() => navigate('dashboard')}
          investigationId={activeInvestigationId || undefined}
        />
      )}
    </AppShell>
  );
}

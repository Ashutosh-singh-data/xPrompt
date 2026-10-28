import React from 'react';
import {
  LayoutDashboard,
  Search,
  PlusCircle,
  FileText,
  Activity,
  Layers,
  X,
} from 'lucide-react';

export type NavItemKey = 'dashboard' | 'new-investigation' | 'investigations' | 'evidence' | 'report' | 'activity';

interface SidebarProps {
  currentNav: NavItemKey;
  onNavigate: (key: NavItemKey, investigationId?: string) => void;
  activeInvestigationId?: string | null;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
}

interface NavItem {
  key: NavItemKey;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  badge?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentNav,
  onNavigate,
  activeInvestigationId,
  isOpenMobile = false,
  onCloseMobile,
}) => {
  const groups: { title: string; items: NavItem[] }[] = [
    {
      title: 'Overview',
      items: [
        { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { key: 'new-investigation', label: 'New investigation', icon: PlusCircle },
      ],
    },
    {
      title: 'Current investigation',
      items: [
        {
          key: 'investigations',
          label: 'Workspace',
          icon: Search,
          badge: activeInvestigationId ? 'Active' : undefined,
        },
        { key: 'evidence', label: 'Evidence explorer', icon: Layers },
        { key: 'report', label: 'Executive report', icon: FileText },
      ],
    },
    {
      title: 'Quality',
      items: [{ key: 'activity', label: 'Benchmarks', icon: Activity }],
    },
  ];

  const handleItemClick = (key: NavItemKey) => {
    onNavigate(key, activeInvestigationId || undefined);
    onCloseMobile?.();
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpenMobile && (
        <div
          className="modal-backdrop fixed inset-0 z-40 bg-navy-950/60 md:hidden"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed md:sticky top-0 left-0 h-screen w-[264px] shrink-0 bg-navy-900 z-50 flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="min-h-0 overflow-y-auto">
          {/* Brand */}
          <div className="h-16 px-6 flex items-center justify-between border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-semibold text-[15px]">
                C
              </div>
              <div className="min-w-0 leading-tight">
                <span className="font-semibold text-[15px] text-white block">ConsultOS</span>
                <span className="text-xs text-slate-400 block">Analytical workspace</span>
              </div>
            </div>
            <button
              onClick={onCloseMobile}
              aria-label="Close navigation menu"
              className="md:hidden p-1.5 text-slate-400 hover:text-white rounded-lg"
            >
              <X size={18} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="px-4 py-6 space-y-7" aria-label="Primary">
            {groups.map((group) => (
              <div key={group.title}>
                <p className="px-3 mb-2 text-xs font-medium text-slate-500">{group.title}</p>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentNav === item.key;

                    return (
                      <button
                        key={item.key}
                        onClick={() => handleItemClick(item.key)}
                        aria-current={isActive ? 'page' : undefined}
                        className={`relative w-full flex items-center justify-between gap-3 h-10 px-3 rounded-lg text-sm transition-colors text-left ${
                          isActive
                            ? 'bg-white/10 text-white font-medium'
                            : 'text-slate-300 hover:text-white hover:bg-white/5'
                        }`}
                      >
                        {isActive && (
                          <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r bg-brand-500" />
                        )}
                        <span className="flex items-center gap-3 min-w-0">
                          <Icon
                            size={17}
                            className={isActive ? 'text-brand-200' : 'text-slate-400'}
                          />
                          <span className="truncate">{item.label}</span>
                        </span>

                        {item.badge && (
                          <span className="text-xs font-medium bg-brand-600/25 text-brand-200 px-2 py-0.5 rounded-full">
                            {item.badge}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </div>

        {/* Footer: active session + version */}
        <div className="px-4 pb-5 space-y-4">
          {activeInvestigationId && (
            <div className="px-4 py-3 rounded-lg bg-white/5 border border-white/10">
              <span className="text-xs text-slate-400 block mb-1">Active session</span>
              <span
                className="font-mono text-xs text-slate-200 block truncate"
                title={activeInvestigationId}
              >
                {activeInvestigationId}
              </span>
            </div>
          )}
          <div className="px-3 text-xs text-slate-500 flex items-center justify-between">
            <span>ConsultOS v2.4</span>
            <span>FastAPI</span>
          </div>
        </div>
      </aside>
    </>
  );
};

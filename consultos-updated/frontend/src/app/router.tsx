import { useState, useEffect, useCallback } from 'react';
import { NavItemKey } from '../layouts/Sidebar';

export interface RouteState {
  page: NavItemKey | 'not-found';
  investigationId: string | null;
  evidenceId: string | null;
}

export function parseRoute(): RouteState {
  const hash = window.location.hash.replace(/^#\/?/, '');
  if (!hash || hash === 'dashboard') {
    return { page: 'dashboard', investigationId: null, evidenceId: null };
  }

  if (hash === 'new' || hash === 'new-investigation') {
    return { page: 'new-investigation', investigationId: null, evidenceId: null };
  }

  if (hash === 'activity' || hash === 'evaluation') {
    return { page: 'activity', investigationId: null, evidenceId: null };
  }

  // #investigations or #investigation/:id
  const invMatch = hash.match(/^investigation[s]?\/([a-zA-Z0-9_\-]+)/);
  if (invMatch) {
    return { page: 'investigations', investigationId: invMatch[1], evidenceId: null };
  }

  // #evidence/:id or #evidence/:id/:evidenceId
  const evMatch = hash.match(/^evidence\/([a-zA-Z0-9_\-]+)(?:\/([a-zA-Z0-9_\-]+))?/);
  if (evMatch) {
    return { page: 'evidence', investigationId: evMatch[1], evidenceId: evMatch[2] || null };
  }

  // #report/:id
  const repMatch = hash.match(/^report\/([a-zA-Z0-9_\-]+)/);
  if (repMatch) {
    return { page: 'report', investigationId: repMatch[1], evidenceId: null };
  }

  return { page: 'dashboard', investigationId: null, evidenceId: null };
}

export function useRouter() {
  const [route, setRoute] = useState<RouteState>(() => parseRoute());

  useEffect(() => {
    const handleHashChange = () => {
      setRoute(parseRoute());
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = useCallback((page: NavItemKey | 'not-found', investigationId?: string | null, evidenceId?: string | null) => {
    let newHash = '';
    switch (page) {
      case 'dashboard':
        newHash = '#dashboard';
        break;
      case 'new-investigation':
        newHash = '#new';
        break;
      case 'investigations':
        newHash = investigationId ? `#investigation/${investigationId}` : '#dashboard';
        break;
      case 'evidence':
        if (investigationId) {
          newHash = evidenceId ? `#evidence/${investigationId}/${evidenceId}` : `#evidence/${investigationId}`;
        } else {
          newHash = '#dashboard';
        }
        break;
      case 'report':
        newHash = investigationId ? `#report/${investigationId}` : '#dashboard';
        break;
      case 'activity':
        newHash = '#activity';
        break;
      default:
        newHash = '#dashboard';
    }

    if (window.location.hash !== newHash) {
      window.location.hash = newHash;
    } else {
      setRoute(parseRoute());
    }
  }, []);

  return {
    route,
    navigate,
  };
}

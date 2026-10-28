import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Investigation,
  Task,
  Evidence,
  Hypothesis,
  InvestigationEvent,
  FinalReport,
} from '../types';
import { investigationsService } from '../services/investigations';
import { useInvestigationStream } from './useInvestigationStream';

export function useInvestigation(investigationId: string | null) {
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const [report, setReport] = useState<FinalReport | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isExecutingAction, setIsExecutingAction] = useState<boolean>(false);

  const isMountedRef = useRef(true);

  const fetchData = useCallback(async (silent = false) => {
    if (!investigationId) return;
    if (!silent) setIsLoading(true);
    setError(null);

    try {
      const [invData, taskData, evData, hypData, eventData, repData] = await Promise.all([
        investigationsService.getInvestigation(investigationId),
        investigationsService.getTasks(investigationId),
        investigationsService.getEvidence(investigationId),
        investigationsService.getHypotheses(investigationId),
        investigationsService.getEvents(investigationId),
        investigationsService.getReport(investigationId).catch(() => null),
      ]);

      if (!isMountedRef.current) return;

      setInvestigation(invData);
      setTasks(taskData);
      setEvidence(evData);
      setHypotheses(hypData);
      setEvents(eventData);
      setReport(repData);
    } catch (err: any) {
      if (!isMountedRef.current) return;
      setError(err.message || 'Failed to fetch investigation details');
    } finally {
      if (isMountedRef.current && !silent) {
        setIsLoading(false);
      }
    }
  }, [investigationId]);

  // Initial load
  useEffect(() => {
    isMountedRef.current = true;
    fetchData();

    return () => {
      isMountedRef.current = false;
    };
  }, [fetchData]);

  // Handle incoming stream events to update state optimistically
  const handleStreamEvent = useCallback((event: InvestigationEvent) => {
    setEvents((prev) => {
      if (prev.some((e) => e.id === event.id)) return prev;
      return [...prev, event];
    });

    // Re-fetch authoritative persisted state from backend
    fetchData(true);
  }, [fetchData]);

  const isLive = investigation?.status === 'running' || investigation?.status === 'replanning';

  // Bounded polling if running or replanning as backup to SSE
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      fetchData(true);
    }, 2500);

    return () => clearInterval(interval);
  }, [isLive, fetchData]);

  const { streamStatus, reconnect: reconnectStream } = useInvestigationStream({
    investigationId,
    enabled: Boolean(investigationId),
    onEvent: handleStreamEvent,
  });

  // Action: Run
  const runInvestigation = useCallback(async () => {
    if (!investigationId) return;
    setIsExecutingAction(true);
    try {
      await investigationsService.runInvestigation(investigationId);
      await fetchData(true);
    } catch (err: any) {
      setError(err.message || 'Failed to start execution');
    } finally {
      setIsExecutingAction(false);
    }
  }, [investigationId, fetchData]);

  // Action: Cancel
  const cancelInvestigation = useCallback(async () => {
    if (!investigationId) return;
    setIsExecutingAction(true);
    try {
      await investigationsService.cancelInvestigation(investigationId);
      await fetchData(true);
    } catch (err: any) {
      setError(err.message || 'Failed to cancel investigation');
    } finally {
      setIsExecutingAction(false);
    }
  }, [investigationId, fetchData]);

  // Action: Retry Task
  const retryTask = useCallback(async (taskId: string) => {
    if (!investigationId) return;
    setIsExecutingAction(true);
    try {
      await investigationsService.retryTask(investigationId, taskId);
      await fetchData(true);
    } catch (err: any) {
      setError(err.message || `Failed to retry task ${taskId}`);
    } finally {
      setIsExecutingAction(false);
    }
  }, [investigationId, fetchData]);

  return {
    investigation,
    tasks,
    evidence,
    hypotheses,
    events,
    report,
    isLoading,
    error,
    isExecutingAction,
    streamStatus,
    refresh: () => fetchData(false),
    runInvestigation,
    cancelInvestigation,
    retryTask,
    reconnectStream,
  };
}

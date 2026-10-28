import { useEffect, useRef, useState, useCallback } from 'react';
import { investigationsService } from '../services/investigations';
import { InvestigationEvent } from '../types';

export interface UseInvestigationStreamOptions {
  investigationId: string | null;
  enabled?: boolean;
  onEvent?: (event: InvestigationEvent) => void;
}

export function useInvestigationStream({
  investigationId,
  enabled = true,
  onEvent,
}: UseInvestigationStreamOptions) {
  const [streamStatus, setStreamStatus] = useState<'idle' | 'connecting' | 'connected' | 'reconnecting' | 'error'>('idle');
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const unsubscribeRef = useRef<(() => void) | null>(null);

  const startStream = useCallback(() => {
    if (!investigationId || !enabled) return;

    setStreamStatus('connecting');

    unsubscribeRef.current?.();

    const unsub = investigationsService.subscribeEventStream(investigationId, {
      onConnect: () => {
        setStreamStatus('connected');
      },
      onEvent: (event) => {
        setEvents((prev) => {
          // Deduplicate by event id
          if (prev.some((e) => e.id === event.id)) return prev;
          return [...prev, event];
        });
        onEventRef.current?.(event);
      },
      onError: (err) => {
        console.warn('[ConsultOS Stream Error]', err);
        setStreamStatus('reconnecting');
      },
    });

    unsubscribeRef.current = unsub;
  }, [investigationId, enabled]);

  useEffect(() => {
    if (enabled && investigationId) {
      startStream();
    } else {
      setStreamStatus('idle');
    }

    return () => {
      unsubscribeRef.current?.();
      unsubscribeRef.current = null;
    };
  }, [investigationId, enabled, startStream]);

  return {
    streamStatus,
    events,
    reconnect: startStream,
  };
}

import {
  apiClient,
  isSimulatorForced,
  getStoredApiBaseUrl,
} from './api';
import { localSimulator } from './mockEngine';
import {
  Investigation,
  Task,
  Evidence,
  Hypothesis,
  InvestigationEvent,
  FinalReport,
} from '../types';

export class InvestigationsService {
  private shouldUseSimulator(): boolean {
    if (isSimulatorForced()) return true;
    return apiClient.getConnectionState() === 'offline';
  }

  // GET /api/investigations
  public async listInvestigations(): Promise<Investigation[]> {
    if (this.shouldUseSimulator()) {
      return localSimulator.getInvestigations();
    }

    try {
      return await apiClient.request<Investigation[]>('/api/investigations');
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        return localSimulator.getInvestigations();
      }
      throw err;
    }
  }

  // POST /api/investigations (Supports multipart upload or JSON)
  public async createInvestigation(
    businessQuestion: string,
    file?: File | null
  ): Promise<Investigation> {
    if (this.shouldUseSimulator()) {
      return localSimulator.createInvestigation(
        businessQuestion,
        file ? { name: file.name, size: file.size } : undefined
      );
    }

    try {
      if (file) {
        const formData = new FormData();
        formData.append('business_question', businessQuestion);
        formData.append('file', file);
        return await apiClient.request<Investigation>('/api/investigations', {
          method: 'POST',
          body: formData,
        });
      } else {
        return await apiClient.request<Investigation>('/api/investigations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ business_question: businessQuestion }),
        });
      }
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        return localSimulator.createInvestigation(
          businessQuestion,
          file ? { name: file.name, size: file.size } : undefined
        );
      }
      throw err;
    }
  }

  // GET /api/investigations/{id}
  public async getInvestigation(id: string): Promise<Investigation> {
    if (this.shouldUseSimulator()) {
      const inv = localSimulator.getInvestigationById(id);
      if (!inv) throw { message: `Investigation ${id} not found`, status: 404 };
      return inv;
    }

    try {
      return await apiClient.request<Investigation>(`/api/investigations/${id}`);
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        const inv = localSimulator.getInvestigationById(id);
        if (inv) return inv;
      }
      throw err;
    }
  }

  // POST /api/investigations/{id}/run
  public async runInvestigation(id: string): Promise<{ status: string }> {
    if (this.shouldUseSimulator()) {
      localSimulator.runInvestigation(id);
      return { status: 'running' };
    }

    try {
      return await apiClient.request<{ status: string }>(`/api/investigations/${id}/run`, {
        method: 'POST',
      });
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        localSimulator.runInvestigation(id);
        return { status: 'running' };
      }
      throw err;
    }
  }

  // GET /api/investigations/{id}/tasks
  public async getTasks(id: string): Promise<Task[]> {
    if (this.shouldUseSimulator()) {
      return localSimulator.getTasks(id);
    }

    try {
      return await apiClient.request<Task[]>(`/api/investigations/${id}/tasks`);
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        return localSimulator.getTasks(id);
      }
      throw err;
    }
  }

  // GET /api/investigations/{id}/evidence
  public async getEvidence(id: string): Promise<Evidence[]> {
    if (this.shouldUseSimulator()) {
      return localSimulator.getEvidence(id);
    }

    try {
      return await apiClient.request<Evidence[]>(`/api/investigations/${id}/evidence`);
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        return localSimulator.getEvidence(id);
      }
      throw err;
    }
  }

  // GET /api/investigations/{id}/hypotheses
  public async getHypotheses(id: string): Promise<Hypothesis[]> {
    if (this.shouldUseSimulator()) {
      return localSimulator.getHypotheses(id);
    }

    try {
      return await apiClient.request<Hypothesis[]>(`/api/investigations/${id}/hypotheses`);
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        return localSimulator.getHypotheses(id);
      }
      return [];
    }
  }

  // GET /api/investigations/{id}/events
  public async getEvents(id: string): Promise<InvestigationEvent[]> {
    if (this.shouldUseSimulator()) {
      return localSimulator.getEvents(id);
    }

    try {
      return await apiClient.request<InvestigationEvent[]>(`/api/investigations/${id}/events`);
    } catch (err) {
      if (apiClient.getConnectionState() === 'offline') {
        return localSimulator.getEvents(id);
      }
      throw err;
    }
  }

  // GET /api/investigations/{id}/report
  public async getReport(id: string): Promise<FinalReport | null> {
    if (this.shouldUseSimulator()) {
      return localSimulator.getReport(id);
    }

    try {
      return await apiClient.request<FinalReport>(`/api/investigations/${id}/report`);
    } catch (err: any) {
      // 404 or 204 or report-not-ready means report is pending
      if (err.status === 404 || err.status === 204) {
        return null;
      }
      if (apiClient.getConnectionState() === 'offline') {
        return localSimulator.getReport(id);
      }
      throw err;
    }
  }

  // POST /api/investigations/{id}/retry/{task_id}
  public async retryTask(id: string, taskId: string): Promise<Task> {
    if (this.shouldUseSimulator()) {
      const task = localSimulator.retryTask(id, taskId);
      if (!task) throw { message: 'Task not found', status: 404 };
      return task;
    }

    return await apiClient.request<Task>(`/api/investigations/${id}/retry/${taskId}`, {
      method: 'POST',
    });
  }

  // POST /api/investigations/{id}/cancel
  public async cancelInvestigation(id: string): Promise<{ status: string }> {
    if (this.shouldUseSimulator()) {
      localSimulator.cancelInvestigation(id);
      return { status: 'cancelled' };
    }

    return await apiClient.request<{ status: string }>(`/api/investigations/${id}/cancel`, {
      method: 'POST',
    });
  }

  // Subscribe to live events (SSE if live backend, or event emitter if simulator)
  public subscribeEventStream(
    investigationId: string,
    callbacks: {
      onEvent: (event: InvestigationEvent) => void;
      onError?: (error: any) => void;
      onConnect?: () => void;
    }
  ): () => void {
    if (this.shouldUseSimulator()) {
      callbacks.onConnect?.();
      return localSimulator.subscribeEvents(investigationId, callbacks.onEvent);
    }

    const baseUrl = getStoredApiBaseUrl();
    const streamUrl = `${baseUrl}/api/investigations/${investigationId}/events/stream`;

    try {
      const eventSource = new EventSource(streamUrl);

      eventSource.onopen = () => {
        callbacks.onConnect?.();
      };

      eventSource.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data);
          callbacks.onEvent(parsed);
        } catch (err) {
          console.warn('[ConsultOS SSE] Parse error:', err);
        }
      };

      eventSource.onerror = (err) => {
        callbacks.onError?.(err);
      };

      return () => {
        eventSource.close();
      };
    } catch (err) {
      callbacks.onError?.(err);
      // Fallback to simulator events if available
      return localSimulator.subscribeEvents(investigationId, callbacks.onEvent);
    }
  }
}

export const investigationsService = new InvestigationsService();

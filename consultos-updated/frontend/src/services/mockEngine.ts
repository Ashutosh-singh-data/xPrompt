import {
  Investigation,
  Task,
  Evidence,
  Hypothesis,
  InvestigationEvent,
  FinalReport,
} from '../types';
import {
  INITIAL_DEMO_INVESTIGATION,
  INITIAL_TASKS,
  INITIAL_EVIDENCE,
  INITIAL_HYPOTHESES,
  INITIAL_EVENTS,
  INITIAL_REPORT,
} from './mockData';

const STORAGE_KEY_INVESTIGATIONS = 'consultos_db_investigations';
const STORAGE_KEY_TASKS = 'consultos_db_tasks';
const STORAGE_KEY_EVIDENCE = 'consultos_db_evidence';
const STORAGE_KEY_HYPOTHESES = 'consultos_db_hypotheses';
const STORAGE_KEY_EVENTS = 'consultos_db_events';
const STORAGE_KEY_REPORTS = 'consultos_db_reports';

export class LocalSimulationEngine {
  private eventListeners: Map<string, Set<(event: InvestigationEvent) => void>> = new Map();
  private runningTimers: Map<string, NodeJS.Timeout[]> = new Map();

  constructor() {
    this.seedIfEmpty();
  }

  private seedIfEmpty() {
    if (!localStorage.getItem(STORAGE_KEY_INVESTIGATIONS)) {
      this.saveInvestigations([INITIAL_DEMO_INVESTIGATION]);
      this.saveTasks([INITIAL_DEMO_INVESTIGATION.id], INITIAL_TASKS);
      this.saveEvidence([INITIAL_DEMO_INVESTIGATION.id], INITIAL_EVIDENCE);
      this.saveHypotheses([INITIAL_DEMO_INVESTIGATION.id], INITIAL_HYPOTHESES);
      this.saveEvents([INITIAL_DEMO_INVESTIGATION.id], INITIAL_EVENTS);
      this.saveReport(INITIAL_DEMO_INVESTIGATION.id, INITIAL_REPORT);
    }
  }

  // --- Persistence Helpers ---
  public getInvestigations(): Investigation[] {
    const raw = localStorage.getItem(STORAGE_KEY_INVESTIGATIONS);
    return raw ? JSON.parse(raw) : [INITIAL_DEMO_INVESTIGATION];
  }

  private saveInvestigations(invs: Investigation[]) {
    localStorage.setItem(STORAGE_KEY_INVESTIGATIONS, JSON.stringify(invs));
  }

  public getInvestigationById(id: string): Investigation | null {
    const invs = this.getInvestigations();
    return invs.find((inv) => inv.id === id) || null;
  }

  public getTasks(investigationId: string): Task[] {
    const raw = localStorage.getItem(`${STORAGE_KEY_TASKS}_${investigationId}`);
    if (raw) return JSON.parse(raw);
    if (investigationId === INITIAL_DEMO_INVESTIGATION.id) return INITIAL_TASKS;
    return [];
  }

  private saveTasks(investigationIds: string[], tasks: Task[]) {
    investigationIds.forEach((id) => {
      localStorage.setItem(`${STORAGE_KEY_TASKS}_${id}`, JSON.stringify(tasks));
    });
  }

  public getEvidence(investigationId: string): Evidence[] {
    const raw = localStorage.getItem(`${STORAGE_KEY_EVIDENCE}_${investigationId}`);
    if (raw) return JSON.parse(raw);
    if (investigationId === INITIAL_DEMO_INVESTIGATION.id) return INITIAL_EVIDENCE;
    return [];
  }

  private saveEvidence(investigationIds: string[], evidence: Evidence[]) {
    investigationIds.forEach((id) => {
      localStorage.setItem(`${STORAGE_KEY_EVIDENCE}_${id}`, JSON.stringify(evidence));
    });
  }

  public getHypotheses(investigationId: string): Hypothesis[] {
    const raw = localStorage.getItem(`${STORAGE_KEY_HYPOTHESES}_${investigationId}`);
    if (raw) return JSON.parse(raw);
    if (investigationId === INITIAL_DEMO_INVESTIGATION.id) return INITIAL_HYPOTHESES;
    return [];
  }

  private saveHypotheses(investigationIds: string[], hypotheses: Hypothesis[]) {
    investigationIds.forEach((id) => {
      localStorage.setItem(`${STORAGE_KEY_HYPOTHESES}_${id}`, JSON.stringify(hypotheses));
    });
  }

  public getEvents(investigationId: string): InvestigationEvent[] {
    const raw = localStorage.getItem(`${STORAGE_KEY_EVENTS}_${investigationId}`);
    if (raw) return JSON.parse(raw);
    if (investigationId === INITIAL_DEMO_INVESTIGATION.id) return INITIAL_EVENTS;
    return [];
  }

  private saveEvents(investigationIds: string[], events: InvestigationEvent[]) {
    investigationIds.forEach((id) => {
      localStorage.setItem(`${STORAGE_KEY_EVENTS}_${id}`, JSON.stringify(events));
    });
  }

  public getReport(investigationId: string): FinalReport | null {
    const raw = localStorage.getItem(`${STORAGE_KEY_REPORTS}_${investigationId}`);
    if (raw) return JSON.parse(raw);
    if (investigationId === INITIAL_DEMO_INVESTIGATION.id) return INITIAL_REPORT;
    return null;
  }

  private saveReport(investigationId: string, report: FinalReport | null) {
    if (report) {
      localStorage.setItem(`${STORAGE_KEY_REPORTS}_${investigationId}`, JSON.stringify(report));
    } else {
      localStorage.removeItem(`${STORAGE_KEY_REPORTS}_${investigationId}`);
    }
  }

  // --- CRUD & Actions ---
  public createInvestigation(
    question: string,
    fileInfo?: { name: string; size: number }
  ): Investigation {
    const id = `inv_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const newInv: Investigation = {
      id,
      business_question: question,
      status: 'draft',
      current_plan_version: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      dataset_filename: fileInfo?.name || 'dataset.csv',
      dataset_size_bytes: fileInfo?.size || 1024 * 512,
      dataset_rows_count: Math.floor(10000 + Math.random() * 80000),
      tasks_count: 5,
      completed_tasks_count: 0,
    };

    const initialTasks: Task[] = [
      {
        id: `${id}_tsk_01`,
        investigation_id: id,
        title: 'Initial Dataset Profiling & Cohort Disaggregation',
        description: 'Examine primary transaction distributions, null rates, and segment by customer lifetime cohorts.',
        task_type: 'data_profiling',
        status: 'pending',
        dependencies: [],
        attempts: 0,
        plan_version: 1,
        is_replan_addition: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: `${id}_tsk_02`,
        investigation_id: id,
        title: 'Conversion Funnel Milestone Drop-off Audit',
        description: 'Trace step conversions through product views, add-to-carts, checkout initiation, and completion.',
        task_type: 'funnel_analysis',
        status: 'pending',
        dependencies: [`${id}_tsk_01`],
        attempts: 0,
        plan_version: 1,
        is_replan_addition: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: `${id}_tsk_03`,
        investigation_id: id,
        title: 'Channel Acquisition & Unit Economics Diagnostics',
        description: 'Analyze CAC escalation and return on ad spend across paid media channels.',
        task_type: 'channel_diagnostics',
        status: 'pending',
        dependencies: [`${id}_tsk_01`],
        attempts: 0,
        plan_version: 1,
        is_replan_addition: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: `${id}_tsk_04`,
        investigation_id: id,
        title: 'Supply Chain & Inventory Constraint Validation',
        description: 'Verify if fulfillment stockouts or shipping delivery delays influenced customer churn.',
        task_type: 'inventory_validation',
        status: 'pending',
        dependencies: [`${id}_tsk_01`],
        attempts: 0,
        plan_version: 1,
        is_replan_addition: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: `${id}_tsk_05`,
        investigation_id: id,
        title: 'Final Evidence Synthesis & Attribution Verification',
        description: 'Aggregate verified empirical evidence and synthesize root causes into actionable recommendations.',
        task_type: 'synthesis_verification',
        status: 'pending',
        dependencies: [`${id}_tsk_02`, `${id}_tsk_03`, `${id}_tsk_04`],
        attempts: 0,
        plan_version: 1,
        is_replan_addition: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    const initialHypotheses: Hypothesis[] = [
      {
        id: `${id}_hyp_01`,
        investigation_id: id,
        statement: 'Macro market friction or customer price elasticity caused broad conversion drop.',
        status: 'pending',
        supporting_evidence_ids: [],
        contradicting_evidence_ids: [],
        confidence: 0.5,
        created_at: new Date().toISOString(),
      },
      {
        id: `${id}_hyp_02`,
        investigation_id: id,
        statement: 'Technical or checkout failure in mobile channels degraded purchase completions.',
        status: 'pending',
        supporting_evidence_ids: [],
        contradicting_evidence_ids: [],
        confidence: 0.5,
        created_at: new Date().toISOString(),
      },
    ];

    const initialEvent: InvestigationEvent = {
      id: `evt_${Date.now()}_0`,
      investigation_id: id,
      event_type: 'plan_created',
      details: { plan_version: 1, tasks_count: initialTasks.length, business_question: question },
      created_at: new Date().toISOString(),
    };

    const invs = [newInv, ...this.getInvestigations()];
    this.saveInvestigations(invs);
    this.saveTasks([id], initialTasks);
    this.saveEvidence([id], []);
    this.saveHypotheses([id], initialHypotheses);
    this.saveEvents([id], [initialEvent]);
    this.saveReport(id, null);

    return newInv;
  }

  // --- Execution Simulation (Supports Replanning, Live Stream, Evidence Production) ---
  public runInvestigation(id: string): void {
    const inv = this.getInvestigationById(id);
    if (!inv || inv.status === 'running' || inv.status === 'completed') return;

    this.updateInvestigationStatus(id, 'running');
    this.emitEvent(id, {
      id: `evt_${Date.now()}_start`,
      investigation_id: id,
      event_type: 'investigation_started',
      details: { timestamp: new Date().toISOString() },
      created_at: new Date().toISOString(),
    });

    const tasks = this.getTasks(id);
    const timers: NodeJS.Timeout[] = [];

    // Step 1: Start Task 1
    const t1 = setTimeout(() => {
      this.updateTaskState(id, tasks[0].id, 'running', 0.8);
    }, 600);
    timers.push(t1);

    // Step 2: Complete Task 1 & Record Evidence 1
    const t2 = setTimeout(() => {
      const ev1: Evidence = {
        id: `ev_${Date.now()}_1`,
        investigation_id: id,
        task_id: tasks[0].id,
        source_type: 'cohort_profiler',
        source_reference: `${inv.dataset_filename}:rows_1-20000`,
        finding: 'Disaggregation reveals regular returning buyers remained stable, while new paid social acquisition dropped 31%.',
        units_or_period: 'Comparative monthly baseline',
        calculation: 'SUM(new_user_orders) / SUM(total_orders)',
        created_at: new Date().toISOString(),
      };
      this.addEvidence(id, ev1);
      this.updateTaskState(id, tasks[0].id, 'completed', 2.4, {
        summary: 'New customer drop confirmed at -31%. Returning customer retention steady.',
      });
      // Unlock Task 2, 3, 4
      this.updateTaskState(id, tasks[1].id, 'running', 1.2);
      this.updateTaskState(id, tasks[2].id, 'running', 1.5);
    }, 2800);
    timers.push(t2);

    // Step 3: Complete Task 3 (pricing/elasticity) -> Contradict Hypothesis 1 -> TRIGGER REPLANNING
    const t3 = setTimeout(() => {
      this.updateTaskState(id, tasks[2].id, 'completed', 3.1, {
        elasticity_score: 'No significant price sensitivity detected across product tiers.',
      });

      // Update Hypothesis 1
      const hyps = this.getHypotheses(id);
      if (hyps[0]) {
        hyps[0].status = 'contradicted';
        hyps[0].confidence = 0.1;
        this.saveHypotheses([id], hyps);
        this.emitEvent(id, {
          id: `evt_${Date.now()}_hyp1`,
          investigation_id: id,
          event_type: 'hypothesis_updated',
          details: { hypothesis_id: hyps[0].id, status: 'contradicted' },
          created_at: new Date().toISOString(),
        });
      }

      // REPLANNING EVENT: Bump plan version to 2 and inject deeper investigation tasks!
      this.updateInvestigationStatus(id, 'replanning');
      this.bumpPlanVersion(id, 2);

      const injectedTask1: Task = {
        id: `${id}_tsk_replan_gateway_logs`,
        investigation_id: id,
        title: 'Replan Task: Deep API Telemetry & 3DS2 Exception Audit',
        description: 'Injected during Plan v2 revision: Query low-level payment gateway error codes for mobile traffic.',
        task_type: 'gateway_telemetry',
        status: 'pending',
        dependencies: [tasks[1].id],
        attempts: 0,
        plan_version: 2,
        is_replan_addition: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const currentTasks = this.getTasks(id);
      currentTasks.splice(3, 0, injectedTask1);
      this.saveTasks([id], currentTasks);

      this.emitEvent(id, {
        id: `evt_${Date.now()}_replan`,
        investigation_id: id,
        event_type: 'replanning_triggered',
        details: {
          reason: 'Initial pricing hypothesis contradicted. Injected specialized mobile gateway audit task.',
          plan_version: 2,
          added_tasks: [injectedTask1.title],
        },
        created_at: new Date().toISOString(),
      });
    }, 5500);
    timers.push(t3);

    // Step 4: Complete Task 2 (checkout funnel)
    const t4 = setTimeout(() => {
      this.updateInvestigationStatus(id, 'running');

      const ev2: Evidence = {
        id: `ev_${Date.now()}_2`,
        investigation_id: id,
        task_id: tasks[1].id,
        source_type: 'checkout_funnel',
        source_reference: `${inv.dataset_filename}:session_events`,
        finding: 'Mobile Safari payment authorization rate fell from 98.4% to 81.2% following gateway update.',
        units_or_period: 'Daily time-series',
        calculation: 'COUNT(auth_success) / COUNT(payment_submits)',
        created_at: new Date().toISOString(),
      };
      this.addEvidence(id, ev2);
      this.updateTaskState(id, tasks[1].id, 'completed', 4.1, {
        mobile_drop_delta: '-17.2% on iOS mobile checkout',
      });

      // Start the newly injected replan task
      this.updateTaskState(id, `${id}_tsk_replan_gateway_logs`, 'running', 1.0);
    }, 7800);
    timers.push(t4);

    // Step 5: Complete Replan Task & Task 4 (inventory)
    const t5 = setTimeout(() => {
      const ev3: Evidence = {
        id: `ev_${Date.now()}_3`,
        investigation_id: id,
        task_id: `${id}_tsk_replan_gateway_logs`,
        source_type: 'gateway_raw_exceptions',
        source_reference: `${inv.dataset_filename}:gateway_exceptions`,
        finding: 'Identified 9,656 instances of ERR_3DS2_CHALLENGE_TIMEOUT blocked inside social in-app webviews.',
        units_or_period: 'Q3 Event Log',
        calculation: 'COUNT(ERR_3DS2_CHALLENGE_TIMEOUT)',
        created_at: new Date().toISOString(),
      };
      this.addEvidence(id, ev3);
      this.updateTaskState(id, `${id}_tsk_replan_gateway_logs`, 'completed', 3.8, {
        root_cause: '3DS2 authentication modal iframe sandboxing inside iOS WebView',
      });

      // Complete Task 4 (inventory)
      this.updateTaskState(id, tasks[3].id, 'completed', 2.9, {
        out_of_stock_pct: '2.1% (within standard limits)',
      });

      // Update Hypothesis 2 to supported
      const hyps = this.getHypotheses(id);
      const currentEvs = this.getEvidence(id);
      if (hyps[1]) {
        hyps[1].status = 'supported';
        hyps[1].confidence = 0.98;
        hyps[1].supporting_evidence_ids = currentEvs.map((e) => e.id);
        this.saveHypotheses([id], hyps);
        this.emitEvent(id, {
          id: `evt_${Date.now()}_hyp2`,
          investigation_id: id,
          event_type: 'hypothesis_updated',
          details: { hypothesis_id: hyps[1].id, status: 'supported' },
          created_at: new Date().toISOString(),
        });
      }

      // Start final synthesis task
      this.updateTaskState(id, tasks[4].id, 'running', 1.5);
    }, 10500);
    timers.push(t5);

    // Step 6: Complete Final Synthesis & Generate Report
    const t6 = setTimeout(() => {
      this.updateTaskState(id, tasks[4].id, 'completed', 4.5, {
        synthesis: 'High-confidence correlation verified between 3DS2 gateway timeout and $1.42M uncompleted orders.',
      });

      const report: FinalReport = {
        id: `rep_${id}`,
        investigation_id: id,
        business_question: inv.business_question,
        status: 'ready',
        executive_summary: `Investigation confirmed that revenue decline was caused by a payment processing regression in mobile in-app browsers, where 3DS2 challenge modals failed to render after the recent gateway revision. This resulted in approximately $1.42M in aborted customer transactions and $184K in wasted paid social ad traffic.`,
        methodology: 'Multi-stage autonomous causal graph analysis with dynamic hypothesis invalidation and replanning.',
        findings: [
          {
            title: 'Mobile 3DS2 Gateway Timeout Incompatibility',
            claim: 'Encountered 9,656 ERR_3DS2_CHALLENGE_TIMEOUT errors inside iOS webview sessions.',
            fact_type: 'observed_fact',
            evidence_ids: [],
            impact: '14,200 lost checkout conversions',
          },
          {
            title: 'Product Margin & Inventory Hypotheses Excluded',
            claim: 'Stockouts remained at nominal 2.1% and price elasticity showed no adverse shifting.',
            fact_type: 'observed_fact',
            evidence_ids: [],
            impact: 'Rules out merchandising failure',
          },
        ],
        calculations: [
          {
            metric: 'Aborted Transaction Value',
            formula: '14,200 lost orders * $100 AOV',
            result: '$1,420,000',
          },
          {
            metric: 'Squandered Acquisition Spend',
            formula: '12% paid social budget escalation directing traffic to broken flow',
            result: '$184,200',
          },
        ],
        recommendations: [
          'Deploy hotfix to use Native App Redirect or Apple Pay Web instead of embedded iframe for 3DS2 challenges.',
          'Temporarily throttle top paid social campaigns until mobile checkout success rate returns above 98%.',
          'Send personalized abandoned cart recovery incentives to affected users.',
        ],
        limitations: [
          'Dataset covers mobile and desktop sessions; does not include offline call-center orders.',
        ],
        unresolved_questions: [
          'Did any secondary fraud scoring rules compound the in-app timeout behavior?',
        ],
        execution_summary: {
          total_tasks: 6,
          completed_tasks: 6,
          failed_tasks: 0,
          plan_revisions: 2,
          total_duration_sec: 14.8,
          evidence_count: 3,
        },
        created_at: new Date().toISOString(),
      };

      this.saveReport(id, report);
      this.updateInvestigationStatus(id, 'completed');

      this.emitEvent(id, {
        id: `evt_${Date.now()}_rep`,
        investigation_id: id,
        event_type: 'report_generated',
        details: { report_id: report.id, status: 'ready' },
        created_at: new Date().toISOString(),
      });
    }, 13000);
    timers.push(t6);

    this.runningTimers.set(id, timers);
  }

  public cancelInvestigation(id: string): void {
    const timers = this.runningTimers.get(id);
    if (timers) {
      timers.forEach((t) => clearTimeout(t));
      this.runningTimers.delete(id);
    }
    this.updateInvestigationStatus(id, 'cancelled');
    this.emitEvent(id, {
      id: `evt_${Date.now()}_cancel`,
      investigation_id: id,
      event_type: 'investigation_cancelled',
      details: { reason: 'User initiated cancellation' },
      created_at: new Date().toISOString(),
    });
  }

  public retryTask(investigationId: string, taskId: string): Task | null {
    const tasks = this.getTasks(investigationId);
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return null;

    task.status = 'ready';
    task.attempts += 1;
    task.error = null;
    task.updated_at = new Date().toISOString();
    this.saveTasks([investigationId], tasks);

    this.emitEvent(investigationId, {
      id: `evt_${Date.now()}_retry`,
      investigation_id: investigationId,
      task_id: taskId,
      event_type: 'task_retried',
      details: { task_id: taskId, attempt: task.attempts },
      created_at: new Date().toISOString(),
    });

    // Simulate rerun of task
    setTimeout(() => {
      this.updateTaskState(investigationId, taskId, 'running', 1.0);
      setTimeout(() => {
        this.updateTaskState(investigationId, taskId, 'completed', 3.2, {
          recovered: true,
          notes: 'Task succeeded on retry attempt.',
        });
      }, 2500);
    }, 400);

    return task;
  }

  private updateInvestigationStatus(id: string, status: any) {
    const invs = this.getInvestigations();
    const inv = invs.find((i) => i.id === id);
    if (inv) {
      inv.status = status;
      inv.updated_at = new Date().toISOString();
      const currentTasks = this.getTasks(id);
      inv.tasks_count = currentTasks.length;
      inv.completed_tasks_count = currentTasks.filter((t) => t.status === 'completed').length;
      this.saveInvestigations(invs);
    }
  }

  private bumpPlanVersion(id: string, version: number) {
    const invs = this.getInvestigations();
    const inv = invs.find((i) => i.id === id);
    if (inv) {
      inv.current_plan_version = version;
      inv.updated_at = new Date().toISOString();
      this.saveInvestigations(invs);
    }
  }

  private updateTaskState(
    investigationId: string,
    taskId: string,
    status: any,
    duration?: number,
    result?: any
  ) {
    const tasks = this.getTasks(investigationId);
    const task = tasks.find((t) => t.id === taskId);
    if (task) {
      task.status = status;
      if (duration) task.duration = duration;
      if (result) task.result = result;
      task.updated_at = new Date().toISOString();
      this.saveTasks([investigationId], tasks);

      this.emitEvent(investigationId, {
        id: `evt_${Date.now()}_tsk_${taskId}`,
        investigation_id: investigationId,
        task_id: taskId,
        event_type: status === 'completed' ? 'task_completed' : status === 'running' ? 'task_started' : 'task_updated',
        details: { status, duration, result },
        created_at: new Date().toISOString(),
      });

      // Update investigation completed count
      const invs = this.getInvestigations();
      const inv = invs.find((i) => i.id === investigationId);
      if (inv) {
        inv.completed_tasks_count = tasks.filter((t) => t.status === 'completed').length;
        inv.tasks_count = tasks.length;
        this.saveInvestigations(invs);
      }
    }
  }

  private addEvidence(investigationId: string, ev: Evidence) {
    const all = this.getEvidence(investigationId);
    all.push(ev);
    this.saveEvidence([investigationId], all);

    this.emitEvent(investigationId, {
      id: `evt_${Date.now()}_ev_${ev.id}`,
      investigation_id: investigationId,
      task_id: ev.task_id,
      event_type: 'evidence_recorded',
      details: { evidence_id: ev.id, finding: ev.finding },
      created_at: new Date().toISOString(),
    });
  }

  private emitEvent(investigationId: string, event: InvestigationEvent) {
    const events = this.getEvents(investigationId);
    events.push(event);
    this.saveEvents([investigationId], events);

    const listeners = this.eventListeners.get(investigationId);
    if (listeners) {
      listeners.forEach((cb) => cb(event));
    }
  }

  public subscribeEvents(
    investigationId: string,
    callback: (event: InvestigationEvent) => void
  ): () => void {
    if (!this.eventListeners.has(investigationId)) {
      this.eventListeners.set(investigationId, new Set());
    }
    this.eventListeners.get(investigationId)!.add(callback);
    return () => {
      this.eventListeners.get(investigationId)?.delete(callback);
    };
  }
}

export const localSimulator = new LocalSimulationEngine();

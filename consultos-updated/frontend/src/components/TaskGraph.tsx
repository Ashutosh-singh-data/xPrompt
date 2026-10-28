import React, { useMemo, useState } from 'react';
import { Task } from '../types';
import { StatusBadge } from './StatusBadge';
import { formatDuration } from '../utils/formatters';
import { GitBranch, CornerDownRight, RefreshCw, ArrowRight, Loader2 } from 'lucide-react';

interface TaskGraphProps {
  tasks: Task[];
  onSelectTask: (task: Task) => void;
  onRetryTask?: (taskId: string) => void;
  selectedTaskId?: string | null;
}

interface GraphLevel {
  level: number;
  tasks: Task[];
}

export const TaskGraph: React.FC<TaskGraphProps> = ({
  tasks,
  onSelectTask,
  onRetryTask,
  selectedTaskId,
}) => {
  const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);

  // Topological sort / level grouping based on dependencies
  const levels: GraphLevel[] = useMemo(() => {
    if (!tasks || tasks.length === 0) return [];

    const taskMap = new Map<string, Task>();
    tasks.forEach((t) => taskMap.set(t.id, t));

    const taskLevels = new Map<string, number>();

    const getLevel = (taskId: string, visited: Set<string> = new Set()): number => {
      if (taskLevels.has(taskId)) return taskLevels.get(taskId)!;
      if (visited.has(taskId)) return 0; // cycle fallback
      visited.add(taskId);

      const task = taskMap.get(taskId);
      if (!task || !task.dependencies || task.dependencies.length === 0) {
        taskLevels.set(taskId, 0);
        return 0;
      }

      let maxDepLevel = -1;
      for (const depId of task.dependencies) {
        maxDepLevel = Math.max(maxDepLevel, getLevel(depId, new Set(visited)));
      }

      const calculatedLevel = maxDepLevel + 1;
      taskLevels.set(taskId, calculatedLevel);
      return calculatedLevel;
    };

    tasks.forEach((t) => getLevel(t.id));

    const grouped: Map<number, Task[]> = new Map();
    tasks.forEach((t) => {
      const lvl = taskLevels.get(t.id) || 0;
      if (!grouped.has(lvl)) grouped.set(lvl, []);
      grouped.get(lvl)!.push(t);
    });

    const result: GraphLevel[] = [];
    const sortedLevels = Array.from(grouped.keys()).sort((a, b) => a - b);
    sortedLevels.forEach((lvl) => {
      result.push({ level: lvl, tasks: grouped.get(lvl)! });
    });

    return result;
  }, [tasks]);

  // Determine if a task is a dependency or dependent of hovered task
  const hoveredTask = useMemo(
    () => tasks.find((t) => t.id === hoveredTaskId),
    [tasks, hoveredTaskId]
  );

  const relatedTaskIds = useMemo(() => {
    if (!hoveredTask) return new Set<string>();
    const set = new Set<string>();
    set.add(hoveredTask.id);
    (hoveredTask.dependencies || []).forEach((d) => set.add(d));
    tasks.forEach((t) => {
      if ((t.dependencies || []).includes(hoveredTask.id)) {
        set.add(t.id);
      }
    });
    return set;
  }, [hoveredTask, tasks]);

  if (tasks.length === 0) {
    return (
      <div className="px-8 py-14 text-center text-muted border border-dashed border-line-strong rounded-xl bg-surface text-sm">
        No task graph yet. Start the investigation to generate analytical tasks.
      </div>
    );
  }

  return (
    <div className="card p-6 overflow-x-auto">
      <div className="flex items-start gap-5 min-w-[700px]">
        {levels.map((lvlGroup, colIdx) => (
          <div key={lvlGroup.level} className="flex-1 flex flex-col gap-4 min-w-[210px]">
            {/* Phase header */}
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div className="flex items-center gap-2 text-[13px] font-semibold text-ink">
                <span>Phase {colIdx + 1}</span>
                {colIdx < levels.length - 1 && <ArrowRight size={13} className="text-faint" />}
              </div>
              <span className="text-xs text-muted">
                {lvlGroup.tasks.length} {lvlGroup.tasks.length === 1 ? 'task' : 'tasks'}
              </span>
            </div>

            {/* Task nodes */}
            <div className="flex flex-col gap-4">
              {lvlGroup.tasks.map((task) => {
                const isSelected = selectedTaskId === task.id;
                const isRelated = relatedTaskIds.has(task.id);
                const isFailed = task.status === 'failed';
                const isRunning = task.status === 'running';
                const isReplan = task.is_replan_addition || (task.plan_version && task.plan_version > 1);

                return (
                  <div
                    key={task.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => onSelectTask(task)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onSelectTask(task);
                      }
                    }}
                    onMouseEnter={() => setHoveredTaskId(task.id)}
                    onMouseLeave={() => setHoveredTaskId(null)}
                    className={`group relative text-left p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-brand-50/70 border-brand-600 ring-2 ring-brand-600/15'
                        : isFailed
                        ? 'bg-rose-50/60 border-rose-200 hover:border-rose-300'
                        : isRunning
                        ? 'bg-brand-50/50 border-brand-200 shadow-card'
                        : isReplan
                        ? 'bg-amber-50/60 border-amber-200 hover:border-amber-300'
                        : isRelated && hoveredTaskId
                        ? 'bg-subtle border-brand-200 shadow-card'
                        : 'bg-surface border-line shadow-card hover:border-line-strong hover:shadow-raised'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <span className="text-xs text-muted truncate">{task.task_type}</span>
                      {isReplan && (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-800 bg-amber-100 border border-amber-200 px-2 py-0.5 rounded-full shrink-0">
                          <GitBranch size={11} />
                          Replan v{task.plan_version || 2}
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm font-semibold text-ink line-clamp-2 mb-3 leading-snug group-hover:text-brand-700 transition-colors">
                      {task.title}
                    </h4>

                    {task.dependencies && task.dependencies.length > 0 && (
                      <div className="flex items-center gap-1.5 text-xs text-muted mb-3">
                        <CornerDownRight size={12} className="text-faint" />
                        <span>Depends on {task.dependencies.length}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-3 border-t border-line gap-2">
                      <StatusBadge type="task" status={task.status} size="sm" />

                      <div className="flex items-center gap-2">
                        {task.duration !== undefined && (
                          <span className="text-xs text-muted tabular-nums">
                            {formatDuration(task.duration)}
                          </span>
                        )}

                        {isFailed && onRetryTask && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onRetryTask(task.id);
                            }}
                            className="btn btn-sm btn-danger-soft h-7 px-2.5 text-xs"
                          >
                            <RefreshCw size={11} />
                            Retry
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

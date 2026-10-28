import React from 'react';
import { Task } from '../types';
import { StatusBadge } from './StatusBadge';
import { formatDuration } from '../utils/formatters';
import { GitBranch, RefreshCw, AlertTriangle } from 'lucide-react';

interface TaskListProps {
  tasks: Task[];
  onSelectTask: (task: Task) => void;
  onRetryTask?: (taskId: string) => void;
  selectedTaskId?: string | null;
}

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  onSelectTask,
  onRetryTask,
  selectedTaskId,
}) => {
  if (tasks.length === 0) {
    return (
      <div className="px-8 py-14 text-center text-muted border border-dashed border-line-strong rounded-xl bg-surface text-sm">
        No analytical tasks available.
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="table-head border-b border-line">
              <th className="py-3.5 px-6 font-semibold">Task</th>
              <th className="py-3.5 px-4 font-semibold">Type</th>
              <th className="py-3.5 px-4 font-semibold">Status</th>
              <th className="py-3.5 px-4 font-semibold">Depends on</th>
              <th className="py-3.5 px-4 font-semibold">Duration</th>
              <th className="py-3.5 px-6 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {tasks.map((task) => {
              const isSelected = selectedTaskId === task.id;
              const isFailed = task.status === 'failed';
              const isBlocked = task.status === 'blocked';
              const isReplan = task.is_replan_addition || (task.plan_version && task.plan_version > 1);

              return (
                <tr
                  key={task.id}
                  onClick={() => onSelectTask(task)}
                  className={`hover:bg-subtle transition-colors cursor-pointer ${
                    isSelected ? 'bg-brand-50/60' : ''
                  }`}
                >
                  <td className="py-4 px-6 max-w-xs md:max-w-md">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-medium text-ink">{task.title}</span>
                        {isReplan && (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                            <GitBranch size={11} />
                            Replan v{task.plan_version || 2}
                          </span>
                        )}
                      </div>
                      <p className="text-[13px] text-muted line-clamp-1">{task.description}</p>
                      {isFailed && task.error && (
                        <div className="mt-1.5 flex items-center gap-1.5 text-rose-700 text-[13px]">
                          <AlertTriangle size={13} className="shrink-0" />
                          <span className="truncate">{task.error}</span>
                        </div>
                      )}
                      {isBlocked && task.blocked_reason && (
                        <div className="mt-1.5 text-amber-800 text-[13px]">
                          Blocked: {task.blocked_reason}
                        </div>
                      )}
                    </div>
                  </td>

                  <td className="py-4 px-4 text-[13px] text-muted whitespace-nowrap">
                    {task.task_type}
                  </td>

                  <td className="py-4 px-4 whitespace-nowrap">
                    <StatusBadge type="task" status={task.status} size="sm" />
                  </td>

                  <td className="py-4 px-4 text-[13px] text-muted whitespace-nowrap">
                    {task.dependencies && task.dependencies.length > 0 ? (
                      <span title={task.dependencies.join(', ')}>
                        {task.dependencies.length} task{task.dependencies.length > 1 ? 's' : ''}
                      </span>
                    ) : (
                      <span className="text-faint">None</span>
                    )}
                  </td>

                  <td className="py-4 px-4 text-[13px] text-muted whitespace-nowrap tabular-nums">
                    <div>{formatDuration(task.duration)}</div>
                    {task.attempts > 1 && (
                      <div className="text-xs text-faint">{task.attempts} attempts</div>
                    )}
                  </td>

                  <td className="py-4 px-6 text-right whitespace-nowrap">
                    <div className="flex items-center justify-end gap-2">
                      {isFailed && onRetryTask && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onRetryTask(task.id);
                          }}
                          className="btn btn-sm btn-danger-soft"
                        >
                          <RefreshCw size={12} />
                          Retry
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectTask(task);
                        }}
                        className="btn btn-sm btn-secondary"
                      >
                        Inspect
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

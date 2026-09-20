import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { differenceInDays, parseISO, addDays, format, min, max, isValid } from 'date-fns';
import api from '../lib/api';

export default function ProjectTasks() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [progressInput, setProgressInput] = useState<number>(0);
  const [updateError, setUpdateError] = useState<string>('');

  const { data: schedule, isLoading } = useQuery({
    queryKey: ['schedule', id],
    queryFn: async () => {
      const res = await api.get(`/api/projects/${id}/schedule`);
      return res.data;
    }
  });

  const { data: tasks } = useQuery({
    queryKey: ['tasks', id],
    queryFn: async () => {
      const res = await api.get(`/api/projects/${id}/tasks`);
      return res.data;
    }
  });

  const progressMutation = useMutation({
    mutationFn: async ({ taskId, progress }: { taskId: number, progress: number }) => {
      return api.post(`/api/tasks/${taskId}/progress`, { progress });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', id] });
      queryClient.invalidateQueries({ queryKey: ['schedule', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', id] });
      queryClient.invalidateQueries({ queryKey: ['alerts', id] });
      queryClient.invalidateQueries({ queryKey: ['issues', id] });
      setSelectedTask((prev: any) => ({ ...prev, progress: progressInput }));
      setUpdateError('');
    },
    onError: (err: any) => {
      setUpdateError(err.response?.data?.detail || 'Failed to update progress');
    }
  });

  const statusMutation = useMutation({
    mutationFn: async ({ taskId, status }: { taskId: number, status: string }) => {
      return api.post(`/api/tasks/${taskId}/status`, { status });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', id] });
      queryClient.invalidateQueries({ queryKey: ['schedule', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', id] });
      queryClient.invalidateQueries({ queryKey: ['alerts', id] });
      queryClient.invalidateQueries({ queryKey: ['issues', id] });
      setSelectedTask((prev: any) => ({ ...prev, status: variables.status }));
      setUpdateError('');
    },
    onError: (err: any) => {
      setUpdateError(err.response?.data?.detail || 'Failed to update status');
    }
  });

  if (isLoading) return <div className="p-8 text-slate-500">Loading schedule...</div>;

  // Build timeline scale
  let minDate = new Date();
  let maxDate = new Date();
  
  if (schedule?.tasks?.length > 0) {
    const startDates = schedule.tasks.map((t: any) => parseISO(t.early_start)).filter(isValid);
    const endDates = schedule.tasks.map((t: any) => parseISO(t.early_finish)).filter(isValid);
    if (startDates.length > 0) minDate = min(startDates);
    if (endDates.length > 0) maxDate = max(endDates);
  }
  
  const totalDays = Math.max(10, differenceInDays(maxDate, minDate) + 4);
  const startDate = minDate;

  // Merge task progress from /tasks into schedule tasks for display
  const tasksDict = tasks?.reduce((acc: any, t: any) => { acc[t.id] = t; return acc; }, {}) || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/projects/${id}`} className="text-slate-400 hover:text-slate-900">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h2 className="text-2xl font-bold text-slate-900">Tasks & Schedule</h2>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col">
        <div className="overflow-x-auto">
          <div className="min-w-[800px]">
            {/* Header */}
            <div className="flex border-b border-slate-200 bg-slate-50">
              <div className="w-1/3 shrink-0 p-3 font-semibold text-slate-700 text-sm border-r border-slate-200">Task Name</div>
              <div className="flex-1 relative h-10">
                {/* Basic Timeline scale (e.g. 1 column per day) */}
                <div className="absolute inset-0 flex text-[10px] text-slate-400">
                  {Array.from({ length: totalDays }).map((_, i) => {
                    const d = addDays(startDate, i);
                    return (
                      <div key={i} className="flex-1 border-r border-slate-100 flex items-end pb-1 justify-center relative">
                        {i % 3 === 0 && <span className="absolute -top-1">{format(d, 'MMM d')}</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Rows */}
            <div className="divide-y divide-slate-100">
              {schedule?.tasks.map((t: any) => {
                const fullTask = tasksDict[t.id];
                const startOff = differenceInDays(parseISO(t.early_start), startDate);
                const dur = differenceInDays(parseISO(t.early_finish), parseISO(t.early_start));
                const leftPct = Math.max(0, (startOff / totalDays) * 100);
                const widthPct = Math.max(1, (dur / totalDays) * 100);
                const isDelayed = fullTask?.delay_days > 0;
                
                return (
                  <div key={t.id} className="flex hover:bg-slate-50 transition-colors" onClick={() => { setSelectedTask(fullTask); setProgressInput(fullTask?.progress || 0); setUpdateError(''); }}>
                    {/* WBS Side */}
                    <div className="w-1/3 shrink-0 p-3 flex items-center justify-between border-r border-slate-200 cursor-pointer">
                      <div className="flex items-center gap-2 truncate">
                        <div className={`w-2 h-2 rounded-full ${t.is_critical ? 'bg-red-500' : 'bg-slate-300'}`} title={t.is_critical ? 'Critical Path' : ''} />
                        <span className="text-sm font-medium text-slate-800 truncate">{t.name}</span>
                      </div>
                      <div className="flex gap-2 items-center text-xs">
                        {fullTask && <span className="text-slate-500">{fullTask.progress}%</span>}
                        {isDelayed && (
                          <div title={`Delayed by ${fullTask.delay_days} days`}>
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          </div>
                        )}
                      </div>
                    </div>
                    {/* Gantt Side */}
                    <div className="flex-1 relative h-12 py-2 group">
                       <div className="absolute inset-0 flex">
                        {Array.from({ length: totalDays }).map((_, i) => (
                          <div key={i} className="flex-1 border-r border-slate-50" />
                        ))}
                      </div>
                      {/* Planned Date Bar */}
                      <div 
                        className="absolute h-3 rounded-sm opacity-50 bg-slate-300 pointer-events-none"
                        style={{ 
                          left: `${Math.max(0, (differenceInDays(parseISO(t.late_start || t.early_start), startDate) / totalDays) * 100)}%`, 
                          width: `${Math.max(1, (differenceInDays(parseISO(t.late_finish || t.early_finish), parseISO(t.late_start || t.early_start)) / totalDays) * 100)}%`,
                          top: '20px'
                        }}
                      />
                      {/* Forecast Date Bar */}
                      <div 
                        className={`absolute h-8 rounded-sm shadow-sm flex items-center px-2 overflow-hidden text-xs text-white font-medium ${t.is_critical ? 'bg-red-500' : 'bg-blue-500'} ${isDelayed ? 'ring-2 ring-red-300 ring-offset-1' : ''}`}
                        style={{ left: `${leftPct}%`, width: `${widthPct}%`, top: '4px' }}
                      >
                         <div 
                           className="absolute left-0 top-0 bottom-0 bg-black/20" 
                           style={{ width: `${fullTask?.progress || 0}%` }} 
                         />
                         <span className="relative z-10 truncate">{t.name}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-4">{selectedTask.name}</h3>
            
            {updateError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm flex items-start gap-2">
                <AlertCircle className="h-5 w-5 shrink-0" />
                <span>{updateError}</span>
              </div>
            )}
            
            <div className="space-y-3 text-sm mb-6">
              <div className="flex justify-between items-center">
                <span className="font-medium">Status:</span>
                <select 
                  value={selectedTask.status}
                  onChange={(e) => statusMutation.mutate({ taskId: selectedTask.id, status: e.target.value })}
                  className="px-2 py-1 border border-slate-300 rounded text-sm disabled:opacity-50"
                  disabled={statusMutation.isPending}
                >
                  <option value="NOT_STARTED">Not Started</option>
                  <option value="ASSIGNED">Assigned</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="BLOCKED">Blocked</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>
              <p><span className="font-medium">Progress:</span> {selectedTask.progress}%</p>
              <p><span className="font-medium text-slate-500">Planned Start:</span> {selectedTask.planned_start}</p>
              <p><span className="font-medium text-slate-900">Forecast End:</span> {selectedTask.forecast_end}</p>
              {selectedTask.delay_days > 0 && (
                <p><span className="font-medium text-red-600">Delay:</span> +{selectedTask.delay_days} days</p>
              )}
              <p><span className="font-medium">Critical:</span> {selectedTask.is_critical ? 'Yes' : 'No'}</p>
            </div>
            
            <div className="border-t pt-4">
              <h4 className="font-medium text-sm mb-2">Update Progress</h4>
              <div className="flex gap-2 items-center">
                <input 
                  type="number" 
                  min="0" 
                  max="100" 
                  value={progressInput}
                  onChange={(e) => setProgressInput(Number(e.target.value))}
                  className="w-20 px-3 py-1 border border-slate-300 rounded text-sm"
                />
                <span className="text-sm">%</span>
                <button 
                  onClick={() => progressMutation.mutate({ taskId: selectedTask.id, progress: progressInput })} 
                  className="ml-auto px-3 py-1 bg-amber-600 text-white rounded text-sm hover:bg-amber-700 disabled:opacity-50"
                  disabled={progressMutation.isPending}
                >
                  Update
                </button>
              </div>
            </div>
            
            <div className="mt-6 text-right">
              <button onClick={() => setSelectedTask(null)} className="px-4 py-2 bg-slate-200 text-slate-800 rounded text-sm font-medium hover:bg-slate-300">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { Activity, AlertOctagon, AlertTriangle, Calendar, CheckCircle2, Clock, LayoutList, Sparkles } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '../lib/api';

const getHealthBadge = (health: string, reason: string) => {
  if (health === 'RED') {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertOctagon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Critical Status (RED)</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{reason || "Project is experiencing significant delays or critical issues."}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  if (health === 'AMBER') {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-amber-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-amber-800">Warning Status (AMBER)</h3>
            <div className="mt-2 text-sm text-amber-700">
              <p>{reason || "Project has minor delays or open issues."}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="bg-green-50 border border-green-200 rounded-md p-4">
      <div className="flex">
        <CheckCircle2 className="h-5 w-5 text-green-400" />
        <div className="ml-3">
          <h3 className="text-sm font-medium text-green-800">Healthy (GREEN)</h3>
          <div className="mt-2 text-sm text-green-700">
            <p>Project is on track.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function ProjectDashboard() {
  const { id } = useParams();

  const { data: dash, isLoading, error } = useQuery({
    queryKey: ['dashboard', id],
    queryFn: async () => {
      const res = await api.get(`/api/projects/${id}/dashboard`);
      return res.data;
    }
  });

  const aiMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/api/projects/${id}/ai-summary`);
      return res.data;
    }
  });

  if (isLoading) return (
    <div className="flex justify-center items-center h-64 text-slate-500">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mr-3"></div>
      Loading dashboard...
    </div>
  );
  if (error || !dash) return (
    <div className="p-8 text-center">
      <div className="inline-flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
        <AlertOctagon className="h-5 w-5" />
        Failed to load dashboard. Please try again.
      </div>
    </div>
  );

  const chartData = [
    { name: 'Completed', value: dash.progress.completed, color: '#10b981' },
    { name: 'In Progress', value: dash.progress.in_progress, color: '#3b82f6' },
    { name: 'Blocked', value: dash.progress.blocked, color: '#ef4444' },
    { name: 'Not Started', value: dash.progress.not_started, color: '#94a3b8' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">{dash.project.name}</h2>
          <div className="mt-1 flex items-center gap-4 text-sm text-slate-500">
            <span className="flex items-center gap-1"><Calendar className="h-4 w-4" /> Planned: {dash.schedule.planned_completion}</span>
            <span className={`flex items-center gap-1 font-medium ${dash.schedule.delay_days > 0 ? 'text-red-600' : 'text-slate-600'}`}>
              <Clock className="h-4 w-4" /> Forecast: {dash.schedule.forecast_completion} 
              {dash.schedule.delay_days > 0 && ` (+${dash.schedule.delay_days}d)`}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <Link 
            to={`/projects/${id}/tasks`}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
          >
            <LayoutList className="h-4 w-4" />
            Tasks & Schedule
          </Link>
          <Link 
            to={`/projects/${id}/change-requests`}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
          >
            Change Requests
          </Link>
          <Link 
            to={`/projects/${id}/audit-logs`}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
          >
            Audit Logs
          </Link>
        </div>
      </div>

      {getHealthBadge(dash.health.status, dash.health.reason)}

      {/* AI Analysis Section */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-lg p-6 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-indigo-900 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-500" />
            AI Project Analysis
          </h3>
          <button 
            onClick={() => aiMutation.mutate()}
            disabled={aiMutation.isPending}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
          >
            {aiMutation.isPending ? 'Analyzing...' : 'Analyze Project'}
          </button>
        </div>

        {aiMutation.isPending && (
          <div className="flex justify-center items-center h-24 text-indigo-500 text-sm">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600 mr-2"></div>
            Analyzing current project state...
          </div>
        )}

        {aiMutation.isError && (
          <div className="bg-red-50 text-red-700 p-4 rounded border border-red-200 text-sm">
            <p className="font-semibold">Unable to generate analysis.</p>
            <p>{(aiMutation.error as any)?.response?.data?.detail || 'Please try again later.'}</p>
          </div>
        )}

        {aiMutation.isSuccess && aiMutation.data && (
          <div className="space-y-4 text-sm text-indigo-950">
            <div>
              <h4 className="font-semibold mb-1">Summary</h4>
              <p>{aiMutation.data.summary}</p>
            </div>
            
            {aiMutation.data.risks?.length > 0 && (
              <div>
                <h4 className="font-semibold mb-1">Key Risks</h4>
                <ul className="list-disc pl-5 space-y-1">
                  {aiMutation.data.risks.map((r: string, i: number) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
            
            <div>
              <h4 className="font-semibold mb-1">Impact</h4>
              <p>{aiMutation.data.impact}</p>
            </div>
            
            {aiMutation.data.recommended_attention?.length > 0 && (
              <div>
                <h4 className="font-semibold mb-1">Recommended Attention</h4>
                <ul className="list-disc pl-5 space-y-1">
                  {aiMutation.data.recommended_attention.map((r: string, i: number) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-col justify-center items-center">
          <span className="text-slate-500 text-sm font-medium">Overall Progress</span>
          <span className="text-3xl font-bold text-slate-900 mt-2">{dash.progress.overall}%</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-col justify-center items-center">
          <span className="text-slate-500 text-sm font-medium">Completed</span>
          <span className="text-3xl font-bold text-green-600 mt-2">{dash.progress.completed}</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-col justify-center items-center">
          <span className="text-slate-500 text-sm font-medium">In Progress</span>
          <span className="text-3xl font-bold text-blue-600 mt-2">{dash.progress.in_progress}</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-col justify-center items-center">
          <span className="text-slate-500 text-sm font-medium">Blocked</span>
          <span className="text-3xl font-bold text-red-600 mt-2">{dash.progress.blocked}</span>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-col justify-center items-center">
          <span className="text-slate-500 text-sm font-medium">Open Issues</span>
          <span className="text-3xl font-bold text-amber-600 mt-2">{dash.issues.open}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Progress Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 lg:col-span-1">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-slate-400" />
            Task Status
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 0, left: 30, bottom: 0 }}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} />
                <Tooltip cursor={{fill: 'transparent'}} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Critical Path & Alerts */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 lg:col-span-2 space-y-6">
          <div>
            <h3 className="font-semibold text-slate-900 mb-4">Active Alerts</h3>
            {dash.alerts && dash.alerts.length > 0 ? (
              <div className="space-y-3">
                {dash.alerts.map((alert: any) => (
                  <div key={alert.id} className="flex items-start gap-3 p-3 rounded-md bg-slate-50 border border-slate-100">
                    {alert.severity === 'CRITICAL' ? (
                      <AlertOctagon className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="font-medium text-sm text-slate-900">{alert.message}</p>
                      <p className="text-xs text-slate-500 mt-1">{alert.type}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">No active alerts.</p>
            )}
          </div>

          <div>
            <h3 className="font-semibold text-slate-900 mb-4">Critical Path</h3>
            <div className="flex flex-wrap items-center gap-2">
              {dash.critical_path.map((taskName: string, i: number) => (
                <div key={i} className="flex items-center">
                  <span className="px-3 py-1 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold rounded-md">
                    {taskName}
                  </span>
                  {i < dash.critical_path.length - 1 && (
                    <ArrowRight className="h-4 w-4 text-slate-400 mx-2" />
                  )}
                </div>
              ))}
              {dash.critical_path.length === 0 && (
                <span className="text-sm text-slate-500">Critical path not available.</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const ArrowRight = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
);

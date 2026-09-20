import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Building2, Calendar, AlertTriangle, ArrowRight } from 'lucide-react';
import api from '../lib/api';

interface Project {
  id: number;
  name: string;
  status: string;
  health: 'GREEN' | 'AMBER' | 'RED';
  baseline_end: string;
  forecast_end: string;
  delay_days: number;
}

const getHealthColor = (health: string) => {
  switch (health) {
    case 'GREEN': return 'bg-green-100 text-green-800 border-green-200';
    case 'AMBER': return 'bg-amber-100 text-amber-800 border-amber-200';
    case 'RED': return 'bg-red-100 text-red-800 border-red-200';
    default: return 'bg-slate-100 text-slate-800 border-slate-200';
  }
};

export default function Projects() {
  const navigate = useNavigate();
  
  const { data: projects, isLoading, error } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await api.get('/api/projects');
      return res.data;
    }
  });

  if (isLoading) return (
    <div className="flex justify-center items-center h-64 text-slate-500">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mr-3"></div>
      Loading projects...
    </div>
  );
  if (error) return (
    <div className="p-8 text-center">
      <div className="inline-flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
        <AlertTriangle className="h-5 w-5" />
        Failed to load projects. Please try again.
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-900">Projects</h2>
        <button className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
          New Project
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects?.map(project => (
          <div 
            key={project.id} 
            className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => navigate(`/projects/${project.id}`)}
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-slate-400" />
                  <h3 className="font-semibold text-lg text-slate-900">{project.name}</h3>
                </div>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getHealthColor(project.health)}`}>
                  {project.health}
                </span>
              </div>
              
              <div className="space-y-3 text-sm text-slate-600">
                <div className="flex items-center justify-between">
                  <span>Status:</span>
                  <span className="font-medium text-slate-900">{project.status}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1"><Calendar className="h-4 w-4" /> Planned:</span>
                  <span>{project.baseline_end || 'Not set'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1"><AlertTriangle className="h-4 w-4" /> Forecast:</span>
                  <span className={project.delay_days > 0 ? 'text-red-600 font-medium' : ''}>
                    {project.forecast_end || 'Not set'}
                  </span>
                </div>
                {project.delay_days > 0 && (
                  <div className="pt-2 mt-2 border-t border-slate-100 flex justify-end">
                    <span className="text-red-600 font-semibold text-xs bg-red-50 px-2 py-1 rounded">
                      +{project.delay_days} days delay
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="bg-slate-50 px-6 py-3 border-t border-slate-200 flex justify-end">
              <span className="text-amber-600 text-sm font-medium flex items-center gap-1 hover:text-amber-700">
                View Dashboard <ArrowRight className="h-4 w-4" />
              </span>
            </div>
          </div>
        ))}
      </div>
      
      {projects?.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200 shadow-sm">
          <Building2 className="mx-auto h-12 w-12 text-slate-300 mb-3" />
          <h3 className="text-lg font-medium text-slate-900">No projects</h3>
          <p className="mt-1 text-slate-500">Get started by creating a new project.</p>
        </div>
      )}
    </div>
  );
}

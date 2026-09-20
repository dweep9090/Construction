import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Plus } from 'lucide-react';
import api from '../lib/api';
import { getCurrentUser } from '../utils/auth';

interface ChangeRequest {
  id: number;
  title: string;
  description: string;
  reason: string;
  impact_days: number;
  status: string;
  created_by: number;
}

export default function ChangeRequests() {
  const { id } = useParams();
  const [requests, setRequests] = useState<ChangeRequest[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [reason, setReason] = useState('');
  const [impactDays, setImpactDays] = useState(0);
  const [loading, setLoading] = useState(false);
  const user = getCurrentUser();

  const fetchRequests = () => {
    api.get(`/api/projects/${id}/change-requests`)
      .then(res => setRequests(res.data))
      .catch(console.error);
  };

  useEffect(() => {
    fetchRequests();
  }, [id]);

  const handleApprove = (crId: number) => {
    api.post(`/api/change-requests/${crId}/approve`)
      .then(() => fetchRequests())
      .catch(console.error);
  };

  const handleReject = (crId: number) => {
    api.post(`/api/change-requests/${crId}/reject`)
      .then(() => fetchRequests())
      .catch(console.error);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post(`/api/projects/${id}/change-requests`, {
        title,
        description,
        reason,
        impact_days: impactDays
      });
      setShowForm(false);
      setTitle('');
      setDescription('');
      setReason('');
      setImpactDays(0);
      fetchRequests();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const canCreate = user?.role === 'PROJECT_MANAGER' || user?.role === 'PROJECT_DIRECTOR';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Change Requests</h2>
        {canCreate && !showForm && (
          <button 
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Change Request
          </button>
        )}
      </div>

      {showForm && (
        <div className="bg-white shadow sm:rounded-md p-6 border border-slate-200">
          <h3 className="text-lg font-medium mb-4">Submit a New Change Request</h3>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-slate-700">Title</label>
              <input type="text" required value={title} onChange={e => setTitle(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Description</label>
              <textarea required value={description} onChange={e => setDescription(e.target.value)} rows={3} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Reason / Justification</label>
              <input type="text" required value={reason} onChange={e => setReason(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Impact Days (Delay)</label>
              <input type="number" required min="0" value={impactDays} onChange={e => setImpactDays(Number(e.target.value))} className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm" />
            </div>
            <div className="flex gap-2 justify-end pt-2">
              <button type="button" onClick={() => setShowForm(false)} className="bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 px-4 py-2 rounded-md text-sm font-medium">Cancel</button>
              <button type="submit" disabled={loading} className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50">
                {loading ? 'Submitting...' : 'Submit Request'}
              </button>
            </div>
          </form>
        </div>
      )}
      
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {requests.map((req) => (
            <li key={req.id} className="px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">{req.title}</h3>
                <p className="text-gray-500 text-sm mt-1">{req.description}</p>
                <div className="mt-2 text-sm text-gray-500">
                  <span className="font-semibold mr-4">Impact: {req.impact_days} days</span>
                  <span className="font-semibold">Reason: {req.reason}</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span className={`px-2 py-1 text-xs font-semibold rounded-full
                  ${req.status === 'APPROVED' ? 'bg-green-100 text-green-800' : 
                    req.status === 'REJECTED' ? 'bg-red-100 text-red-800' : 
                    'bg-yellow-100 text-yellow-800'}`}>
                  {req.status}
                </span>
                
                {user?.role === 'PROJECT_DIRECTOR' && req.status === 'SUBMITTED' && (
                  <div className="flex gap-2 mt-2">
                    <button onClick={() => handleApprove(req.id)} className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium">Approve</button>
                    <button onClick={() => handleReject(req.id)} className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium">Reject</button>
                  </div>
                )}
              </div>
            </li>
          ))}
          {requests.length === 0 && (
            <li className="px-6 py-4 text-center text-gray-500">No change requests found.</li>
          )}
        </ul>
      </div>
    </div>
  );
}

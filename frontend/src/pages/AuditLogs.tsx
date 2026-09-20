import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../lib/api';

interface AuditLog {
  id: number;
  action: string;
  entity: string;
  entity_id: number;
  previous_value: string;
  new_value: string;
  timestamp: string;
  role: string;
}

export default function AuditLogs() {
  const { id } = useParams();
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    api.get(`/api/projects/${id}/audit-logs`)
      .then(res => setLogs(res.data))
      .catch(console.error);
  }, [id]);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Audit Logs</h2>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {logs.map((log) => (
            <li key={log.id} className="px-6 py-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  <span className="font-bold text-amber-600">{log.action}</span> on <span className="font-semibold">{log.entity}</span> (ID: {log.entity_id})
                </p>
                <div className="mt-1 flex flex-col text-sm text-gray-500">
                  {log.previous_value && <span>From: {log.previous_value}</span>}
                  {log.new_value && <span>To: {log.new_value}</span>}
                </div>
              </div>
              <div className="text-right text-sm text-gray-500">
                <p>{new Date(log.timestamp).toLocaleString()}</p>
                <p className="font-medium text-gray-900 mt-1">{log.role || 'System'}</p>
              </div>
            </li>
          ))}
          {logs.length === 0 && (
            <li className="px-6 py-4 text-center text-gray-500">No audit logs found.</li>
          )}
        </ul>
      </div>
    </div>
  );
}

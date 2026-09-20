import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Project {
  id: number;
  name: string;
  description: string;
  status: string;
  health: string;
}

export default function PublicProjects() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/public/projects')
      .then(res => res.json())
      .then(data => setProjects(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Public Projects Dashboard</h2>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {projects.map(p => (
          <div key={p.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-xl font-bold mb-2">{p.name}</h3>
            <p className="text-gray-600 mb-4">{p.description}</p>
            <div className="flex gap-2">
              <span className={`px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800`}>
                {p.status}
              </span>
            </div>
            <Link to={`/projects/${p.id}`} className="mt-4 inline-block text-amber-600 font-medium">
              View Dashboard →
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

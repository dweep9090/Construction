import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Projects from './pages/Projects';
import ProjectDashboard from './pages/ProjectDashboard';
import ProjectTasks from './pages/ProjectTasks';
import PublicProjects from './pages/PublicProjects';
import ChangeRequests from './pages/ChangeRequests';
import AuditLogs from './pages/AuditLogs';

import React from 'react';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/projects" replace />} />
          <Route path="projects" element={<Projects />} />
          <Route path="public-projects" element={<PublicProjects />} />
          <Route path="projects/:id" element={<ProjectDashboard />} />
          <Route path="projects/:id/tasks" element={<ProjectTasks />} />
          <Route path="projects/:id/change-requests" element={<ChangeRequests />} />
          <Route path="projects/:id/audit-logs" element={<AuditLogs />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;

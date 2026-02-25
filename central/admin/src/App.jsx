import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Lazy load pages for better performance and organization
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Buildings from './pages/Buildings';
import Persons from './pages/Persons';
import Hardware from './pages/Hardware';
import Schedule from './pages/Schedule';
import Attendance from './pages/Attendance';

// Placeholder companions for future pages
const PlaceholderPage = ({ title }) => (
  <div className="space-y-4">
    <h2 className="text-3xl font-bold tracking-tight">{title}</h2>
    <div className="p-12 border-2 border-dashed border-border rounded-3xl flex flex-col items-center justify-center text-muted-foreground">
      <p>This module is currently under development.</p>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } />

          <Route path="/buildings" element={
            <ProtectedRoute>
              <Layout>
                <Buildings />
              </Layout>
            </ProtectedRoute>
          } />

          <Route path="/persons" element={
            <ProtectedRoute>
              <Layout>
                <Persons />
              </Layout>
            </ProtectedRoute>
          } />

          <Route path="/hardware" element={
            <ProtectedRoute>
              <Layout>
                <Hardware />
              </Layout>
            </ProtectedRoute>
          } />

          <Route path="/schedule" element={
            <ProtectedRoute>
              <Layout>
                <Schedule />
              </Layout>
            </ProtectedRoute>
          } />

          <Route path="/attendance" element={
            <ProtectedRoute>
              <Layout>
                <Attendance />
              </Layout>
            </ProtectedRoute>
          } />

          {/* Catch all redirect to root */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

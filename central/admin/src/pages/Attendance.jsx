import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { ClipboardCheck, FileText, Download, Filter, Search, Loader2 } from 'lucide-react';

const Attendance = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/attendance');
      setLogs(response.data.logs || response.data || []);
    } catch (error) {
      console.error('Error fetching attendance logs:', error);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };
  const filteredLogs = logs.filter(log => {
    const search = searchTerm.toLowerCase();
    return (
      (log.person && log.person.toLowerCase().includes(search)) ||
      (log.session && log.session.toLowerCase().includes(search)) ||
      (log.building && log.building.toLowerCase().includes(search)) ||
      (log.room && log.room.toLowerCase().includes(search))
    );
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Attendance Reports</h2>
          <p className="text-muted-foreground mt-1">Review biometric detection logs and session statistics.</p>
        </div>
        <button className="bg-secondary border border-border text-foreground px-4 py-2.5 rounded-xl font-bold flex items-center gap-2 hover:bg-secondary/80 transition-all">
          <Download size={20} />
          Export CSV
        </button>
      </div>

      <div className="bg-card/40 border border-border rounded-3xl overflow-hidden shadow-sm shadow-black/5 backdrop-blur-md">
        <div className="p-6 border-b border-border bg-secondary/10 flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <input 
                type="text" 
                placeholder="Search logs..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-background border border-border rounded-xl py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground font-medium">Showing {filteredLogs.length} recent detections</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-secondary/10 text-muted-foreground text-xs uppercase tracking-wider font-bold">
              <tr>
                <th className="px-6 py-4">Person</th>
                <th className="px-6 py-4">Session</th>
                <th className="px-6 py-4">Building</th>
                <th className="px-6 py-4">Room</th>
                <th className="px-6 py-4">Detected At</th>
                <th className="px-6 py-4">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-muted-foreground">
                    <Loader2 className="animate-spin mx-auto mb-2" size={24} />
                    Loading logs...
                  </td>
                </tr>
              ) : filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-secondary/20 transition-colors group">
                  <td className="px-6 py-4 font-bold">{log.person}</td>
                  <td className="px-6 py-4 text-sm font-mono text-muted-foreground">{log.session}</td>
                  <td className="px-6 py-4 text-sm font-medium">{log.building}</td>
                  <td className="px-6 py-4 text-sm font-mono text-muted-foreground">{log.room}</td>
                  <td className="px-6 py-4 text-sm font-medium underline decoration-primary/30 decoration-2 underline-offset-4">
                    {new Date(log.time).toLocaleString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td className="px-6 py-4 text-sm font-bold text-green-500">{log.confidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Attendance;

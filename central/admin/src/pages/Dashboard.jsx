import React from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { 
  Users, 
  Activity, 
  CheckCircle2, 
  Clock, 
  ArrowUpRight, 
  ArrowDownRight,
  MoreVertical
} from 'lucide-react';

const StatCard = ({ icon: Icon, label, value }) => (
  <div className="p-6 rounded-3xl bg-card/40 border border-border backdrop-blur-md shadow-sm shadow-black/5 hover:border-primary/50 transition-colors duration-300">
    <div className="flex justify-between items-start mb-4">
      <div className="p-3 rounded-xl bg-secondary text-primary">
        <Icon size={24} />
      </div>
      <button className="text-muted-foreground hover:text-foreground">
        <MoreVertical size={20} />
      </button>
    </div>
    <div>
      <p className="text-sm text-muted-foreground font-medium">{label}</p>
      <div className="flex items-end gap-3 mt-1">
        <h3 className="text-3xl font-bold">{value}</h3>
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const [stats, setStats] = React.useState({
    totalStudents: '...',
    activeNodes: '...',
    attendanceToday: '...',
    ongoingSessions: '...',
    recentLogs: []
  });

  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/dashboard/stats');
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        // Fallback to visual placeholders only if API fails
        setStats({
          totalStudents: '...',
          activeNodes: '...',
          attendanceToday: '...',
          ongoingSessions: '...',
          recentLogs: []
        });
      }
    };
    fetchStats();
    
    // Auto-refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>
          <p className="text-muted-foreground mt-1">Welcome back, Admin. Here's what's happening today.</p>
        </div>
        <div className="bg-secondary px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground border border-border">
          {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={Users} 
          label="Total Students" 
          value={stats.totalStudents} 
        />
        <StatCard 
          icon={Activity} 
          label="Active Edge Nodes" 
          value={stats.activeNodes} 
        />
        <StatCard 
          icon={CheckCircle2} 
          label="Attendance Today" 
          value={stats.attendanceToday} 
        />
        <StatCard 
          icon={Clock} 
          label="Ongoing Sessions" 
          value={stats.ongoingSessions} 
        />
      </div>

      <div className="grid grid-cols-1 gap-6">
        <div className="p-6 rounded-3xl bg-card/40 border border-border backdrop-blur-md shadow-sm shadow-black/5">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Recent Attendance Logs</h3>
            <Link to="/attendance" className="text-sm text-primary font-medium hover:underline">View All</Link>
          </div>
          <div className="space-y-4">
            {stats.recentLogs.length > 0 ? stats.recentLogs.map((log, i) => (
              <div key={log.id || i} className="flex items-center justify-between p-4 rounded-xl bg-secondary/30 hover:bg-secondary/50 transition-colors border border-transparent hover:border-border">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                    {log.person.split(' ').map(n=>n[0]).join('')}
                  </div>
                  <div>
                    <p className="font-semibold">{log.person}</p>
                    <p className="text-xs text-muted-foreground">{log.building}, Room {log.room} • {log.subject}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">
                    {new Date(log.time).toLocaleTimeString(undefined, {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                  <p className="text-xs text-green-500 font-semibold">{log.confidence} Confidence</p>
                </div>
              </div>
            )) : (
              <div className="text-center p-8 text-muted-foreground">
                <p>No recent attendance activity.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

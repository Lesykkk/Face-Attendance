import React from 'react';
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

const StatCard = ({ icon: Icon, label, value, trend, trendValue }) => (
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
        <div className={`flex items-center text-xs font-semibold mb-1 ${trend === 'up' ? 'text-green-500' : 'text-red-500'}`}>
          {trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          {trendValue}
        </div>
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
        // Fallback to visual placeholders
        setStats({
          totalStudents: '1,284',
          activeNodes: '8/12',
          attendanceToday: '89%',
          ongoingSessions: '5',
          recentLogs: [
            { id: 1, person: 'John Doe', room: '214', subject: 'Math Analysis', time: '08:45 AM', confidence: '98.4%' }
          ]
        });
      }
    };
    fetchStats();
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
          trend="up" 
          trendValue="+12.5%" 
        />
        <StatCard 
          icon={Activity} 
          label="Active Edge Nodes" 
          value={stats.activeNodes} 
          trend="down" 
          trendValue="-2" 
        />
        <StatCard 
          icon={CheckCircle2} 
          label="Attendance Today" 
          value={stats.attendanceToday} 
          trend="up" 
          trendValue="+4.2%" 
        />
        <StatCard 
          icon={Clock} 
          label="Ongoing Sessions" 
          value={stats.ongoingSessions} 
          trend="up" 
          trendValue="+1" 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-3xl bg-card/40 border border-border backdrop-blur-md shadow-sm shadow-black/5">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Recent Attendance Logs</h3>
            <button className="text-sm text-primary font-medium hover:underline">View All</button>
          </div>
          <div className="space-y-4">
            {stats.recentLogs.map((log, i) => (
              <div key={log.id || i} className="flex items-center justify-between p-4 rounded-xl bg-secondary/30 hover:bg-secondary/50 transition-colors border border-transparent hover:border-border">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                    {log.person.split(' ').map(n=>n[0]).join('')}
                  </div>
                  <div>
                    <p className="font-semibold">{log.person}</p>
                    <p className="text-xs text-muted-foreground">Room {log.room} • {log.subject}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{log.time}</p>
                  <p className="text-xs text-green-500 font-semibold">{log.confidence} Confidence</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 rounded-3xl bg-card/40 border border-border backdrop-blur-md shadow-sm shadow-black/5">
          <h3 className="text-xl font-bold mb-6">System Health</h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Edge Node A (Main)</span>
                <span className="text-sm text-green-500">Active</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full w-[95%] shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Edge Node B (Building 2)</span>
                <span className="text-sm text-yellow-500">Latency</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full w-[70%]"></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">PostgreSQL Database</span>
                <span className="text-sm text-green-500">Healthy</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full w-[98%] shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

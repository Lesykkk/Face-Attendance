import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import { Bell, User, Clock, Activity, Shield, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

const Layout = ({ children }) => {
  const { user } = useAuth();
  const [time, setTime] = useState(new Date());
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const notifications = [
    { 
      id: 1, 
      title: 'System Online', 
      desc: 'All Edge Nodes are reporting successfully.', 
      time: 'Just now', 
      icon: CheckCircle2, 
      color: 'text-green-500' 
    },
    { 
      id: 2, 
      title: 'New Hardware', 
      desc: 'Edge Node "Building A" was recently updated.', 
      time: '12 mins ago', 
      icon: Activity, 
      color: 'text-primary' 
    },
    { 
      id: 3, 
      title: 'Security Sync', 
      desc: 'Database embeddings successfully synchronized.', 
      time: '1 hour ago', 
      icon: Shield, 
      color: 'text-amber-500' 
    }
  ];

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false
    });
  };

  return (
    <div className="flex min-h-screen bg-background text-foreground selection:bg-primary selection:text-primary-foreground">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-20 border-b border-border flex items-center justify-between px-8 bg-card/30 backdrop-blur-md sticky top-0 z-10">
          <div className="flex flex-col">
            <h1 className="text-xl font-bold tracking-tight">
              Hello, <span className="text-primary">{user?.username || 'Admin'}</span>
            </h1>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock size={14} className="text-primary" />
              <span className="text-xs font-medium tabular-nums">
                {formatTime(time)} • {formatDate(time)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative">
              <button 
                onClick={() => setShowNotifications(!showNotifications)}
                className={`p-2 rounded-xl border transition-all relative ${
                  showNotifications 
                    ? 'bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20' 
                    : 'bg-secondary/50 border-border text-muted-foreground hover:text-foreground hover:bg-secondary'
                }`}
              >
                <Bell size={20} />
                <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full border-2 border-card" />
              </button>

              <AnimatePresence>
                {showNotifications && (
                  <>
                    <div 
                      className="fixed inset-0 z-10" 
                      onClick={() => setShowNotifications(false)} 
                    />
                    <motion.div 
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute right-0 mt-4 w-80 bg-card border border-border rounded-2xl shadow-2xl p-4 z-20 overflow-hidden"
                    >
                      <div className="flex items-center justify-between mb-4 px-2">
                        <h3 className="font-bold">Recent Activity</h3>
                        <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                          Live Status
                        </span>
                      </div>
                      
                      <div className="space-y-2">
                        {notifications.map((n) => (
                          <div key={n.id} className="p-3 rounded-xl hover:bg-secondary/50 transition-colors border border-transparent hover:border-border group">
                            <div className="flex gap-3">
                              <div className={`p-2 rounded-lg bg-secondary group-hover:bg-card transition-colors ${n.color}`}>
                                <n.icon size={18} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-bold truncate">{n.title}</p>
                                <p className="text-[11px] text-muted-foreground line-clamp-1">{n.desc}</p>
                                <p className="text-[10px] text-primary font-medium mt-1 uppercase tracking-tighter opacity-70">{n.time}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <button className="w-full mt-4 py-2 text-xs font-bold text-muted-foreground hover:text-foreground transition-colors border-t border-border pt-4">
                        Clear all notifications
                      </button>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

            <div className="flex items-center gap-3 pl-4 border-l border-border">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-bold">{user?.username || 'Admin User'}</p>
                <div className="flex items-center gap-1.5 justify-end">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Online Status</p>
                </div>
              </div>
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary to-primary/60 flex items-center justify-center text-primary-foreground shadow-lg shadow-primary/20">
                <User size={20} />
              </div>
            </div>
          </div>
        </header>
        <main className="flex-1 p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;

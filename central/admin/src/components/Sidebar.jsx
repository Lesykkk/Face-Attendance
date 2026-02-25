import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Users, 
  LayoutDashboard, 
  Building2, 
  Cpu, 
  Calendar, 
  ClipboardCheck, 
  Settings, 
  LogOut 
} from 'lucide-react';

const SidebarItem = ({ icon: Icon, label, path, active = false }) => (
  <Link to={path} className={`
    flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200
    ${active 
      ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20' 
      : 'text-muted-foreground hover:bg-secondary hover:text-foreground'}
  `}>
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </Link>
);

const Sidebar = () => {
  const location = useLocation();
  const { logout } = useAuth();
  const isActive = (path) => location.pathname === path;

  return (
    <div className="w-64 border-r border-border h-screen flex flex-col p-4 bg-card/50 backdrop-blur-xl sticky top-0">
      <div className="flex items-center gap-3 px-4 py-6 mb-8">
        <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
          <ClipboardCheck className="text-primary-foreground" size={24} />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight">Face Attendance</h1>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold">Central Admin</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        <SidebarItem icon={LayoutDashboard} label="Dashboard" path="/" active={isActive('/')} />
        <SidebarItem icon={Building2} label="Buildings" path="/buildings" active={isActive('/buildings')} />
        <SidebarItem icon={Users} label="Persons" path="/persons" active={isActive('/persons')} />
        <SidebarItem icon={Cpu} label="Hardware" path="/hardware" active={isActive('/hardware')} />
        <SidebarItem icon={Calendar} label="Schedule" path="/schedule" active={isActive('/schedule')} />
        <SidebarItem icon={ClipboardCheck} label="Attendance" path="/attendance" active={isActive('/attendance')} />
      </nav>

      <div className="pt-4 border-t border-border space-y-1">
        <SidebarItem icon={Settings} label="Settings" path="/settings" active={isActive('/settings')} />
        <button 
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200 text-muted-foreground hover:bg-destructive/10 hover:text-destructive mt-1"
        >
          <LogOut size={20} />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;

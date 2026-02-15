
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Flag, Crosshair, LayoutDashboard, PlusCircle, Calendar, LogOut, Clock, 
  CheckCircle2, AlertCircle, ChevronRight, Menu, X, Lock, User, Database, 
  Terminal, Settings, Key, ShieldAlert
} from 'lucide-react';

// --- API Configuration ---
const getApiUrl = () => {
  const host = window.location.hostname;
  return `http://${host}:8000/api`;
};
const getAdminUrl = () => {
  const host = window.location.hostname;
  return `http://${host}:8000/admin`;
};

const API_URL = getApiUrl();
const ADMIN_URL = getAdminUrl();

// --- Types ---
interface UserProfile {
  username: string;
  is_staff: boolean;
  authHeader: string;
  force_password_change: boolean;
}

interface BookingRequest {
  id: number;
  course: number;
  course_name: string;
  username?: string;
  desired_date: string;
  earliest_time: string;
  latest_time: string;
  players: number;
  execution_time: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED' | 'RUNNING';
  result_log?: string;
  created_at: string;
}

interface GolfCourse {
  id: number;
  name: string;
  url: string;
}

interface UserCredential {
  id: number;
  course: number;
  course_name: string;
  course_email: string;
}

// --- Components ---

const LoginScreen = ({ onLogin }: { onLogin: (u: string, p: string) => Promise<void> }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await onLogin(username, password);
    } catch (err) {
      setError('Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          <div className="bg-emerald-600 p-8 text-center">
            <div className="w-16 h-16 bg-white/20 rounded-2xl mx-auto flex items-center justify-center backdrop-blur-sm mb-4">
              <Flag className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-black text-white tracking-tight uppercase italic">PinSeeker</h1>
            <p className="text-emerald-100 mt-2 font-medium">Automated Tee Time Engine</p>
          </div>
          
          <form onSubmit={handleSubmit} className="p-8 space-y-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Username</label>
                <div className="relative">
                  <User className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                  <input 
                    type="text" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none font-medium transition-all"
                    placeholder="Enter your username"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                  <input 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none font-medium transition-all"
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>
            </div>

            {error && (
              <div className="p-4 bg-red-50 text-red-600 text-sm font-medium rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-slate-900 text-white font-bold py-4 rounded-xl hover:bg-slate-800 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
              {!loading && <ChevronRight className="w-4 h-4" />}
            </button>
          </form>
          <div className="bg-slate-50 p-4 text-center border-t border-slate-100">
            <p className="text-xs text-slate-400 font-medium">Restricted Access • Authorized Personnel Only</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const ChangePasswordScreen = ({ user, onSuccess }: { user: UserProfile, onSuccess: () => void }) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/me/change_password/`, {
        method: 'POST',
        headers: { 
          'Authorization': user.authHeader,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_password: newPassword })
      });
      if (res.ok) {
        onSuccess();
      } else {
        const data = await res.json();
        setError(data.error || "Failed to update password.");
      }
    } catch (e) {
      setError("Connection failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl p-8 space-y-6">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-14 h-14 bg-amber-100 rounded-full flex items-center justify-center mb-2">
            <ShieldAlert className="w-7 h-7 text-amber-600" />
          </div>
          <h2 className="text-2xl font-black text-slate-900">Security Update Required</h2>
          <p className="text-slate-500 font-medium">Please change your temporary password to continue.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">New Password</label>
            <input 
              type="password" 
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-2">Confirm Password</label>
            <input 
              type="password" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 outline-none"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm font-medium rounded-lg">{error}</div>
          )}

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-slate-900 text-white font-bold py-4 rounded-xl hover:bg-slate-800 transition-all"
          >
            {loading ? 'Updating...' : 'Update Password & Continue'}
          </button>
        </form>
      </div>
    </div>
  );
};

const CredentialManager = ({ courses, user }: { courses: GolfCourse[], user: UserProfile }) => {
  const [credentials, setCredentials] = useState<UserCredential[]>([]);
  const [editingCourse, setEditingCourse] = useState<number | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchCredentials = async () => {
    try {
      const res = await fetch(`${API_URL}/credentials/`, {
        headers: { 'Authorization': user.authHeader }
      });
      if (res.ok) setCredentials(await res.json());
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchCredentials(); }, []);

  const handleEdit = (courseId: number, currentEmail: string = '') => {
    setEditingCourse(courseId);
    setEmail(currentEmail);
    setPassword('');
  };

  const handleSave = async (courseId: number) => {
    const existingCred = credentials.find(c => c.course === courseId);
    const method = existingCred ? 'PUT' : 'POST';
    const url = existingCred 
      ? `${API_URL}/credentials/${existingCred.id}/` 
      : `${API_URL}/credentials/`;

    const body: any = { course: courseId, course_email: email };
    if (password) body.password = password;

    const res = await fetch(url, {
      method: method,
      headers: { 
        'Authorization': user.authHeader,
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify(body)
    });

    if (res.ok) {
      await fetchCredentials();
      setEditingCourse(null);
    } else {
      alert("Failed to save credentials.");
    }
  };

  if (isLoading) return <div className="p-8 text-center text-slate-500">Loading settings...</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-black text-slate-900">Course Credentials</h1>
        <p className="text-slate-500 mt-2">Manage your login details for each golf course provider. The bot uses these to book on your behalf.</p>
      </div>

      <div className="grid gap-4">
        {courses.map(course => {
          const cred = credentials.find(c => c.course === course.id);
          const isEditing = editingCourse === course.id;

          return (
            <div key={course.id} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all hover:border-emerald-200">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${cred ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                  {cred ? <CheckCircle2 className="w-6 h-6" /> : <Key className="w-6 h-6" />}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{course.name}</h3>
                  <div className="text-sm">
                    {cred ? (
                      <span className="text-emerald-600 font-medium">Configured as {cred.course_email}</span>
                    ) : (
                      <span className="text-slate-400 italic">Not configured</span>
                    )}
                  </div>
                </div>
              </div>

              {isEditing ? (
                <div className="flex-1 max-w-lg bg-slate-50 p-4 rounded-xl border border-slate-200 animate-in fade-in slide-in-from-top-2">
                   <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                      <input 
                        type="email" placeholder="Course Username/Email"
                        value={email} onChange={e => setEmail(e.target.value)}
                        className="p-2 border rounded-lg text-sm"
                      />
                      <input 
                        type="password" placeholder="Course Password"
                        value={password} onChange={e => setPassword(e.target.value)}
                        className="p-2 border rounded-lg text-sm"
                      />
                   </div>
                   <div className="flex gap-2 justify-end">
                      <button onClick={() => setEditingCourse(null)} className="px-3 py-1.5 text-xs font-bold text-slate-500 hover:text-slate-700">Cancel</button>
                      <button onClick={() => handleSave(course.id)} className="px-3 py-1.5 text-xs font-bold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">Save Credentials</button>
                   </div>
                </div>
              ) : (
                <button 
                  onClick={() => handleEdit(course.id, cred?.course_email)}
                  className="px-5 py-2.5 rounded-xl border border-slate-200 font-bold text-sm hover:bg-slate-50 hover:border-slate-300 transition-colors"
                >
                  {cred ? 'Update Login' : 'Setup Login'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Sidebar = ({ activeTab, setActiveTab, isOpen, setIsOpen, user, onLogout }: { 
  activeTab: string, 
  setActiveTab: (t: string) => void,
  isOpen: boolean,
  setIsOpen: (o: boolean) => void,
  user: UserProfile,
  onLogout: () => void
}) => {
  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'new-request', icon: PlusCircle, label: 'New Request' },
    { id: 'bookings', icon: Calendar, label: 'History' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  const handleNav = (id: string) => {
    setActiveTab(id);
    setIsOpen(false);
  };

  return (
    <>
      {/* Mobile Overlay */}
      <div 
        className={`fixed inset-0 bg-slate-900/60 z-40 md:hidden backdrop-blur-sm transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setIsOpen(false)}
      />

      <aside className={`
        fixed left-0 top-0 h-screen w-72 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 z-50 transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="p-8 flex items-center justify-between text-white">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center rotate-3 shadow-lg shadow-emerald-500/20">
                <Flag className="w-6 h-6 text-white" />
              </div>
              <Crosshair className="w-4 h-4 text-emerald-300 absolute -bottom-1 -right-1" />
            </div>
            <span className="text-2xl font-black tracking-tight uppercase italic">PinSeeker</span>
          </div>
          <button onClick={() => setIsOpen(false)} className="md:hidden p-2 hover:bg-slate-800 rounded-lg transition-colors">
            <X className="w-6 h-6 text-slate-400" />
          </button>
        </div>

        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto mt-4">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNav(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-4 rounded-xl transition-all duration-200 ${
                activeTab === item.id 
                  ? 'bg-emerald-600 text-white shadow-xl shadow-emerald-600/20' 
                  : 'hover:bg-slate-800 hover:text-white'
              }`}
            >
              <item.icon className={`w-5 h-5 ${activeTab === item.id ? 'text-white' : 'text-slate-500'}`} />
              <span className="font-semibold">{item.label}</span>
            </button>
          ))}

          {/* Admin System Link - Only visible to staff */}
          {user.is_staff && (
            <div className="pt-4 mt-4 border-t border-slate-800">
               <p className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">System Admin</p>
               <a 
                 href={ADMIN_URL}
                 target="_blank"
                 className="w-full flex items-center gap-3 px-4 py-4 rounded-xl transition-all duration-200 hover:bg-purple-900/30 hover:text-purple-300 text-slate-400 group"
               >
                  <Database className="w-5 h-5 group-hover:text-purple-400" />
                  <span className="font-semibold">System Database</span>
                  <ChevronRight className="w-4 h-4 ml-auto opacity-50" />
               </a>
            </div>
          )}
        </nav>

        <div className="p-6 border-t border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-3 mb-6">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white uppercase ${user.is_staff ? 'bg-purple-600' : 'bg-slate-700'}`}>
              {user.username.substring(0, 2)}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold text-white capitalize">{user.username}</span>
              <span className="text-xs text-slate-500">{user.is_staff ? 'System Admin' : 'Golfer'}</span>
            </div>
          </div>
          <button 
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-slate-700 hover:border-red-500/50 hover:text-red-400 transition-all text-sm font-medium"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};

// ... (StatCard, StatusBadge, Dashboard, NewRequestForm components kept as is from original, just updated Sidebar usage and App return) ...
// To save space in this response, I am re-using the previous components where they haven't changed, 
// but including the updated App component which orchestrates the new views.

const StatCard = ({ title, value, icon: Icon, colorClass }: any) => (
  <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-start justify-between h-full group hover:shadow-md transition-all">
    <div className="space-y-1">
      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{title}</p>
      <h3 className="text-3xl font-black text-slate-900">{value}</h3>
    </div>
    <div className={`p-4 rounded-2xl ${colorClass} bg-opacity-10 group-hover:scale-110 transition-transform`}>
      <Icon className={`w-7 h-7 ${colorClass.replace('bg-', 'text-')}`} />
    </div>
  </div>
);

const StatusBadge = ({ status }: { status: string }) => {
  const styles: any = {
    PENDING: 'bg-amber-100 text-amber-700 border-amber-200',
    RUNNING: 'bg-blue-100 text-blue-700 border-blue-200 animate-pulse',
    SUCCESS: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    FAILED: 'bg-red-100 text-red-700 border-red-200',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold border uppercase tracking-wide whitespace-nowrap shadow-sm ${styles[status] || styles.PENDING}`}>
      <div className={`w-1.5 h-1.5 rounded-full ${styles[status]?.replace('text-', 'bg-') || 'bg-amber-500'}`} />
      {status}
    </span>
  );
};

const Dashboard = ({ bookings, isLoading, user }: { bookings: BookingRequest[], isLoading: boolean, user: UserProfile }) => {
  if (isLoading) return (
    <div className="flex flex-col items-center justify-center h-64 space-y-4">
      <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-slate-500 font-medium animate-pulse">Scanning the greens...</p>
    </div>
  );

  const successCount = bookings.filter(b => b.status === 'SUCCESS').length;
  const pendingCount = bookings.filter(b => b.status === 'PENDING').length;
  const nextRun = bookings.find(b => b.status === 'PENDING')?.execution_time || 'None';

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">
            {user.is_staff ? 'Admin Dashboard' : 'My Dashboard'}
          </h1>
          <p className="text-slate-500 mt-1 font-medium">
            {user.is_staff ? 'Overview of all system activity.' : 'Your personal automated golf bookings.'}
          </p>
        </div>
        <div className="bg-emerald-50 px-4 py-2 rounded-xl border border-emerald-100 flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-sm"></div>
          <span className="text-sm font-bold text-emerald-700 uppercase tracking-wide">Server Live</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard title="Active Queued" value={pendingCount} icon={Clock} colorClass="bg-blue-600" />
        <StatCard title="Total Success" value={successCount} icon={CheckCircle2} colorClass="bg-emerald-600" />
        <StatCard title="Next Target" value={nextRun !== 'None' ? new Date(nextRun).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--:--'} icon={Calendar} colorClass="bg-purple-600" />
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50 overflow-hidden">
        <div className="px-8 py-6 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-xl font-bold text-slate-900">
            {user.is_staff ? 'Global Tee Times' : 'My Tee Times'}
          </h3>
          <button className="text-sm font-bold text-emerald-600 hover:text-emerald-700">View All</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 text-slate-400">
                <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px]">Course</th>
                {user.is_staff && <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px]">User</th>}
                <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px]">Play Window</th>
                <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px] hidden sm:table-cell">Players</th>
                <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px]">Status</th>
                <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px] hidden md:table-cell">Execution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {bookings.map((booking) => (
                <tr key={booking.id} className="hover:bg-slate-50/50 transition-colors group">
                  <td className="px-8 py-5">
                    <span className="font-bold text-slate-900 text-base">{booking.course_name}</span>
                  </td>
                  {user.is_staff && (
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2">
                         <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-bold text-slate-600 uppercase">
                          {booking.username?.substring(0, 2) || '??'}
                         </div>
                         <span className="text-slate-600 font-medium">{booking.username}</span>
                      </div>
                    </td>
                  )}
                  <td className="px-8 py-5">
                    <div className="flex flex-col">
                      <span className="text-slate-900 font-semibold">{new Date(booking.desired_date).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}</span>
                      <span className="text-xs font-medium text-slate-400 uppercase tracking-tighter mt-0.5">{booking.earliest_time} - {booking.latest_time}</span>
                    </div>
                  </td>
                  <td className="px-8 py-5 hidden sm:table-cell">
                    <div className="flex -space-x-1">
                      {[...Array(booking.players)].map((_, i) => (
                        <div key={i} className="w-7 h-7 rounded-full bg-slate-100 border-2 border-white flex items-center justify-center text-[10px] font-bold text-slate-500">P{i+1}</div>
                      ))}
                    </div>
                  </td>
                  <td className="px-8 py-5">
                    <StatusBadge status={booking.status} />
                  </td>
                  <td className="px-8 py-5 text-slate-400 font-mono text-xs hidden md:table-cell">
                    {new Date(booking.execution_time).toLocaleString()}
                  </td>
                </tr>
              ))}
              {bookings.length === 0 && (
                <tr>
                  <td colSpan={user.is_staff ? 6 : 5} className="px-8 py-16 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
                        <Calendar className="w-8 h-8 text-slate-200" />
                      </div>
                      <p className="text-slate-400 font-medium">No booking activity found.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const NewRequestForm = ({ courses, onSubmit }: { courses: GolfCourse[], onSubmit: (data: any) => void }) => {
  const [formData, setFormData] = useState({
    course: '',
    desired_date: '',
    earliest_time: '07:00',
    latest_time: '11:00',
    players: '4',
    executionDate: '',
    executionTime: '08:00:05',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    const execution_time = `${formData.executionDate}T${formData.executionTime}`;
    await onSubmit({ ...formData, execution_time });
    setIsSubmitting(false);
  };

  return (
    <div className="max-w-4xl mx-auto pb-20">
      <div className="mb-10 text-center md:text-left">
        <h1 className="text-4xl font-black text-slate-900 tracking-tight">Deploy A Bot</h1>
        <p className="text-slate-500 font-medium mt-2">Configure the seeker for your next round.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Course Selection */}
        <section className="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600"><Flag className="w-5 h-5" /></div>
            <h2 className="text-lg font-bold text-slate-900">Destination</h2>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {courses.length === 0 && (
              <div className="col-span-full bg-red-50 border border-red-100 p-6 rounded-2xl text-red-600 text-sm flex items-center gap-3 font-medium">
                <AlertCircle className="w-6 h-6" />
                <span>No courses configured. Use the Admin panel to add your golf clubs.</span>
              </div>
            )}
            {courses.map((course) => (
              <label 
                key={course.id} 
                className={`relative group flex items-center p-5 border-2 rounded-2xl cursor-pointer transition-all duration-300 ${
                  Number(formData.course) === course.id
                    ? 'border-emerald-500 bg-emerald-50/50 shadow-lg shadow-emerald-500/10' 
                    : 'border-slate-100 hover:border-slate-300 bg-white'
                }`}
              >
                <input 
                  type="radio" name="course" value={course.id} className="sr-only"
                  onChange={(e) => setFormData({...formData, course: e.target.value})}
                  required
                />
                <div className="flex-1">
                  <span className={`block text-lg font-bold transition-colors ${Number(formData.course) === course.id ? 'text-emerald-900' : 'text-slate-900'}`}>
                    {course.name}
                  </span>
                  <span className="text-xs text-slate-400 font-medium uppercase tracking-widest mt-1 block">Active Booking Engine</span>
                </div>
                {Number(formData.course) === course.id && (
                  <div className="bg-emerald-500 rounded-full p-1.5 shadow-md">
                    <CheckCircle2 className="w-5 h-5 text-white" />
                  </div>
                )}
              </label>
            ))}
          </div>
        </section>

        {/* Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Round Logistics */}
          <section className="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-50 rounded-lg text-blue-600"><Calendar className="w-5 h-5" /></div>
              <h2 className="text-lg font-bold text-slate-900">Round Details</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 px-1">Tee Date</label>
                <input 
                  type="date" className="w-full h-14 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 border-2 px-5 font-bold text-slate-900 transition-all outline-none"
                  value={formData.desired_date}
                  onChange={(e) => setFormData({...formData, desired_date: e.target.value})}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 px-1">Earliest</label>
                  <input 
                    type="time" className="w-full h-14 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 border-2 px-5 font-bold text-slate-900 transition-all outline-none"
                    value={formData.earliest_time}
                    onChange={(e) => setFormData({...formData, earliest_time: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 px-1">Latest</label>
                  <input 
                    type="time" className="w-full h-14 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 border-2 px-5 font-bold text-slate-900 transition-all outline-none"
                    value={formData.latest_time}
                    onChange={(e) => setFormData({...formData, latest_time: e.target.value})}
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 px-1">Player Count</label>
                <div className="grid grid-cols-4 gap-2">
                  {[1, 2, 3, 4].map(n => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setFormData({...formData, players: n.toString()})}
                      className={`h-14 rounded-2xl font-black transition-all border-2 ${
                        formData.players === n.toString() 
                        ? 'bg-slate-900 text-white border-slate-900 shadow-lg' 
                        : 'bg-slate-50 text-slate-500 border-transparent hover:border-slate-200'
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Bot Execution */}
          <section className="bg-slate-900 rounded-3xl p-8 shadow-2xl space-y-6 text-white overflow-hidden relative">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <Crosshair className="w-32 h-32 rotate-12" />
            </div>
            
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-emerald-500 rounded-lg text-white"><Clock className="w-5 h-5" /></div>
                <h2 className="text-lg font-bold">Execution Plan</h2>
              </div>
              
              <div className="bg-slate-800/50 p-5 rounded-2xl border border-white/5 mb-8">
                <p className="text-sm text-slate-400 leading-relaxed font-medium">
                  Set the exact moment the course opens its bookings (e.g., 7:00 AM sharp 10 days out). The seeker will execute precisely at this time.
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-2 px-1">Execution Day</label>
                  <input 
                    type="date" className="w-full h-14 rounded-2xl bg-slate-800 border-transparent focus:border-emerald-500 border-2 px-5 font-bold text-white transition-all outline-none"
                    value={formData.executionDate}
                    onChange={(e) => setFormData({...formData, executionDate: e.target.value})}
                    required
                  />
                </div>

                <div>
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-2 px-1">Release Time (HH:MM:SS)</label>
                  <input 
                    type="time" step="1" className="w-full h-14 rounded-2xl bg-slate-800 border-transparent focus:border-emerald-500 border-2 px-5 font-bold text-white transition-all outline-none"
                    value={formData.executionTime}
                    onChange={(e) => setFormData({...formData, executionTime: e.target.value})}
                  />
                </div>
              </div>
            </div>
          </section>
        </div>

        <div className="flex flex-col items-center gap-4 py-8">
          <button 
            type="submit" 
            disabled={isSubmitting || !formData.course}
            className="w-full md:w-auto min-w-[300px] h-16 bg-emerald-600 text-white font-black text-lg rounded-2xl hover:bg-emerald-700 active:scale-95 transition-all shadow-2xl shadow-emerald-600/30 flex items-center justify-center gap-3 disabled:opacity-30 disabled:pointer-events-none"
          >
            {isSubmitting ? 'Armed & Loading...' : 'Schedule Seeker'}
            {!isSubmitting && <Crosshair className="w-6 h-6" />}
          </button>
          <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">Powered by Playwright Automation</p>
        </div>
      </form>
    </div>
  );
};

const App = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [bookings, setBookings] = useState<BookingRequest[]>([]);
  const [courses, setCourses] = useState<GolfCourse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    if (!user) return;
    
    try {
      const headers = { 'Authorization': user.authHeader, 'Content-Type': 'application/json' };
      const [bookingsRes, coursesRes] = await Promise.all([
        fetch(`${API_URL}/requests/`, { headers }),
        fetch(`${API_URL}/courses/`, { headers })
      ]);
      if (bookingsRes.ok && coursesRes.ok) {
        setBookings(await bookingsRes.json());
        setCourses(await coursesRes.json());
      }
    } catch (err) {
      console.warn("Retrying connection to API...");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && !user.force_password_change) {
      fetchData();
      const interval = setInterval(fetchData, 8000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleLogin = async (u: string, p: string) => {
    const authHeader = 'Basic ' + btoa(`${u}:${p}`);
    const res = await fetch(`${API_URL}/me/`, {
      headers: { 'Authorization': authHeader }
    });
    
    if (res.ok) {
      const data = await res.json();
      setUser({
        username: data.username,
        is_staff: data.is_staff,
        force_password_change: data.force_password_change,
        authHeader: authHeader
      });
      setLoading(true);
    } else {
      throw new Error('Invalid credentials');
    }
  };

  const handleLogout = () => {
    setUser(null);
    setBookings([]);
    setCourses([]);
    setActiveTab('dashboard');
  };

  const handleNewBooking = async (data: any) => {
    if (!user) return;
    try {
      const res = await fetch(`${API_URL}/requests/`, {
        method: 'POST',
        headers: { 'Authorization': user.authHeader, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        await fetchData();
        setActiveTab('dashboard');
      } else {
        alert("Configuration error. Please verify your execution time.");
      }
    } catch (e) {
      alert("Lost connection to server.");
    }
  };

  if (!user) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  if (user.force_password_change) {
    return <ChangePasswordScreen user={user} onSuccess={() => setUser({ ...user, force_password_change: false })} />;
  }

  return (
    <div className="flex min-h-screen bg-slate-50 font-sans selection:bg-emerald-100 selection:text-emerald-900">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isOpen={isSidebarOpen} 
        setIsOpen={setIsSidebarOpen} 
        user={user}
        onLogout={handleLogout}
      />
      
      <main className="flex-1 w-full md:ml-72 transition-all duration-300">
        <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-slate-200 px-6 py-4 flex justify-between items-center md:hidden">
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Flag className="w-5 h-5 text-white" />
              </div>
            <span className="text-lg font-black tracking-tight uppercase italic text-slate-900">PinSeeker</span>
          </div>
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="p-2.5 bg-slate-100 text-slate-600 rounded-xl hover:bg-slate-200 active:scale-95 transition-all"
          >
            <Menu className="w-6 h-6" />
          </button>
        </header>

        <div className="p-6 md:p-12">
          {activeTab === 'dashboard' && <Dashboard bookings={bookings} isLoading={loading} user={user} />}
          {activeTab === 'new-request' && <NewRequestForm courses={courses} onSubmit={handleNewBooking} />}
          {activeTab === 'bookings' && <Dashboard bookings={bookings} isLoading={loading} user={user} />}
          {activeTab === 'settings' && <CredentialManager courses={courses} user={user} />}
        </div>
      </main>
    </div>
  );
};

const root = createRoot(document.getElementById('root')!);
root.render(<App />);

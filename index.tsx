
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Flag, Crosshair, LayoutDashboard, PlusCircle, Calendar, Key, LogOut, Clock, 
  CheckCircle2, XCircle, AlertCircle, FolderTree, FileCode, ChevronRight, ChevronDown 
} from 'lucide-react';

// --- API Configuration ---
// In a real app, use environment variables. Basic Auth used here for local simplicity.
const API_URL = 'http://127.0.0.1:8000/api';
// HARDCODED CREDENTIALS FOR DEMO ONLY - Replace with a real Login Form in production
const BASIC_AUTH = 'Basic ' + btoa('admin:password123'); 

// --- Types ---
interface BookingRequest {
  id: number;
  course: number; // ID from DB
  course_name: string;
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

// --- Components ---

const Sidebar = ({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (t: string) => void }) => {
  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'new-request', icon: PlusCircle, label: 'New Request' },
    { id: 'bookings', icon: Calendar, label: 'Bookings' },
  ];

  return (
    <div className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen fixed left-0 top-0 border-r border-slate-800">
      <div className="p-6 flex items-center gap-3 text-white border-b border-slate-800">
        <div className="relative">
          <Flag className="w-8 h-8 text-emerald-500" />
          <Crosshair className="w-4 h-4 text-white absolute -bottom-1 -right-1" />
        </div>
        <span className="text-xl font-bold tracking-tight">PinSeeker</span>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === item.id 
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20' 
                : 'hover:bg-slate-800 hover:text-white'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 hover:text-white transition-colors text-slate-400">
          <LogOut className="w-5 h-5" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon: Icon, colorClass }: any) => (
  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-start justify-between">
    <div>
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <h3 className="text-2xl font-bold text-slate-900 mt-1">{value}</h3>
    </div>
    <div className={`p-3 rounded-lg ${colorClass} bg-opacity-10`}>
      <Icon className={`w-6 h-6 ${colorClass.replace('bg-', 'text-')}`} />
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
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${styles[status] || styles.PENDING}`}>
      {status === 'SUCCESS' ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
      {status}
    </span>
  );
};

// --- Dashboard View ---
const Dashboard = ({ bookings, isLoading }: { bookings: BookingRequest[], isLoading: boolean }) => {
  if (isLoading) return <div className="p-10 text-center">Loading bookings...</div>;

  const successCount = bookings.filter(b => b.status === 'SUCCESS').length;
  const pendingCount = bookings.filter(b => b.status === 'PENDING').length;
  // Parse next execution safely
  const nextRun = bookings.find(b => b.status === 'PENDING')?.execution_time || 'None';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span>Server Status:</span>
          <span className="flex items-center gap-1.5 text-emerald-600 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Online
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Pending Requests" value={pendingCount} icon={Clock} colorClass="text-blue-600" />
        <StatCard title="Successful Bookings" value={successCount} icon={CheckCircle2} colorClass="text-emerald-600" />
        <StatCard title="Next Execution" value={nextRun !== 'None' ? new Date(nextRun).toLocaleTimeString() : '--:--'} icon={Calendar} colorClass="text-purple-600" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">Recent Activity</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-medium">Course</th>
                <th className="px-6 py-3 font-medium">Play Date</th>
                <th className="px-6 py-3 font-medium">Players</th>
                <th className="px-6 py-3 font-medium">Execution</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Log</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {bookings.map((booking) => (
                <tr key={booking.id} className="hover:bg-slate-50/50">
                  <td className="px-6 py-4 font-medium text-slate-900">{booking.course_name}</td>
                  <td className="px-6 py-4 text-slate-600">{booking.desired_date} @ {booking.earliest_time}</td>
                  <td className="px-6 py-4 text-slate-600">{booking.players}</td>
                  <td className="px-6 py-4 text-slate-600 font-mono text-xs">
                    {new Date(booking.execution_time).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={booking.status} />
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-400 max-w-[200px] truncate">
                    {booking.result_log}
                  </td>
                </tr>
              ))}
              {bookings.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400">No bookings found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// --- New Request Form ---
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
    
    // Combine execution date/time
    const execution_time = `${formData.executionDate}T${formData.executionTime}`; // ISO format roughly
    
    await onSubmit({
      ...formData,
      execution_time
    });
    setIsSubmitting(false);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900">New Tee Time Request</h2>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        
        {/* Course Selection */}
        <div className="space-y-4">
          <label className="block text-sm font-medium text-slate-700">Select Golf Course</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {courses.length === 0 && <p className="text-sm text-red-500">No courses found in database. Please ask admin to add courses.</p>}
            {courses.map((course) => (
              <label 
                key={course.id} 
                className={`relative flex items-center p-4 border rounded-lg cursor-pointer transition-all ${
                  Number(formData.course) === course.id
                    ? 'border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500' 
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <input 
                  type="radio" 
                  name="course" 
                  value={course.id} 
                  className="sr-only"
                  onChange={(e) => setFormData({...formData, course: e.target.value})}
                />
                <div className="flex-1">
                  <span className={`block font-medium ${Number(formData.course) === course.id ? 'text-emerald-900' : 'text-slate-900'}`}>
                    {course.name}
                  </span>
                </div>
                {Number(formData.course) === course.id && <CheckCircle2 className="w-5 h-5 text-emerald-600" />}
              </label>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Play Details */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-900 flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Play Details
            </h4>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Desired Date</label>
              <input 
                type="date" 
                className="w-full rounded-lg border-slate-300 border px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                value={formData.desired_date}
                onChange={(e) => setFormData({...formData, desired_date: e.target.value})}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Earliest Time</label>
                <input 
                  type="time" 
                  className="w-full rounded-lg border-slate-300 border px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                  value={formData.earliest_time}
                  onChange={(e) => setFormData({...formData, earliest_time: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Latest Time</label>
                <input 
                  type="time" 
                  className="w-full rounded-lg border-slate-300 border px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                  value={formData.latest_time}
                  onChange={(e) => setFormData({...formData, latest_time: e.target.value})}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Player Count</label>
              <select 
                className="w-full rounded-lg border-slate-300 border px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                value={formData.players}
                onChange={(e) => setFormData({...formData, players: e.target.value})}
              >
                <option value="1">1 Player</option>
                <option value="2">2 Players</option>
                <option value="3">3 Players</option>
                <option value="4">4 Players</option>
              </select>
            </div>
          </div>

          {/* Execution Strategy */}
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-900 flex items-center gap-2">
              <Crosshair className="w-4 h-4" />
              Bot Execution Strategy
            </h4>
            
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <p className="text-sm text-slate-600">
                  Set this to the exact moment tee times are released (usually 7 or 14 days prior at 8:00 AM).
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Execution Date</label>
              <input 
                type="date" 
                className="w-full rounded-lg border-slate-300 border px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                value={formData.executionDate}
                onChange={(e) => setFormData({...formData, executionDate: e.target.value})}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Execution Time</label>
              <input 
                type="time" 
                step="1"
                className="w-full rounded-lg border-slate-300 border px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
                value={formData.executionTime}
                onChange={(e) => setFormData({...formData, executionTime: e.target.value})}
              />
              <p className="text-xs text-slate-500 mt-1">Include seconds for precision (e.g., 08:00:05)</p>
            </div>
          </div>
        </div>

        <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-100">
          <button 
            type="submit" 
            disabled={isSubmitting}
            className="px-5 py-2.5 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors shadow-lg shadow-emerald-900/10 flex items-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? 'Scheduling...' : 'Schedule Bot'}
            {!isSubmitting && <Crosshair className="w-4 h-4" />}
          </button>
        </div>
      </form>
    </div>
  );
};

// --- Main App Layout ---
const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [bookings, setBookings] = useState<BookingRequest[]>([]);
  const [courses, setCourses] = useState<GolfCourse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const headers = { 'Authorization': BASIC_AUTH, 'Content-Type': 'application/json' };
      
      const [bookingsRes, coursesRes] = await Promise.all([
        fetch(`${API_URL}/requests/`, { headers }),
        fetch(`${API_URL}/courses/`, { headers })
      ]);

      if (bookingsRes.ok && coursesRes.ok) {
        setBookings(await bookingsRes.json());
        setCourses(await coursesRes.json());
      } else {
        console.error("Auth failed or API down");
      }
    } catch (err) {
      console.error("Network error", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll for status updates every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleNewBooking = async (data: any) => {
    try {
      const res = await fetch(`${API_URL}/requests/`, {
        method: 'POST',
        headers: { 'Authorization': BASIC_AUTH, 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        await fetchData();
        setActiveTab('dashboard');
      } else {
        alert("Failed to create booking");
      }
    } catch (e) {
      alert("Error submitting form");
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 ml-64 p-8">
        <header className="mb-8 flex justify-between items-center">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <span>PinSeeker</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-slate-900 font-medium capitalize">{activeTab.replace('-', ' ')}</span>
          </div>
          <div className="flex items-center gap-4">
             <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
              <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold text-sm">
                AD
              </div>
              <span className="text-sm font-medium text-slate-700">Admin</span>
            </div>
          </div>
        </header>

        {activeTab === 'dashboard' && <Dashboard bookings={bookings} isLoading={loading} />}
        {activeTab === 'new-request' && <NewRequestForm courses={courses} onSubmit={handleNewBooking} />}
        {activeTab === 'bookings' && <Dashboard bookings={bookings} isLoading={loading} />}
      </main>
    </div>
  );
};

const root = createRoot(document.getElementById('root')!);
root.render(<App />);

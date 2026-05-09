import React, { useState, useEffect } from 'react';
import { 
  Flag, Crosshair, LayoutDashboard, PlusCircle, Calendar, LogOut, Clock, 
  CheckCircle2, AlertCircle, ChevronRight, Menu, X, Lock, Terminal, Trash2, XCircle
} from 'lucide-react';

// --- API Configuration ---
// In production (Cloud Run), the API is on the same host.
const API_URL = '/api';

// --- Hardcoded Courses (Serverless Architecture) ---
const AVAILABLE_COURSES = [
  { id: 1, name: "Capital Hills", url: "", advance_booking_days: 10 },
  { id: 2, name: "Old Post Road", url: "", advance_booking_days: 10 },
  { id: 3, name: "Orchard Creek", url: "", advance_booking_days: 14 },
  { id: 4, name: "Schenectady Muni", url: "", advance_booking_days: 7 },
  { id: 5, name: "Fairways of Halfmoon", url: "", advance_booking_days: 14 },
  { id: 6, name: "Stadium Golf Club", url: "", advance_booking_days: 7 },
  { id: 7, name: "Van Patten", url: "", advance_booking_days: 7 },
  { id: 8, name: "Eagle Crest", url: "", advance_booking_days: 14 },
];

// --- Types ---
interface BookingRequest {
  id: string; // Changed to string for Firestore UUIDs
  course: number;
  course_name: string;
  desired_date: string;
  earliest_time: string;
  latest_time: string;
  players: number;
  release_time: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED' | 'RUNNING' | 'CANCELLED';
  result_log?: string;
  created_at: string;
  updated_at: string;
}

// --- Components ---

const PasscodeScreen = ({ onLogin }: { onLogin: (p: string) => void }) => {
  const [passcode, setPasscode] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLogin(passcode);
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
                <label className="block text-sm font-bold text-slate-700 mb-2">Access Passcode</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                  <input 
                    type="password" 
                    value={passcode}
                    onChange={(e) => setPasscode(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none font-medium transition-all"
                    placeholder="Enter the secret passcode"
                    required
                  />
                </div>
              </div>
            </div>

            <button 
              type="submit" 
              className="w-full bg-slate-900 text-white font-bold py-4 rounded-xl hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
            >
              Unlock Terminal
              <ChevronRight className="w-4 h-4" />
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


const Sidebar = ({ activeTab, setActiveTab, isOpen, setIsOpen, onLogout }: { 
  activeTab: string, 
  setActiveTab: (t: string) => void,
  isOpen: boolean,
  setIsOpen: (o: boolean) => void,
  onLogout: () => void
}) => {
  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'new-request', icon: PlusCircle, label: 'New Request' }
  ];

  const handleNav = (id: string) => {
    setActiveTab(id);
    setIsOpen(false);
  };

  return (
    <>
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
        </nav>

        <div className="p-6 border-t border-slate-800 bg-slate-900/50">
          <button 
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-slate-700 hover:border-red-500/50 hover:text-red-400 transition-all text-sm font-medium"
          >
            <Lock className="w-4 h-4" />
            <span>Lock Terminal</span>
          </button>
        </div>
      </aside>
    </>
  );
};

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
    CANCELLED: 'bg-slate-100 text-slate-500 border-slate-200',
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold border uppercase tracking-wide whitespace-nowrap shadow-sm ${styles[status] || styles.PENDING}`}>
      <div className={`w-1.5 h-1.5 rounded-full ${styles[status]?.replace('text-', 'bg-') || 'bg-amber-500'}`} />
      {status}
    </span>
  );
};

const BookingTable = ({ bookings, emptyMessage }: { bookings: BookingRequest[], emptyMessage: string }) => (
  <div className="bg-white rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50 overflow-hidden">
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left border-collapse">
        <thead>
          <tr className="bg-slate-50/50 text-slate-400">
            <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px]">Course</th>
            <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px]">Play Window</th>
            <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px] hidden sm:table-cell">Players</th>
            <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px]">Status</th>
            <th className="px-8 py-4 font-bold uppercase tracking-wider text-[10px] hidden md:table-cell">Details</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {bookings.map((booking) => (
            <tr key={booking.id} className="hover:bg-slate-50/50 transition-colors group">
              <td className="px-8 py-5">
                <span className="font-bold text-slate-900 text-base">{booking.course_name}</span>
              </td>
              <td className="px-8 py-5">
                <div className="flex flex-col">
                  <span className="text-slate-900 font-semibold">{new Date(booking.desired_date + 'T12:00:00').toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}</span>
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
              <td className="px-8 py-5 text-slate-500 font-medium text-xs hidden md:table-cell max-w-[200px] truncate">
                {booking.result_log || `Releases: ${new Date(booking.release_time).toLocaleString()}`}
              </td>
            </tr>
          ))}
          {bookings.length === 0 && (
            <tr>
              <td colSpan={5} className="px-8 py-16 text-center">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
                    <Calendar className="w-8 h-8 text-slate-200" />
                  </div>
                  <p className="text-slate-400 font-medium">{emptyMessage}</p>
                </div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  </div>
);

const Dashboard = ({ bookings, isLoading }: { bookings: BookingRequest[], isLoading: boolean }) => {
  if (isLoading) return (
    <div className="flex flex-col items-center justify-center h-64 space-y-4">
      <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-slate-500 font-medium animate-pulse">Scanning the greens...</p>
    </div>
  );

  const activeBookings = bookings.filter(b => b.status === 'PENDING' || b.status === 'RUNNING');
  const successCount = bookings.filter(b => b.status === 'SUCCESS').length;
  const pendingCount = activeBookings.length;
  // Get the most imminent pending job
  const sortedPending = [...activeBookings].sort((a, b) => new Date(a.release_time).getTime() - new Date(b.release_time).getTime());
  const nextRun = sortedPending[0]?.release_time || 'None';

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">Mission Control</h1>
          <p className="text-slate-500 mt-1 font-medium">Overview of all system activity.</p>
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

      <div className="px-1 py-2">
        <h3 className="text-xl font-bold text-slate-900 mb-4">Active & Recent Jobs</h3>
      </div>
      <BookingTable bookings={bookings} emptyMessage="No active bookings. Deploy a seeker!" />
    </div>
  );
};

const NewRequestForm = ({ onSubmit }: { onSubmit: (data: any) => void }) => {
  const [formData, setFormData] = useState({
    course: '',
    desired_date: '',
    earliest_time: '07:00',
    latest_time: '11:00',
    players: '4',
    executionDate: '',
    executionTime: '07:00:00',
    course_email: '',
    course_password: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // Combine date and time for Firestore
    const release_time = new Date(`${formData.executionDate}T${formData.executionTime}`).toISOString();
    
    // Find course name from ID
    const courseObj = AVAILABLE_COURSES.find(c => c.id === Number(formData.course));

    await onSubmit({ 
      ...formData, 
      course: Number(formData.course),
      course_name: courseObj?.name || 'Unknown Course',
      release_time 
    });
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
            {AVAILABLE_COURSES.map((course) => (
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
                  onChange={(e) => setFormData({...formData, course: e.target.value, desired_date: ''})}
                  required
                />
                <div className="flex-1">
                  <span className={`block text-lg font-bold transition-colors ${Number(formData.course) === course.id ? 'text-emerald-900' : 'text-slate-900'}`}>
                    {course.name}
                  </span>
                  <span className="text-xs text-slate-400 font-medium uppercase tracking-widest mt-1 block">
                    {course.advance_booking_days ? `Book up to ${course.advance_booking_days} days out` : 'Active Booking Engine'}
                  </span>
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
              {(() => {
                const selectedCourse = AVAILABLE_COURSES.find(c => c.id === Number(formData.course));
                const today = new Date().toISOString().split('T')[0];
                const maxDate = selectedCourse?.advance_booking_days
                  ? new Date(Date.now() + selectedCourse.advance_booking_days * 86400000).toISOString().split('T')[0]
                  : undefined;
                return (
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2 px-1">Tee Date{maxDate && <span className="text-emerald-500 ml-2 normal-case tracking-normal">(max {selectedCourse?.advance_booking_days} days out)</span>}</label>
                <input 
                  type="date" className="w-full h-14 rounded-2xl bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 border-2 px-5 font-bold text-slate-900 transition-all outline-none"
                  value={formData.desired_date}
                  min={today}
                  max={maxDate}
                  onChange={(e) => setFormData({...formData, desired_date: e.target.value})}
                  required
                />
              </div>
                );
              })()}

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
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-2 px-1">Course Email</label>
                    <input 
                      type="email" placeholder="Required for login"
                      className="w-full h-12 rounded-xl bg-slate-800 border-transparent focus:border-emerald-500 border-2 px-4 text-sm font-medium text-white transition-all outline-none"
                      value={formData.course_email}
                      onChange={(e) => setFormData({...formData, course_email: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-2 px-1">Course Password</label>
                    <input 
                      type="password" placeholder="••••••••"
                      className="w-full h-12 rounded-xl bg-slate-800 border-transparent focus:border-emerald-500 border-2 px-4 text-sm font-medium text-white transition-all outline-none"
                      value={formData.course_password}
                      onChange={(e) => setFormData({...formData, course_password: e.target.value})}
                      required
                    />
                  </div>
                </div>

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
  const [passcode, setPasscode] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [bookings, setBookings] = useState<BookingRequest[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    if (!passcode) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/bookings?passcode=${passcode}`);
      if (res.ok) {
        setBookings(await res.json());
      }
    } catch (err) {
      console.warn("Retrying connection to API...");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (passcode) {
      fetchData();
      const interval = setInterval(fetchData, 10000); // Polling every 10 seconds
      return () => clearInterval(interval);
    }
  }, [passcode]);

  const handleLogin = (code: string) => {
    setPasscode(code);
  };

  const handleLogout = () => {
    setPasscode(null);
    setBookings([]);
    setActiveTab('dashboard');
  };

  const handleNewBooking = async (data: any) => {
    if (!passcode) return;
    try {
      const payload = { ...data, passcode };
      const res = await fetch(`${API_URL}/bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        alert("Bot Armed! Job sent to Firestore.");
        fetchData();
        setActiveTab('dashboard');
      } else {
        const errorData = await res.json();
        alert(`Failed: ${errorData.detail || "Invalid Passcode"}`);
      }
    } catch (e) {
      alert("Lost connection to server.");
    }
  };

  if (!passcode) {
    return <PasscodeScreen onLogin={handleLogin} />;
  }

  return (
    <div className="flex min-h-screen bg-slate-50 font-sans selection:bg-emerald-100 selection:text-emerald-900">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isOpen={isSidebarOpen} 
        setIsOpen={setIsSidebarOpen} 
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
          {activeTab === 'dashboard' && <Dashboard bookings={bookings} isLoading={loading} />}
          {activeTab === 'new-request' && <NewRequestForm onSubmit={handleNewBooking} />}
        </div>
      </main>
    </div>
  );
};

export default App;

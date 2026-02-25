import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { 
  Calendar, 
  Clock, 
  Users, 
  MapPin, 
  Plus, 
  Trash2, 
  Loader2, 
  Search,
  CheckCircle2,
  AlertCircle,
  LayoutGrid
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CustomSelect from '../components/CustomSelect';
import DeleteModal from '../components/DeleteModal';
import ErrorModal from '../components/ErrorModal';

const Schedule = () => {
  const [sessions, setSessions] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [persons, setPersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Creation Form State
  const [externalId, setExternalId] = useState('');
  const [subject, setSubject] = useState('');
  const [selectedBuilding, setSelectedBuilding] = useState('');
  const [selectedRoom, setSelectedRoom] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [selectedPersonIds, setSelectedPersonIds] = useState([]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [sessionsRes, buildingsRes, personsRes] = await Promise.all([
        api.get('/sessions'),
        api.get('/buildings'),
        api.get('/persons')
      ]);
      setSessions(sessionsRes.data);
      setBuildings(buildingsRes.data);
      setPersons(personsRes.data);
      
      // Fetch all rooms from all buildings to build a complete lookup
      const roomsPromises = buildingsRes.data.map(b => api.get(`/buildings/${b.id}/rooms`));
      const roomsResponses = await Promise.all(roomsPromises);
      const allRooms = roomsResponses.flatMap(res => res.data);
      setRooms(allRooms);
    } catch (error) {
      console.error('Error fetching schedule data:', error);
      setErrorMessage('Failed to load schedule data. Please check your connection.');
      setErrorModalOpen(true);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await api.get('/sessions');
      setSessions(response.data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!selectedRoom || selectedPersonIds.length === 0) return;

    try {
      setIsSubmitting(true);
      
      // Convert naive datetime-local strings to UTC ISO strings to prevent double timezone shifts
      const utcStartTime = new Date(startTime).toISOString();
      const utcEndTime = new Date(endTime).toISOString();

      await api.post('/sessions', {
        external_id: externalId,
        room_id: parseInt(selectedRoom, 10),
        subject: subject,
        start_time: utcStartTime,
        end_time: utcEndTime,
        person_ids: selectedPersonIds.map(id => parseInt(id, 10))
      });
      
      await fetchSessions();
      closeModal();
    } catch (error) {
      console.error('Error creating session:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to create session.');
      setErrorModalOpen(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!sessionToDelete) return;

    try {
      setIsDeleting(true);
      await api.delete(`/sessions/${sessionToDelete.id}`);
      setSessions(sessions.filter(s => s.id !== sessionToDelete.id));
      setDeleteModalOpen(false);
      setSessionToDelete(null);
    } catch (error) {
      console.error('Error deleting session:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to delete session.');
      setErrorModalOpen(true);
    } finally {
      setIsDeleting(false);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setExternalId('');
    setSubject('');
    setSelectedBuilding('');
    setSelectedRoom('');
    setStartTime('');
    setEndTime('');
    setSelectedPersonIds([]);
  };

  const togglePerson = (id) => {
    setSelectedPersonIds(prev => 
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  const formatDateTime = (isoString) => {
    const date = new Date(isoString);
    return {
      date: date.toLocaleDateString('uk-UA', { day: 'numeric', month: 'short' }),
      time: date.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
    };
  };

  const getRoomInfo = (roomId) => {
    const room = rooms.find(r => r.id === roomId);
    if (!room) return 'Unknown Room';
    const building = buildings.find(b => b.id === room.building_id);
    return building ? `${building.name} / ${room.name}` : room.name;
  };

  const filteredSessions = sessions.filter(s => 
    s.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.external_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Schedule</h2>
          <p className="text-muted-foreground mt-1">Plan lessons and manage participants.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-primary-foreground px-4 py-2.5 rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-primary/20 hover:opacity-90 transition-all"
        >
          <Plus size={20} />
          Plan New Session
        </button>
      </div>

      <div className="bg-card/40 border border-border rounded-3xl overflow-hidden shadow-sm shadow-black/5 backdrop-blur-md">
        <div className="p-6 border-b border-border bg-secondary/10 flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            <input 
              type="text" 
              placeholder="Search by subject or ID..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-background border border-border rounded-xl py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-secondary/5 text-muted-foreground text-xs uppercase tracking-wider font-bold border-b border-border">
              <tr>
                <th className="px-6 py-4">Subject & ID</th>
                <th className="px-6 py-4">Location</th>
                <th className="px-6 py-4">Time</th>
                <th className="px-6 py-4">Students</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-muted-foreground">
                    <Loader2 className="animate-spin mx-auto mb-2 text-primary" size={32} />
                    <p className="font-medium">Loading timetable...</p>
                  </td>
                </tr>
              ) : filteredSessions.length > 0 ? (
                filteredSessions.map((session) => {
                  const start = formatDateTime(session.start_time);
                  const end = formatDateTime(session.end_time);
                  return (
                    <tr key={session.id} className="hover:bg-secondary/20 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                            <Calendar size={20} />
                          </div>
                          <div>
                            <p className="font-bold leading-tight">{session.subject}</p>
                            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">{session.external_id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-sm">
                          <MapPin size={14} className="text-muted-foreground" />
                          <span className="font-medium">{getRoomInfo(session.room_id)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-1.5 text-xs font-bold text-foreground">
                            <Calendar size={12} className="text-primary" />
                            {start.date}
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
                            <Clock size={12} />
                            {start.time} - {end.time}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5">
                          <div className="px-2 py-0.5 rounded-lg bg-secondary text-primary text-[10px] font-bold">
                            {session.members_count} Members
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={() => {
                            setSessionToDelete(session);
                            setDeleteModalOpen(true);
                          }}
                          className="p-2 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-muted-foreground">
                    <p className="italic">No sessions found.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Creation Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeModal}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="relative w-full max-w-2xl bg-card border border-border rounded-3xl p-8 shadow-2xl"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold mb-6">Plan New Session</h3>
              <form onSubmit={handleCreateSession} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground ml-1">External ID</label>
                    <input
                      type="text"
                      autoFocus
                      value={externalId}
                      onChange={(e) => setExternalId(e.target.value)}
                      className="w-full bg-secondary/30 border border-border rounded-2xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium placeholder:text-muted-foreground/30"
                      placeholder="e.g. MATH-101-2024"
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground ml-1">Subject</label>
                    <input
                      type="text"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      className="w-full bg-secondary/30 border border-border rounded-2xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium placeholder:text-muted-foreground/30"
                      placeholder="e.g. Mathematical Analysis"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <CustomSelect 
                    label="Building"
                    placeholder="Select Building"
                    value={selectedBuilding}
                    options={buildings}
                    onChange={(id) => {
                      setSelectedBuilding(id);
                      setSelectedRoom('');
                    }}
                  />
                  <CustomSelect 
                    label="Room"
                    placeholder="Select Room"
                    value={selectedRoom}
                    options={rooms.filter(r => r.building_id === selectedBuilding)}
                    onChange={(id) => setSelectedRoom(id)}
                    disabled={!selectedBuilding}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground ml-1">Start Time</label>
                    <input
                      type="datetime-local"
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      className="w-full bg-secondary/30 border border-border rounded-2xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground ml-1">End Time</label>
                    <input
                      type="datetime-local"
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      className="w-full bg-secondary/30 border border-border rounded-2xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-sm font-bold flex items-center gap-2">
                      <Users size={16} className="text-primary" />
                      Participants
                    </label>
                    <span className="text-xs font-bold text-primary">{selectedPersonIds.length} Selected</span>
                  </div>
                  <div className="bg-secondary/20 border border-border rounded-2xl p-4 max-h-48 overflow-y-auto grid grid-cols-2 gap-2">
                    {persons.map(person => (
                      <label 
                        key={person.id}
                        className={`flex items-center gap-3 p-3 rounded-xl border transition-all cursor-pointer group ${selectedPersonIds.includes(person.id) ? 'bg-primary/10 border-primary/30 ring-1 ring-primary/20' : 'bg-card/50 border-transparent hover:bg-secondary/50'}`}
                      >
                        <input 
                          type="checkbox"
                          className="hidden"
                          checked={selectedPersonIds.includes(person.id)}
                          onChange={() => togglePerson(person.id)}
                        />
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs transition-colors ${selectedPersonIds.includes(person.id) ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground group-hover:bg-primary/20 group-hover:text-primary'}`}>
                          {person.full_name.split(' ').map(n=>n[0]).join('')}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-bold truncate leading-tight">{person.full_name}</p>
                          <p className="text-[10px] text-muted-foreground font-medium">{person.person_code}</p>
                        </div>
                        {selectedPersonIds.includes(person.id) && <CheckCircle2 size={16} className="text-primary" />}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex gap-4 pt-2">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="flex-1 px-4 py-3 rounded-xl font-bold border border-border hover:bg-secondary transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !selectedRoom || selectedPersonIds.length === 0}
                    className="flex-1 bg-primary text-primary-foreground px-4 py-3 rounded-xl font-bold shadow-lg shadow-primary/20 hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? <Loader2 className="animate-spin" size={20} /> : 'Save Session'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <DeleteModal 
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title="Delete Session?"
        message="Are you sure you want to delete this session"
        itemName={sessionToDelete?.subject}
        isDeleting={isDeleting}
      />

      <ErrorModal 
        isOpen={errorModalOpen}
        onClose={() => setErrorModalOpen(false)}
        message={errorMessage}
      />
    </div>
  );
};

export default Schedule;

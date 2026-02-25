import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { Building2, Plus, Search, Trash2, Edit2, Loader2, ChevronRight, ChevronDown, MapPin } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import DeleteModal from '../components/DeleteModal';
import ErrorModal from '../components/ErrorModal';

const Buildings = () => {
  const [buildings, setBuildings] = useState([]);
  const [roomsByBuilding, setRoomsByBuilding] = useState({}); // { buildingId: [rooms] }
  const [loading, setLoading] = useState(true);
  const [loadingRooms, setLoadingRooms] = useState(new Set()); // Set of building IDs
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('building'); // 'building' or 'room'
  const [modalTitle, setModalTitle] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [expandedBuildings, setExpandedBuildings] = useState(new Set());
  
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteType, setDeleteType] = useState('building'); // 'building' or 'room'
  const [itemToDelete, setItemToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchBuildings();
  }, []);

  const fetchBuildings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/buildings');
      setBuildings(response.data.buildings || response.data || []);
    } catch (error) {
      console.error('Error fetching buildings:', error);
      setBuildings([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchRoomsForBuilding = async (buildingId, force = false) => {
    if (!force && roomsByBuilding[buildingId]) return;

    try {
      setLoadingRooms(prev => new Set(prev).add(buildingId));
      const response = await api.get(`/buildings/${buildingId}/rooms`);
      setRoomsByBuilding(prev => ({
        ...prev,
        [buildingId]: response.data || []
      }));
    } catch (error) {
      console.error(`Error fetching rooms for building ${buildingId}:`, error);
    } finally {
      setLoadingRooms(prev => {
        const next = new Set(prev);
        next.delete(buildingId);
        return next;
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    try {
      setIsSubmitting(true);
      if (modalType === 'building') {
        if (isEditMode && editingItem) {
          await api.patch(`/buildings/${editingItem.id}`, { name: inputValue });
        } else {
          await api.post('/buildings', { name: inputValue });
        }
        fetchBuildings();
      } else {
        // Room logic
        if (isEditMode && editingItem) {
          // PATCH /rooms/{room_id}
          await api.patch(`/rooms/${editingItem.id}`, { name: inputValue });
          fetchRoomsForBuilding(editingItem.building_id, true);
        } else {
          // POST /buildings/{building_id}/rooms
          const buildingId = editingItem.id; // editingItem stores building when adding new room
          await api.post(`/buildings/${buildingId}/rooms`, { name: inputValue });
          fetchRoomsForBuilding(buildingId, true);
        }
      }
      
      setInputValue('');
      setIsModalOpen(false);
      setIsEditMode(false);
      setEditingItem(null);
    } catch (error) {
      console.error('Error saving:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to save.');
      setErrorModalOpen(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditClick = (item, type) => {
    setModalType(type);
    setEditingItem(item);
    setInputValue(item.name);
    setIsEditMode(true);
    setIsModalOpen(true);
  };
  
  const handleAddBuildingClick = () => {
    setModalType('building');
    setEditingItem(null);
    setInputValue('');
    setIsEditMode(false);
    setIsModalOpen(true);
  };

  const handleAddRoomClick = (building) => {
    setModalType('room');
    setEditingItem(building); // Use editingItem to store the building we're adding research to
    setInputValue('');
    setIsEditMode(false);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setIsEditMode(false);
    setEditingItem(null);
    setInputValue('');
  };

  const handleDeleteClick = (item, type) => {
    setDeleteType(type);
    setItemToDelete(item);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!itemToDelete) return;

    try {
      setIsDeleting(true);
      if (deleteType === 'building') {
        await api.delete(`/buildings/${itemToDelete.id}`);
        setBuildings(buildings.filter(b => b.id !== itemToDelete.id));
      } else {
        await api.delete(`/rooms/${itemToDelete.id}`);
        // Refresh rooms for the specific building
        if (itemToDelete.building_id) {
          fetchRoomsForBuilding(itemToDelete.building_id, true);
        }
      }
      setDeleteModalOpen(false);
      setItemToDelete(null);
    } catch (error) {
      console.error('Error deleting:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to delete. It might be in use.');
      setErrorModalOpen(true);
    } finally {
      setIsDeleting(false);
    }
  };

  const toggleBuildingExpanded = (buildingId) => {
    const newExpanded = new Set(expandedBuildings);
    if (newExpanded.has(buildingId)) {
      newExpanded.delete(buildingId);
    } else {
      newExpanded.add(buildingId);
      // Fetch rooms when expanding
      fetchRoomsForBuilding(buildingId);
    }
    setExpandedBuildings(newExpanded);
  };

  const filteredBuildings = buildings.filter(b => 
    b.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Buildings</h2>
          <p className="text-muted-foreground mt-1">Manage university infrastructure and locations.</p>
        </div>
        <button 
          onClick={handleAddBuildingClick}
          className="bg-primary text-primary-foreground px-4 py-2.5 rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-primary/20 hover:opacity-90 transition-all"
        >
          <Plus size={20} />
          Add Building
        </button>
      </div>

      <div className="bg-card/40 border border-border rounded-3xl overflow-hidden shadow-sm shadow-black/5 backdrop-blur-md">
        <div className="p-6 border-b border-border bg-secondary/10 flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            <input 
              type="text" 
              placeholder="Filter buildings..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-background border border-border rounded-xl py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
            />
          </div>
        </div>

        <div className="divide-y divide-border">
          {loading ? (
            <div className="p-12 flex flex-col items-center justify-center text-muted-foreground gap-3">
              <Loader2 className="animate-spin" size={32} />
              <p className="font-medium">Loading buildings...</p>
            </div>
          ) : filteredBuildings.length > 0 ? (
            filteredBuildings.map((building) => {
              const buildingRooms = roomsByBuilding[building.id] || [];
              const isExpanded = expandedBuildings.has(building.id);
              const isLoadingRooms = loadingRooms.has(building.id);
              
              return (
                <div key={building.id} className="divide-y divide-border/50">
                  <div className="p-4 flex items-center justify-between hover:bg-secondary/20 transition-colors group">
                    <div className="flex items-center gap-4">
                      <button 
                        onClick={() => toggleBuildingExpanded(building.id)}
                        className={`p-1.5 rounded-lg transition-all ${isExpanded ? 'bg-primary/10 text-primary rotate-90' : 'hover:bg-secondary text-muted-foreground'}`}
                      >
                        <ChevronRight size={18} />
                      </button>
                      <div className="w-12 h-12 rounded-2xl bg-secondary flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground group-hover:scale-110 transition-all duration-300">
                        <Building2 size={24} />
                      </div>
                      <div>
                        <h4 className="font-bold text-lg leading-tight">{building.name}</h4>
                        <div className="flex items-center gap-3 mt-0.5">
                          <p className="text-xs text-muted-foreground font-medium">ID: {building.id}</p>
                          <span className="w-1 h-1 rounded-full bg-border" />
                          <p className="text-xs font-bold text-primary flex items-center gap-1">
                            <MapPin size={10} />
                            {buildingRooms.length} {buildingRooms.length === 1 ? 'room' : 'rooms'}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleAddRoomClick(building)}
                        className="bg-secondary text-foreground px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-primary hover:text-primary-foreground transition-all flex items-center gap-1.5"
                      >
                        <Plus size={14} />
                        Add Room
                      </button>
                      <div className="w-px h-6 bg-border mx-1" />
                      <button 
                        onClick={() => handleEditClick(building, 'building')}
                        className="p-2 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-all"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button 
                        onClick={() => handleDeleteClick(building, 'building')}
                        className="p-2 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                  
                  {/* Nested Rooms */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden bg-secondary/5"
                      >
                        <div className="pl-16 pr-4 py-2 space-y-1">
                          {isLoadingRooms ? (
                            <div className="p-8 flex flex-col items-center justify-center text-muted-foreground gap-2">
                              <Loader2 className="animate-spin" size={24} />
                              <p className="text-sm font-medium">Loading rooms...</p>
                            </div>
                          ) : buildingRooms.length > 0 ? (
                            buildingRooms.map((room) => (
                              <div key={room.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-secondary/40 transition-all border border-transparent hover:border-border/50 group/room">
                                <div className="flex items-center gap-3">
                                  <div className="w-8 h-8 rounded-lg bg-border/40 flex items-center justify-center text-muted-foreground group-hover/room:bg-primary/10 group-hover/room:text-primary transition-all">
                                    <MapPin size={16} />
                                  </div>
                                  <div>
                                    <span className="font-bold">{room.name}</span>
                                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Audience / Room</p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover/room:opacity-100 transition-opacity">
                                  <button 
                                    onClick={() => handleEditClick(room, 'room')}
                                    className="p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-all"
                                  >
                                    <Edit2 size={14} />
                                  </button>
                                  <button 
                                    onClick={() => handleDeleteClick(room, 'room')}
                                    className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="p-8 text-center border-2 border-dashed border-border rounded-2xl">
                              <p className="text-sm text-muted-foreground font-medium italic">No rooms assigned to this building yet.</p>
                              <button 
                                onClick={() => handleAddRoomClick(building)}
                                className="mt-2 text-xs font-bold text-primary hover:underline underline-offset-4"
                              >
                                Click here to add the first room
                              </button>
                            </div>
                          )}
                          <div className="h-2" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })
          ) : (
            <div className="p-12 text-center text-muted-foreground">
              <p>No buildings found.</p>
            </div>
          )}
        </div>
      </div>

      {/* Basic Modal for Adding Building */}
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
              className="relative w-full max-w-md bg-card border border-border rounded-3xl p-8 shadow-2xl"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold mb-6">
                {isEditMode ? (modalType === 'building' ? 'Edit Building' : 'Edit Room') : (modalType === 'building' ? 'Add New Building' : 'Add New Room')}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium text-muted-foreground ml-1">
                    {modalType === 'building' ? 'Building Name' : `Room Name (in ${editingItem?.name || ''})`}
                  </label>
                  <input
                    type="text"
                    autoFocus
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    className="w-full bg-secondary/50 border border-border rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                    placeholder={modalType === 'building' ? 'e.g. Building A' : 'e.g. 214'}
                    required
                  />
                </div>
                {modalType === 'room' && !isEditMode && (
                  <p className="text-[10px] text-muted-foreground font-medium italic mt-2">
                    Creating a room in <span className="text-primary font-bold">"{editingItem?.name}"</span>.
                  </p>
                )}
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="flex-1 px-4 py-3 rounded-xl font-bold border border-border hover:bg-secondary transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 bg-primary text-primary-foreground px-4 py-3 rounded-xl font-bold shadow-lg shadow-primary/20 hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? <Loader2 className="animate-spin" size={20} /> : (isEditMode ? 'Save Changes' : 'Create')}
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
        title={deleteType === 'building' ? 'Delete Building?' : 'Delete Room?'}
        message="Are you sure you want to delete"
        itemName={deleteType === 'building' ? itemToDelete?.name : itemToDelete?.name}
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

export default Buildings;

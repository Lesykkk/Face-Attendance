import React, { useState, useEffect, useRef } from 'react';
import api from '../api/axios';
import { User, UserPlus, Trash2, Edit2, Plus, Loader2, Camera, X, Check, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import DeleteModal from '../components/DeleteModal';
import ErrorModal from '../components/ErrorModal';

const Persons = () => {
  const [persons, setPersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingPerson, setEditingPerson] = useState(null);
  
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [personToDelete, setPersonToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Form state
  const [fullName, setFullName] = useState('');
  const [personCode, setPersonCode] = useState('');
  const [role, setRole] = useState('student');
  const [photos, setPhotos] = useState([]);

  useEffect(() => {
    fetchPersons();
  }, []);

  const fetchPersons = async () => {
    try {
      setLoading(true);
      const response = await api.get('/persons');
      setPersons(response.data.persons || response.data || []);
    } catch (error) {
      console.error('Error fetching persons:', error);
      setPersons([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotos(prev => [...prev, reader.result]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removePhoto = (index) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!isEditMode && photos.length === 0) {
      alert('Please upload at least one photo for face recognition');
      return;
    }

    try {
      setIsSubmitting(true);
      
      if (isEditMode && editingPerson) {
        // PATCH /api/persons/{id}
        await api.patch(`/persons/${editingPerson.id}`, {
          full_name: fullName,
          person_code: personCode,
          role
        });
      } else {
        // POST /api/persons
        await api.post('/persons', {
          full_name: fullName,
          person_code: personCode,
          role,
          photos: photos.map(p => p.split(',')[1]) // Remove base64 prefix
        });
      }
      
      handleCloseModal();
      fetchPersons();
    } catch (error) {
      console.error('Error saving person:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to save person data. Check if the code is unique.');
      setErrorModalOpen(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditClick = (person) => {
    setEditingPerson(person);
    setFullName(person.full_name);
    setPersonCode(person.person_code);
    setRole(person.role);
    setPhotos([]); // Photos are not edited via PATCH
    setIsEditMode(true);
    setIsModalOpen(true);
  };

  const handleDeleteClick = (person) => {
    setPersonToDelete(person);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!personToDelete) return;
    try {
      setIsDeleting(true);
      await api.delete(`/persons/${personToDelete.id}`);
      setPersons(persons.filter(p => p.id !== personToDelete.id));
      setDeleteModalOpen(false);
      setPersonToDelete(null);
    } catch (error) {
      console.error('Error deleting person:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to delete person. They might be referenced in logs or sessions.');
      setErrorModalOpen(true);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setIsEditMode(false);
    setEditingPerson(null);
    setFullName('');
    setPersonCode('');
    setRole('student');
    setPhotos([]);
  };

  const filteredPersons = persons.filter(p => 
    p.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.person_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Persons</h2>
          <p className="text-muted-foreground mt-1">Manage students, teachers, and staff biometric data.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-primary-foreground px-4 py-2.5 rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-primary/20 hover:opacity-90 transition-all"
        >
          <Plus size={20} />
          Register Person
        </button>
      </div>

      <div className="bg-card/40 border border-border rounded-3xl overflow-hidden shadow-sm shadow-black/5 backdrop-blur-md">
        <div className="p-6 border-b border-border bg-secondary/10 flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            <input 
              type="text" 
              placeholder="Search by name or code..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-background border border-border rounded-xl py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-secondary/10 text-muted-foreground text-xs uppercase tracking-wider font-bold">
              <tr>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">ID Code</th>
                <th className="px-6 py-4">Role</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center">
                    <Loader2 className="animate-spin mx-auto text-muted-foreground mb-2" size={32} />
                    <p className="text-muted-foreground font-medium">Loading persons...</p>
                  </td>
                </tr>
              ) : filteredPersons.length > 0 ? (
                filteredPersons.map((person) => (
                  <tr key={person.id} className="hover:bg-secondary/20 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-2xl bg-secondary flex items-center justify-center font-bold text-primary group-hover:scale-110 transition-all duration-300 shadow-inner">
                          {person.full_name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <span className="font-semibold">{person.full_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm font-mono text-muted-foreground">{person.person_code}</td>
                    <td className="px-6 py-4 text-sm capitalize">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        person.role === 'student' ? 'bg-blue-100 text-blue-700' : 
                        person.role === 'teacher' ? 'bg-purple-100 text-purple-700' : 
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {person.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleEditClick(person)}
                          className="p-2 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-all"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button 
                          onClick={() => handleDeleteClick(person)}
                          className="p-2 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="px-6 py-12 text-center text-muted-foreground">
                    No persons registered yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Registration Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleCloseModal}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="relative w-full max-w-2xl bg-card border border-border rounded-3xl p-8 shadow-2xl max-h-[90vh] overflow-auto"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-2xl font-bold mb-6">
                {isEditMode ? 'Edit Person' : 'Register Person'}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground ml-1">Full Name</label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full bg-secondary/50 border border-border rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                      placeholder="e.g. John Doe"
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground ml-1">ID / Person Code</label>
                    <input
                      type="text"
                      value={personCode}
                      onChange={(e) => setPersonCode(e.target.value)}
                      className="w-full bg-secondary/50 border border-border rounded-xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono"
                      placeholder="e.g. STU-001"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium text-muted-foreground ml-1">Role</label>
                  <div className="flex gap-2">
                    {['student', 'teacher', 'staff'].map((r) => (
                      <button
                        key={r}
                        type="button"
                        onClick={() => setRole(r)}
                        className={`flex-1 py-2 px-4 rounded-xl border transition-all capitalize font-bold ${
                          role === r 
                          ? 'bg-primary text-primary-foreground border-primary shadow-md' 
                          : 'bg-background border-border text-muted-foreground hover:bg-secondary'
                        }`}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                {!isEditMode && (
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-muted-foreground ml-1 flex justify-between">
                      Photos for Embeddings <span>{photos.length} uploaded</span>
                    </label>
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                      <label className="aspect-square border-2 border-dashed border-border rounded-xl flex flex-col items-center justify-center gap-2 text-muted-foreground hover:text-primary hover:border-primary transition-all cursor-pointer bg-secondary/20">
                        <Camera size={24} />
                        <span className="text-[10px] font-bold uppercase">Upload</span>
                        <input type="file" multiple accept="image/*" onChange={handlePhotoUpload} className="hidden" />
                      </label>
                      {photos.map((photo, i) => (
                        <div key={i} className="relative aspect-square rounded-xl overflow-hidden border border-border group shadow-sm">
                          <img src={photo} alt="" className="w-full h-full object-cover" />
                          <button 
                            onClick={() => removePhoto(i)}
                            className="absolute top-1 right-1 p-1 bg-destructive/80 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all shadow-md"
                          >
                            <X size={12} />
                          </button>
                        </div>
                      ))}
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-2 italic">* Photos are used to generate 128D embeddings and will be discarded by the server.</p>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="flex-1 px-4 py-3 rounded-xl font-bold border border-border hover:bg-secondary transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 bg-primary text-primary-foreground px-4 py-3 rounded-xl font-bold shadow-lg shadow-primary/20 hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? <Loader2 className="animate-spin" size={20} /> : (isEditMode ? 'Save Changes' : 'Complete Registration')}
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
        title="Delete Person?"
        message="Are you sure you want to delete"
        itemName={personToDelete?.full_name}
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

export default Persons;

import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { Cpu, Camera, Plus, Trash2, Shield, Key, Loader2, Server, Video, ChevronRight, Edit2, ChevronDown, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CustomSelect from '../components/CustomSelect';
import DeleteModal from '../components/DeleteModal';
import ErrorModal from '../components/ErrorModal';

const Hardware = () => {
  const [nodes, setNodes] = useState([]);
  const [camerasByNode, setCamerasByNode] = useState({}); // { nodeId: [cameras] }
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [loadingCameras, setLoadingCameras] = useState(new Set()); // Set of node IDs
  
  // Unified Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('node'); // 'node' or 'camera'
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Node Creation specific (to show API key)
  const [newNodeKey, setNewNodeKey] = useState(null);

  // Form Inputs
  const [nodeName, setNodeName] = useState('');
  const [cameraRtsp, setCameraRtsp] = useState('');
  
  // Common Delete/Error Modal State
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  const [deleteType, setDeleteType] = useState('node'); // 'node' or 'camera'
  const [isDeleting, setIsDeleting] = useState(false);
  
  const [errorModalOpen, setErrorModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Camera Location Form Inputs (only used during creation)
  const [cameraBuilding, setCameraBuilding] = useState('');
  const [cameraRoom, setCameraRoom] = useState('');

  useEffect(() => {
    fetchNodes();
  }, []);

  const fetchNodes = async () => {
    try {
      setLoading(true);
      const response = await api.get('/hardware/nodes');
      setNodes(response.data || []);
    } catch (error) {
      console.error('Error fetching nodes:', error);
      setNodes([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchCamerasForNode = async (nodeId, force = false) => {
    if (!force && camerasByNode[nodeId]) return;

    try {
      setLoadingCameras(prev => new Set(prev).add(nodeId));
      const response = await api.get(`/hardware/nodes/${nodeId}/cameras`);
      setCamerasByNode(prev => ({
        ...prev,
        [nodeId]: response.data || []
      }));
    } catch (error) {
      console.error(`Error fetching cameras for node ${nodeId}:`, error);
    } finally {
      setLoadingCameras(prev => {
        const next = new Set(prev);
        next.delete(nodeId);
        return next;
      });
    }
  };

  const toggleNodeExpanded = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
      fetchCamerasForNode(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      
      if (modalType === 'node') {
        if (!nodeName.trim()) return;
        if (isEditMode && editingItem) {
          await api.patch(`/hardware/nodes/${editingItem.id}`, { name: nodeName });
          fetchNodes();
          resetModalState();
        } else {
          const response = await api.post('/hardware/nodes', { name: nodeName });
          setNewNodeKey(response.data.api_key); // Shows the success screen with key
          fetchNodes();
          // Do NOT reset state here because we need to show the key
        }
      } else {
        // Camera logic
        if (!cameraRtsp.trim()) return;
        if (isEditMode && editingItem) {
          await api.patch(`/hardware/cameras/${editingItem.id}`, { 
            rtsp_url: cameraRtsp 
          });
          fetchCamerasForNode(editingItem.edge_node_id, true);
        } else {
          if (!cameraBuilding || !cameraRoom) {
            setErrorMessage('Building and Room are required when adding a new camera');
            setErrorModalOpen(true);
            setIsSubmitting(false);
            return;
          }
          const nodeId = editingItem.id; // When adding, editingItem is the Node
          await api.post(`/hardware/nodes/${nodeId}/cameras`, {
            room_id: parseInt(cameraRoom, 10),
            rtsp_url: cameraRtsp
          });
          fetchCamerasForNode(nodeId, true);
        }
        resetModalState();
      }
    } catch (error) {
      console.error('Error saving:', error);
      setErrorMessage(error.response?.data?.detail || 'Failed to save.');
      setErrorModalOpen(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!itemToDelete) return;

    try {
      setIsDeleting(true);
      if (deleteType === 'node') {
        await api.delete(`/hardware/nodes/${itemToDelete.id}`);
        setNodes(nodes.filter(n => n.id !== itemToDelete.id));
      } else {
        await api.delete(`/hardware/cameras/${itemToDelete.id}`);
        fetchCamerasForNode(itemToDelete.edge_node_id, true);
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

  const resetModalState = () => {
    setIsModalOpen(false);
    setIsEditMode(false);
    setEditingItem(null);
    setNodeName('');
    setCameraRtsp('');
    setCameraBuilding('');
    setCameraRoom('');
  };

  // State for Room Selection Modal
  const [buildings, setBuildings] = useState([]);
  const [roomsByBuilding, setRoomsByBuilding] = useState({});

  useEffect(() => {
    if (modalType === 'camera' && !isEditMode && isModalOpen) {
      // Fetch buildings so user can pick a room
      api.get('/buildings').then(res => setBuildings(res.data)).catch(console.error);
    }
  }, [modalType, isEditMode, isModalOpen]);

  useEffect(() => {
    if (cameraBuilding && !roomsByBuilding[cameraBuilding]) {
      api.get(`/buildings/${cameraBuilding}/rooms`)
        .then(res => setRoomsByBuilding(prev => ({ ...prev, [cameraBuilding]: res.data })))
        .catch(console.error);
    }
  }, [cameraBuilding, roomsByBuilding]);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Hardware</h2>
          <p className="text-muted-foreground mt-1">Register and monitor Edge Nodes and IP Cameras.</p>
        </div>
        <button 
          onClick={() => {
            setModalType('node');
            setNewNodeKey(null);
            setIsEditMode(false);
            setEditingItem(null);
            setNodeName('');
            setIsModalOpen(true);
          }}
          className="bg-primary text-primary-foreground px-4 py-2.5 rounded-xl font-bold flex items-center gap-2 shadow-lg shadow-primary/20 hover:opacity-90 transition-all"
        >
          <Cpu size={20} />
          Register Edge Node
        </button>
      </div>

      <div className="bg-card/40 border border-border rounded-3xl overflow-hidden shadow-sm shadow-black/5 backdrop-blur-md">
        <div className="p-6 border-b border-border bg-secondary/10 flex items-center gap-4">
          <div className="relative flex-1">
            <h3 className="text-lg font-bold ml-2">Edge Nodes</h3>
          </div>
        </div>

        <div className="divide-y divide-border">
          {loading ? (
            <div className="p-12 text-center text-muted-foreground flex flex-col items-center gap-3">
              <Loader2 className="animate-spin" size={32} />
              <p>Scanning network...</p>
            </div>
          ) : nodes.length > 0 ? (
            nodes.map((node) => {
              const nodeCameras = camerasByNode[node.id] || [];
              const isExpanded = expandedNodes.has(node.id);
              const isLoadingCameras = loadingCameras.has(node.id);
              
              return (
                <div key={node.id} className="divide-y divide-border/50">
                  <div className="p-4 flex items-center justify-between hover:bg-secondary/20 transition-colors group">
                    <div className="flex items-center gap-4">
                      <button 
                        onClick={() => toggleNodeExpanded(node.id)}
                        className={`p-1.5 rounded-lg transition-all ${isExpanded ? 'bg-primary/10 text-primary rotate-90' : 'hover:bg-secondary text-muted-foreground'}`}
                      >
                        <ChevronRight size={18} />
                      </button>
                      <div className="w-12 h-12 rounded-2xl bg-green-100 flex items-center justify-center text-green-600 shadow-inner group-hover:scale-110 transition-transform duration-300">
                        <Server size={24} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-lg leading-tight">{node.name}</h4>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-green-500/10 text-green-600">
                            Online
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-0.5">
                          <p className="text-xs text-muted-foreground font-medium">Node ID: {node.id}</p>
                          <span className="w-1 h-1 rounded-full bg-border" />
                          <p className="text-xs font-bold text-primary flex items-center gap-1">
                            <Camera size={10} />
                            {nodeCameras.length} {nodeCameras.length === 1 ? 'camera' : 'cameras'}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => {
                          setModalType('camera');
                          setIsEditMode(false);
                          setEditingItem(node); // Passing node to bind camera
                          setCameraRtsp('');
                          setIsModalOpen(true);
                        }}
                        className="bg-secondary text-foreground px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-primary hover:text-primary-foreground transition-all flex items-center gap-1.5"
                      >
                        <Plus size={14} />
                        Add Camera
                      </button>
                      <div className="w-px h-6 bg-border mx-1" />
                      <button 
                        onClick={() => {
                          setModalType('node');
                          setIsEditMode(true);
                          setEditingItem(node);
                          setNodeName(node.name);
                          setIsModalOpen(true);
                        }}
                        className="p-2 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-all"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button 
                        onClick={() => {
                          setDeleteType('node');
                          setItemToDelete(node);
                          setDeleteModalOpen(true);
                        }}
                        className="p-2 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                  
                  {/* Nested Cameras */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden bg-secondary/5"
                      >
                        <div className="pl-16 pr-4 py-2 space-y-1">
                          {isLoadingCameras ? (
                            <div className="p-8 flex flex-col items-center justify-center text-muted-foreground gap-2">
                              <Loader2 className="animate-spin" size={24} />
                              <p className="text-sm font-medium">Loading connected cameras...</p>
                            </div>
                          ) : nodeCameras.length > 0 ? (
                            nodeCameras.map((camera) => (
                              <div key={camera.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-secondary/40 transition-all border border-transparent hover:border-border/50 group/camera">
                                <div className="flex items-center gap-3">
                                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${camera.is_active ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive'}`}>
                                    <Video size={16} />
                                  </div>
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="font-mono text-sm font-bold">{camera.rtsp_url}</span>
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5">
                                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Camera ID: {camera.id}</p>
                                      <span className="w-1 h-1 rounded-full bg-border" />
                                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">Room ID: {camera.room_id}</p>
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover/camera:opacity-100 transition-opacity">
                                  <button 
                                    onClick={() => {
                                      setModalType('camera');
                                      setIsEditMode(true);
                                      setEditingItem(camera);
                                      setCameraRtsp(camera.rtsp_url);
                                      setIsModalOpen(true);
                                    }}
                                    className="p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-all"
                                  >
                                    <Edit2 size={14} />
                                  </button>
                                  <button 
                                    onClick={() => {
                                      setDeleteType('camera');
                                      setItemToDelete(camera);
                                      setDeleteModalOpen(true);
                                    }}
                                    className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="p-8 text-center border-2 border-dashed border-border rounded-2xl">
                              <p className="text-sm text-muted-foreground font-medium italic">No cameras connected to this node yet.</p>
                              <button 
                                onClick={() => {
                                  setModalType('camera');
                                  setIsEditMode(false);
                                  setEditingItem(node);
                                  setCameraRtsp('');
                                  setIsModalOpen(true);
                                }}
                                className="mt-2 text-xs font-bold text-primary hover:underline underline-offset-4"
                              >
                                Click here to add the first camera
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
            <div className="p-12 text-center text-muted-foreground border-2 border-dashed border-border rounded-2xl m-4">
              <p>No Edge Nodes registered.</p>
            </div>
          )}
        </div>
      </div>
      {/* Unified Registration/Update Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={resetModalState}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className={`relative w-full ${modalType === 'node' && !newNodeKey ? 'max-w-md' : 'max-w-lg'} bg-card border border-border rounded-3xl p-8 shadow-2xl`}
              onClick={e => e.stopPropagation()}
            >
              {modalType === 'node' && newNodeKey ? (
                // Node Registration Success State
                <div className="space-y-6">
                  <div className="flex flex-col items-center">
                    <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-4">
                      <Shield size={32} />
                    </div>
                    <h3 className="text-2xl font-bold text-center">Node Registered!</h3>
                    <p className="text-muted-foreground text-center text-sm mt-1">Copy this API Key. You won't be able to see it again.</p>
                  </div>

                  <div className="bg-secondary/50 p-4 rounded-xl border border-border flex items-center justify-between group shadow-inner">
                    <span className="font-mono text-sm break-all font-bold">{newNodeKey}</span>
                    <button 
                      onClick={() => navigator.clipboard.writeText(newNodeKey)}
                      className="p-2 ml-4 rounded-lg bg-background border border-border hover:bg-primary hover:text-primary-foreground transition-all shadow-sm"
                    >
                      <Key size={18} />
                    </button>
                  </div>

                  <button
                    onClick={resetModalState}
                    className="w-full bg-primary text-primary-foreground py-3 rounded-xl font-bold shadow-lg shadow-primary/20 hover:opacity-90 transition-all"
                  >
                    Done
                  </button>
                </div>
              ) : (
                // Standard Form (Node Edit/Create | Camera Edit/Create)
                <>
                  <h3 className="text-2xl font-bold mb-6">
                    {modalType === 'node' 
                      ? (isEditMode ? 'Edit Edge Node' : 'Register Edge Node')
                      : (isEditMode ? 'Edit Camera' : 'Register Camera')
                    }
                  </h3>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    
                    {modalType === 'node' && (
                      <div className="space-y-1">
                        <label className="text-sm font-medium text-muted-foreground ml-1">Node Name</label>
                        <input
                          type="text"
                          autoFocus
                          value={nodeName}
                          onChange={(e) => setNodeName(e.target.value)}
                          className="w-full bg-secondary/30 border border-border rounded-2xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium placeholder:text-muted-foreground/50"
                          placeholder="e.g. Building A Main"
                          required
                        />
                      </div>
                    )}

                    {modalType === 'camera' && (
                      <>
                        <div className="space-y-1">
                          <label className="text-sm font-medium text-muted-foreground ml-1">RTSP Stream URL</label>
                          <input
                            type="text"
                            autoFocus
                            value={cameraRtsp}
                            onChange={(e) => setCameraRtsp(e.target.value)}
                            className="w-full bg-secondary/30 border border-border rounded-2xl py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono text-sm placeholder:text-muted-foreground/50"
                            placeholder="rtsp://user:pass@192.168.1.100:554/stream"
                            required
                          />
                        </div>

                        {/* Location Fields - Only during creation */}
                        {!isEditMode && (
                          <div className="grid grid-cols-2 gap-4">
                            <CustomSelect
                              label="Building"
                              value={cameraBuilding}
                              options={buildings}
                              onChange={(id) => {
                                setCameraBuilding(id);
                                setCameraRoom('');
                              }}
                              placeholder="Select Building"
                            />
                            <CustomSelect
                              label="Room"
                              value={cameraRoom}
                              options={roomsByBuilding[cameraBuilding] || []}
                              onChange={(id) => setCameraRoom(id)}
                              placeholder="Select Room"
                              disabled={!cameraBuilding}
                            />
                          </div>
                        )}
                        {!isEditMode && (
                          <p className="text-xs text-muted-foreground ml-1 mt-2">
                            Assigning to Node: <span className="font-bold">{editingItem?.name}</span>
                          </p>
                        )}
                      </>
                    )}

                    <div className="flex gap-3 pt-4">
                      <button
                        type="button"
                        onClick={resetModalState}
                        className="flex-1 px-4 py-3 rounded-xl font-bold border border-border hover:bg-secondary transition-all"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isSubmitting || (modalType === 'camera' && !isEditMode && !cameraRoom)}
                        className="flex-1 bg-primary text-primary-foreground px-4 py-3 rounded-xl font-bold shadow-lg shadow-primary/20 hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        {isSubmitting ? (
                          <Loader2 className="animate-spin" size={20} />
                        ) : (
                          modalType === 'node' && !isEditMode ? 'Generate Key' : 'Save Changes'
                        )}
                      </button>
                    </div>
                  </form>
                </>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <DeleteModal 
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={confirmDelete}
        title={`Delete ${deleteType === 'node' ? 'Edge Node' : 'Camera'}?`}
        message="Are you sure you want to delete"
        itemName={deleteType === 'node' ? `"${itemToDelete?.name}"` : `Camera ${itemToDelete?.id}`}
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

export default Hardware;

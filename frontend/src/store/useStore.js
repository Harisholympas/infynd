import { create } from 'zustand'

const useStore = create((set) => ({
  // Navigation
  activeView: 'dashboard',   // dashboard | workflows | editor | connections | history | settings
  setActiveView: (v) => set({ activeView: v }),
  
  // Workflow editor state
  editingWorkflow: null,
  setEditingWorkflow: (wf) => set({ editingWorkflow: wf }),
  
  // Data
  workflows: [],
  connections: [],
  apps: [],
  analytics: null,
  setWorkflows: (w) => set({ workflows: w }),
  setConnections: (c) => set({ connections: c }),
  setApps: (a) => set({ apps: a }),
  setAnalytics: (a) => set({ analytics: a }),
  addWorkflow: (w) => set(s => ({ workflows: [w, ...s.workflows] })),
  removeWorkflow: (id) => set(s => ({ workflows: s.workflows.filter(w => w.id !== id) })),
  updateWorkflow: (id, patch) => set(s => ({
    workflows: s.workflows.map(w => w.id === id ? { ...w, ...patch } : w)
  })),
  
  // Notifications
  notifications: [],
  notify: (msg, type='info') => {
    const id = Date.now()
    set(s => ({ notifications: [...s.notifications, { id, msg, type }] }))
    setTimeout(() => set(s => ({ notifications: s.notifications.filter(n => n.id !== id) })), 4500)
  },
  dismissNotif: (id) => set(s => ({ notifications: s.notifications.filter(n => n.id !== id) })),
}))

export default useStore

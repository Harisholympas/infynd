import React from 'react'
import { Zap, LayoutDashboard, GitBranch, Plug, History, BarChart3 } from 'lucide-react'
import useStore from '../store/useStore'
import clsx from 'clsx'

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'workflows', label: 'Workflows', icon: GitBranch },
  { id: 'connections', label: 'Connections', icon: Plug },
  { id: 'history', label: 'History', icon: History },
  { id: 'analyze', label: 'Analyze', icon: BarChart3 },
]

export default function Sidebar() {
  const { activeView, setActiveView, workflows } = useStore()
  const activeCount = workflows.filter(w => w.status === 'on').length

  return (
    <aside className="fixed left-0 top-0 h-full w-56 bg-white border-r border-gray-200 flex flex-col z-40 shadow-sm">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-gray-200">
        <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-blue-600 rounded-lg flex items-center justify-center" style={{boxShadow:'0 0 16px rgba(99, 102, 241, 0.3)'}}>
          <Zap size={16} className="text-white" fill="white" />
        </div>
        <div>
          <div className="text-sm font-bold text-gray-900 tracking-tight">AutoFlow</div>
          <div className="text-[10px] text-gray-500">Workflow Platform</div>
        </div>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-0.5">
        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveView(id)}
            className={clsx(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
              activeView === id || (id === 'workflows' && activeView === 'editor')
                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-sm'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            )}>
            <Icon size={15} className="flex-shrink-0" />
            <span>{label}</span>
            {id === 'workflows' && activeCount > 0 && (
              <span className="ml-auto bg-emerald-100 text-emerald-700 text-[10px] px-1.5 py-0.5 rounded-full border border-emerald-300 font-mono">
                {activeCount} on
              </span>
            )}
          </button>
        ))}
      </nav>

      <div className="p-3 border-t border-gray-200">
        <div className="flex items-center gap-2 px-3 py-2">
          <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center">
            <span className="text-[10px] font-bold text-indigo-600">U</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-gray-900 truncate">Local User</div>
            <div className="text-[10px] text-gray-500">Free Plan</div>
          </div>
        </div>
      </div>
    </aside>
  )
}

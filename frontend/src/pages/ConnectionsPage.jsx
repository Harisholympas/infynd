import React, { useState, useEffect } from 'react'
import { Plug, Loader2, Trash2, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { connectionAPI } from '../utils/api'
import useStore from '../store/useStore'
import { APP_COLORS } from '../utils/constants'
import clsx from 'clsx'
import AddConnectionModal from '../components/AddConnectionModal'

function ConnectionCard({ conn, onTest, onDelete, testing }) {
  const color = APP_COLORS[conn.app_key] || '#4f63f3'
  const isOk = conn.status === 'active'

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-start gap-3 group shadow-sm">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
        style={{ background: `${color}10`, border: `1px solid ${color}20` }}>
        <span className="text-base">🔌</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-sm font-medium text-gray-900 truncate">{conn.name}</span>
          <span className={clsx('badge text-[10px]',
            isOk ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200')}>
            {isOk ? '● Connected' : '● Error'}
          </span>
        </div>
        <div className="text-xs text-gray-600 font-mono">{conn.app_key}</div>
        {conn.last_tested_at && (
          <div className="text-[10px] text-gray-500 mt-1">
            Tested {new Date(conn.last_tested_at).toLocaleDateString()}
          </div>
        )}
      </div>
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button onClick={() => onTest(conn.id)} disabled={testing === conn.id}
          className="w-7 h-7 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700 flex items-center justify-center transition-all"
          title="Test connection">
          {testing === conn.id ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
        </button>
        <button onClick={() => onDelete(conn.id)}
          className="w-7 h-7 rounded-lg hover:bg-red-50 text-gray-500 hover:text-red-600 flex items-center justify-center transition-all"
          title="Remove">
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  )
}

export default function ConnectionsPage() {
  const { apps, connections, setConnections, notify } = useStore()
  const [showModal, setShowModal] = useState(null)
  const [testing, setTesting] = useState(null)
  const [showApps, setShowApps] = useState(true)
  const [appSearch, setAppSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')

  const categories = ['all', ...new Set(apps.map(a => a.category))]

  const filteredApps = apps.filter(a => {
    const matchSearch = !appSearch || a.name.toLowerCase().includes(appSearch.toLowerCase())
    const matchCat = categoryFilter === 'all' || a.category === categoryFilter
    return matchSearch && matchCat
  })

  const handleTest = async (connId) => {
    setTesting(connId)
    try {
      const res = await connectionAPI.test(connId)
      setConnections(connections.map(c => c.id === connId ? { ...c, status: res.ok ? 'active' : 'error', last_tested_at: new Date().toISOString() } : c))
      notify(res.ok ? `✓ ${res.detail || 'Connection verified'}` : `✗ ${res.detail || 'Connection failed'}`,
        res.ok ? 'success' : 'error')
    } catch (err) { notify(err.message, 'error') }
    finally { setTesting(null) }
  }

  const handleDelete = async (connId) => {
    if (!confirm('Remove this connection?')) return
    try {
      await connectionAPI.delete(connId)
      setConnections(connections.filter(c => c.id !== connId))
      notify('Connection removed', 'info')
    } catch (err) { notify(err.message, 'error') }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      <div>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Plug size={20} className="text-indigo-600" /> Connections
        </h1>
        <p className="text-sm text-gray-600 mt-0.5">Connect your apps to use in workflows</p>
      </div>

      {/* Connected accounts */}
      {connections.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-widest mb-3">
            Connected Accounts ({connections.length})
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {connections.map(conn => (
              <ConnectionCard key={conn.id} conn={conn} testing={testing}
                onTest={handleTest} onDelete={handleDelete} />
            ))}
          </div>
        </div>
      )}

      {/* App directory */}
      <div>
        <button onClick={() => setShowApps(s => !s)}
          className="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-widest mb-3 hover:text-gray-900 transition-colors">
          Add New Connection
          {showApps ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>

        {showApps && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative flex-1 max-w-xs">
                <input className="input text-sm pl-3" placeholder="Search apps..." value={appSearch} onChange={e => setAppSearch(e.target.value)} />
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                {categories.map(cat => (
                  <button key={cat} onClick={() => setCategoryFilter(cat)}
                    className={clsx('px-2.5 py-1 rounded-full text-xs transition-all capitalize',
                      categoryFilter === cat ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-gray-100 text-gray-600 hover:text-gray-900')}>
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {filteredApps.map(app => {
                const connected = connections.filter(c => c.app_key === app.key)
                const color = APP_COLORS[app.key] || '#4f63f3'
                return (
                  <button key={app.key} onClick={() => setShowModal(app)}
                    className="bg-white border border-gray-200 hover:border-gray-300 rounded-xl p-4 text-left transition-all group relative shadow-sm">
                    {connected.length > 0 && (
                      <div className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-emerald-500" />
                    )}
                    <div className="text-2xl mb-2">{app.icon}</div>
                    <div className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors">{app.name}</div>
                    <div className="text-[10px] text-gray-600 mt-0.5">{app.category}</div>
                    <div className="flex items-center gap-2 mt-2 text-[10px] text-gray-600">
                      {app.trigger_count > 0 && <span>{app.trigger_count} trigger{app.trigger_count !== 1 ? 's' : ''}</span>}
                      {app.action_count > 0 && <span>{app.action_count} action{app.action_count !== 1 ? 's' : ''}</span>}
                    </div>
                    {connected.length > 0 && (
                      <div className="text-[10px] text-emerald-600 mt-1">{connected.length} connected</div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <AddConnectionModal app={showModal}
          onClose={() => setShowModal(null)}
          onAdded={(newConn) => setConnections([...connections, newConn])} />
      )}
    </div>
  )
}

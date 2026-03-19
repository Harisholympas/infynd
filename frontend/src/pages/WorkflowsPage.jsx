import React, { useState } from 'react'
import { Plus, Play, Trash2, ToggleLeft, ToggleRight, Search, GitBranch, Loader2, Clock, CheckCircle, XCircle, Zap } from 'lucide-react'
import { workflowAPI } from '../utils/api'
import useStore from '../store/useStore'
import { STATUS_STYLES } from '../utils/constants'
import clsx from 'clsx'

const SORT_OPTIONS = ['name', 'updated_at', 'run_count']

export default function WorkflowsPage() {
  const { workflows, setActiveView, setEditingWorkflow, notify, updateWorkflow, removeWorkflow, addWorkflow } = useStore()
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('updated_at')
  const [running, setRunning] = useState(null)
  const [toggling, setToggling] = useState(null)

  const filtered = workflows
    .filter(w => !search || w.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sort === 'name') return a.name.localeCompare(b.name)
      if (sort === 'run_count') return (b.run_count || 0) - (a.run_count || 0)
      return new Date(b.updated_at || 0) - new Date(a.updated_at || 0)
    })

  const handleNew = () => { setEditingWorkflow(null); setActiveView('editor') }
  const handleEdit = (wf) => { setEditingWorkflow(wf); setActiveView('editor') }

  const handleToggle = async (wf, e) => {
    e.stopPropagation()
    setToggling(wf.id)
    try {
      const res = await workflowAPI.toggle(wf.id)
      updateWorkflow(wf.id, { status: res.status })
      notify(`"${wf.name}" turned ${res.status}`, 'success')
    } catch (err) { notify(err.message, 'error') }
    finally { setToggling(null) }
  }

  const handleRun = async (wf, e) => {
    e.stopPropagation()
    setRunning(wf.id)
    try {
      const res = await workflowAPI.run(wf.id, { trigger: 'manual' })
      notify(res.status === 'success' ? `✓ "${wf.name}" completed` : `"${wf.name}" ${res.status}`,
        res.status === 'success' ? 'success' : 'error')
      updateWorkflow(wf.id, { run_count: (wf.run_count || 0) + 1 })
    } catch (err) { notify(err.message, 'error') }
    finally { setRunning(null) }
  }

  const handleDelete = async (wf, e) => {
    e.stopPropagation()
    if (!confirm(`Delete "${wf.name}"?`)) return
    try {
      await workflowAPI.delete(wf.id)
      removeWorkflow(wf.id)
      notify(`"${wf.name}" deleted`, 'info')
    } catch (err) { notify(err.message, 'error') }
  }

  const handleDuplicate = async (wf, e) => {
    e.stopPropagation()
    try {
      const trigger_cfg = typeof wf.trigger_config === 'string' ? JSON.parse(wf.trigger_config) : (wf.trigger_config || {})
      const payload = {
        name: `${wf.name} (copy)`,
        description: wf.description || '',
        trigger: {
          type: trigger_cfg.type || 'manual',
          app_key: trigger_cfg.app_key || null,
          connection_id: trigger_cfg.connection_id || null,
          config: trigger_cfg.config || {}
        },
        steps: typeof wf.steps === 'string' ? JSON.parse(wf.steps) : (wf.steps || []),
        folder: wf.folder || '',
        tags: typeof wf.tags === 'string' ? JSON.parse(wf.tags) : (wf.tags || [])
      }
      const res = await workflowAPI.create(payload)
      addWorkflow({ ...res, ...payload, run_count: 0, error_count: 0, updated_at: new Date().toISOString() })
      notify(`Duplicated as "${payload.name}"`, 'success')
    } catch (err) { notify(err.message, 'error') }
  }

  const TRIGGER_ICON = { schedule: '🗓️', webhook: '🔗', manual: '▶️', rss: '📡', app_event: '⚡' }

  return (
    <div className="space-y-5 animate-fade-in max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <GitBranch size={24} className="text-indigo-600" /> Workflows
          </h1>
          <p className="text-sm text-gray-600 mt-0.5">{workflows.length} workflows · {workflows.filter(w => w.status === 'on').length} active</p>
        </div>
        <button onClick={handleNew} className="btn-primary">
          <Plus size={14} /> New Workflow
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input className="input pl-8 text-sm" placeholder="Search workflows..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="input w-36 text-sm" value={sort} onChange={e => setSort(e.target.value)}>
          <option value="updated_at">Recently updated</option>
          <option value="name">Name A–Z</option>
          <option value="run_count">Most runs</option>
        </select>
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl py-16 text-center shadow-sm">
          <GitBranch size={32} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">{search ? 'No workflows match your search' : 'No workflows yet'}</p>
          {!search && (
            <button onClick={handleNew} className="btn-primary mx-auto mt-4">
              <Plus size={14} /> Create your first workflow
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          {/* Table header */}
          <div className="grid grid-cols-12 gap-2 px-5 py-3 border-b border-gray-200 text-[11px] font-semibold text-gray-600 uppercase tracking-widest bg-gray-50">
            <div className="col-span-5">Name</div>
            <div className="col-span-2">Trigger</div>
            <div className="col-span-1 text-center">Runs</div>
            <div className="col-span-1 text-center">Errors</div>
            <div className="col-span-2">Last run</div>
            <div className="col-span-1"></div>
          </div>

          {filtered.map((wf, i) => {
            const st = STATUS_STYLES[wf.status] || STATUS_STYLES.off
            const trigger_cfg = typeof wf.trigger_config === 'string' ? JSON.parse(wf.trigger_config || '{}') : (wf.trigger_config || {})
            const triggerIcon = TRIGGER_ICON[trigger_cfg.type || wf.trigger_type] || '▶️'
            const steps = typeof wf.steps === 'string' ? JSON.parse(wf.steps || '[]') : (wf.steps || [])
            const isRunning = running === wf.id
            const isToggling = toggling === wf.id

            return (
              <div key={wf.id}
                className="grid grid-cols-12 gap-2 px-5 py-3.5 border-b border-gray-200 last:border-0 hover:bg-gray-50 cursor-pointer transition-colors group items-center"
                onClick={() => handleEdit(wf)}>

                {/* Name + status */}
                <div className="col-span-5 flex items-center gap-3 min-w-0">
                  <div className={clsx('w-2 h-2 rounded-full flex-shrink-0', st.dot)} />
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">{wf.name}</div>
                    <div className="text-[10px] text-gray-500">{steps.length} step{steps.length !== 1 ? 's' : ''}</div>
                  </div>
                </div>

                {/* Trigger */}
                <div className="col-span-2 text-xs text-gray-600 flex items-center gap-1.5">
                  <span>{triggerIcon}</span>
                  <span className="truncate capitalize">{trigger_cfg.type || wf.trigger_type || 'manual'}</span>
                </div>

                {/* Run count */}
                <div className="col-span-1 text-center">
                  <span className="text-sm font-mono text-gray-700">{wf.run_count || 0}</span>
                </div>

                {/* Error count */}
                <div className="col-span-1 text-center">
                  <span className={clsx('text-sm font-mono', (wf.error_count || 0) > 0 ? 'text-red-600' : 'text-gray-500')}>
                    {wf.error_count || 0}
                  </span>
                </div>

                {/* Last run */}
                <div className="col-span-2 text-[10px] text-gray-500 font-mono">
                  {wf.last_run_at ? new Date(wf.last_run_at).toLocaleString([], { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) : '—'}
                </div>

                {/* Actions */}
                <div className="col-span-1 flex items-center gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                  <button title="Run" onClick={e => handleRun(wf, e)}
                    className="w-6 h-6 rounded hover:bg-indigo-100 text-gray-500 hover:text-indigo-600 flex items-center justify-center transition-all">
                    {isRunning ? <Loader2 size={11} className="animate-spin" /> : <Play size={11} />}
                  </button>
                  <button title="Duplicate" onClick={e => handleDuplicate(wf, e)}
                    className="w-6 h-6 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 flex items-center justify-center transition-all text-[10px]">
                    ⧉
                  </button>
                  <button title="Delete" onClick={e => handleDelete(wf, e)}
                    className="w-6 h-6 rounded hover:bg-red-100 text-gray-500 hover:text-red-600 flex items-center justify-center transition-all">
                    <Trash2 size={11} />
                  </button>
                </div>

                {/* Toggle at the very end */}
                <div className="col-span-12 -mt-1 flex justify-between items-center" onClick={e => e.stopPropagation()}>
                  <div />
                  <button onClick={e => handleToggle(wf, e)}
                    className={clsx('flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full border transition-all', st.bg, st.text, st.border)}>
                    {isToggling ? <Loader2 size={9} className="animate-spin" /> :
                      wf.status === 'on' ? <ToggleRight size={11} /> : <ToggleLeft size={11} />}
                    {wf.status === 'on' ? 'On' : 'Off'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

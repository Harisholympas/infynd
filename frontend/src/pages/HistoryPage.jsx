import React, { useEffect, useState, useCallback } from 'react'
import { History, CheckCircle, XCircle, Clock, RefreshCw, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react'
import { workflowAPI } from '../utils/api'
import useStore from '../store/useStore'
import clsx from 'clsx'

const STATUS_CONFIG = {
  success: { icon: CheckCircle, color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', dot: 'bg-emerald-500' },
  error:   { icon: XCircle,    color: 'text-red-700',     bg: 'bg-red-50',     border: 'border-red-200',     dot: 'bg-red-500' },
  halted:  { icon: AlertCircle,color: 'text-amber-700',   bg: 'bg-amber-50',   border: 'border-amber-200',   dot: 'bg-amber-500' },
  running: { icon: Clock,      color: 'text-blue-700',    bg: 'bg-blue-50',    border: 'border-blue-200',    dot: 'bg-blue-500' },
  skipped: { icon: Clock,      color: 'text-gray-700',    bg: 'bg-gray-50',    border: 'border-gray-200',    dot: 'bg-gray-500' },
}

function StepResult({ step, index }) {
  const [open, setOpen] = useState(false)
  const cfg = STATUS_CONFIG[step.status] || STATUS_CONFIG.running
  const Icon = cfg.icon
  return (
    <div className={clsx('rounded-lg border overflow-hidden', cfg.border, cfg.bg)}>
      <button onClick={() => setOpen(o => !o)} className="w-full flex items-center gap-2.5 px-3 py-2 text-left">
        <Icon size={12} className={cfg.color} />
        <span className="text-xs text-gray-700 flex-1">{index + 1}. {step.app_key} · {step.action}</span>
        <span className={clsx('text-[10px] font-medium', cfg.color)}>{step.status}</span>
        {open ? <ChevronDown size={12} className="text-gray-500" /> : <ChevronRight size={12} className="text-gray-500" />}
      </button>
      {open && step.output && (
        <div className="px-3 pb-3">
          <pre className="text-[11px] text-gray-700 font-mono bg-gray-100 rounded p-2 overflow-auto max-h-48">
            {JSON.stringify(step.output, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function RunRow({ run, workflowName }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = STATUS_CONFIG[run.status] || STATUS_CONFIG.running
  const Icon = cfg.icon
  const steps = typeof run.steps_results === 'string'
    ? JSON.parse(run.steps_results || '[]') : (run.steps_results || [])
  const trigger = typeof run.trigger_data === 'string'
    ? JSON.parse(run.trigger_data || '{}') : (run.trigger_data || {})

  return (
    <div className="border-b border-gray-200 last:border-0">
      <button onClick={() => setExpanded(o => !o)}
        className="w-full grid grid-cols-12 gap-2 px-5 py-3 hover:bg-gray-50 transition-colors text-left items-center">
        <div className="col-span-1 flex justify-center">
          <Icon size={13} className={cfg.color} />
        </div>
        <div className="col-span-4 text-sm text-gray-900 truncate font-medium">{workflowName || run.workflow_id?.slice(0,8)}</div>
        <div className="col-span-2">
          <span className={clsx('badge text-[10px]', cfg.bg, cfg.color, `border ${cfg.border}`)}>
            {run.status}
          </span>
        </div>
        <div className="col-span-2 text-xs text-gray-600 font-mono">
          {run.duration_ms ? `${run.duration_ms}ms` : '—'}
        </div>
        <div className="col-span-2 text-[10px] text-gray-600">
          {run.started_at ? new Date(run.started_at).toLocaleString([], { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) : '—'}
        </div>
        <div className="col-span-1 flex justify-end">
          <span className="text-[10px] text-gray-600">{steps.length} steps</span>
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-4 space-y-3 animate-slide-up">
          {/* Trigger data */}
          <div>
            <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1.5">Trigger Input</div>
            <pre className="text-[11px] text-gray-700 font-mono bg-gray-50 rounded-lg p-3 overflow-auto max-h-24">
              {JSON.stringify(trigger, null, 2)}
            </pre>
          </div>

          {/* Step results */}
          {steps.length > 0 && (
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1.5">Steps</div>
              <div className="space-y-1.5">
                {steps.map((step, i) => <StepResult key={i} step={step} index={i} />)}
              </div>
            </div>
          )}

          {/* Error message */}
          {run.error_message && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="text-[10px] text-red-700 font-semibold mb-1">Error</div>
              <div className="text-xs text-red-600">{run.error_message}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function HistoryPage() {
  const { workflows, notify } = useStore()
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterWorkflow, setFilterWorkflow] = useState('all')

  const loadRuns = useCallback(async () => {
    setLoading(true)
    try {
      const res = await workflowAPI.getAllRuns(200)
      setRuns(res.runs || [])
    } catch (err) { notify(err.message, 'error') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadRuns() }, [loadRuns])

  const wfMap = Object.fromEntries(workflows.map(w => [w.id, w.name]))

  const filtered = runs.filter(r => {
    const matchStatus = filterStatus === 'all' || r.status === filterStatus
    const matchWf = filterWorkflow === 'all' || r.workflow_id === filterWorkflow
    return matchStatus && matchWf
  })

  const stats = {
    total: runs.length,
    success: runs.filter(r => r.status === 'success').length,
    error: runs.filter(r => r.status === 'error').length,
    avgDuration: runs.filter(r => r.duration_ms).length > 0
      ? Math.round(runs.filter(r => r.duration_ms).reduce((a, r) => a + r.duration_ms, 0) / runs.filter(r => r.duration_ms).length)
      : 0
  }

  return (
    <div className="space-y-5 animate-fade-in max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <History size={20} className="text-indigo-600" /> Run History
          </h1>
          <p className="text-sm text-gray-600 mt-0.5">Complete log of all workflow executions</p>
        </div>
        <button onClick={loadRuns} disabled={loading} className="btn-secondary py-1.5">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Total Runs', value: stats.total, color: '#6366f1' },
          { label: 'Successful', value: stats.success, color: '#10b981' },
          { label: 'Failed', value: stats.error, color: '#ef4444' },
          { label: 'Avg Duration', value: stats.avgDuration ? `${stats.avgDuration}ms` : '—', color: '#f59e0b' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm">
            <div className="text-xl font-bold text-gray-900 font-mono" style={{ color }}>{value}</div>
            <div className="text-[10px] text-gray-600 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <select className="input w-40 text-sm" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="all">All statuses</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
          <option value="halted">Halted</option>
        </select>
        <select className="input w-48 text-sm" value={filterWorkflow} onChange={e => setFilterWorkflow(e.target.value)}>
          <option value="all">All workflows</option>
          {workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <span className="text-xs text-gray-600">{filtered.length} run{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 gap-2 px-5 py-2.5 border-b border-gray-200 text-[10px] font-semibold text-gray-600 uppercase tracking-widest">
          <div className="col-span-1"></div>
          <div className="col-span-4">Workflow</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2">Duration</div>
          <div className="col-span-2">Started</div>
          <div className="col-span-1 text-right">Steps</div>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12">
            <History size={28} className="text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600 text-sm">No runs yet</p>
            <p className="text-gray-500 text-xs mt-1">Turn on a workflow and run it to see history here</p>
          </div>
        ) : (
          filtered.map(run => (
            <RunRow key={run.id} run={run} workflowName={wfMap[run.workflow_id]} />
          ))
        )}
      </div>
    </div>
  )
}

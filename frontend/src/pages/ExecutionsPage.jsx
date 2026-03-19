import React, { useEffect, useState } from 'react'
import { Activity, CheckCircle, XCircle, Clock } from 'lucide-react'
import { executionAPI } from '../utils/api'
import ExecutionLog from '../components/ExecutionLog'
import clsx from 'clsx'

export default function ExecutionsPage() {
  const [execs, setExecs] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    executionAPI.history(null, 50)
      .then(d => setExecs(d.executions || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const StatusIcon = ({ status }) => {
    if (status === 'completed') return <CheckCircle size={13} className="text-accent-green" />
    if (status === 'failed' || status === 'error') return <XCircle size={13} className="text-accent-red" />
    return <Clock size={13} className="text-accent-amber" />
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Activity size={20} className="text-brand-400" /> Executions
        </h1>
        <p className="text-sm text-slate-500 mt-1">Agent execution history and logs</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="space-y-2">
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="w-6 h-6 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
            </div>
          ) : execs.length === 0 ? (
            <div className="card text-center py-12">
              <Activity size={28} className="text-slate-700 mx-auto mb-2" />
              <p className="text-slate-500 text-sm">No executions yet</p>
            </div>
          ) : (
            execs.map(exec => (
              <button
                key={exec.id}
                onClick={() => setSelected(exec)}
                className={clsx(
                  'card w-full text-left hover:border-white/10 transition-all',
                  selected?.id === exec.id && 'border-brand-500/30 bg-brand-500/5'
                )}
              >
                <div className="flex items-center gap-3">
                  <StatusIcon status={exec.status} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-slate-300 truncate font-mono">
                      {exec.agent_id?.slice(0, 8)}...
                    </div>
                    <div className="text-[10px] text-slate-600">
                      {exec.started_at ? new Date(exec.started_at).toLocaleString() : ''}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={clsx('badge text-[10px]',
                      exec.status === 'completed' ? 'bg-accent-green/10 text-accent-green' :
                      exec.status === 'failed' ? 'bg-accent-red/10 text-accent-red' :
                      'bg-accent-amber/10 text-accent-amber'
                    )}>{exec.status}</span>
                    {exec.duration_ms && (
                      <div className="text-[10px] text-slate-600 mt-0.5 font-mono">{exec.duration_ms}ms</div>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="card sticky top-0">
          {selected ? (
            <ExecutionLog execution={selected} />
          ) : (
            <div className="flex items-center justify-center h-40 text-slate-600 text-sm">
              Select an execution to view details
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import React, { useState } from 'react'
import { Play, Trash2, ChevronDown, ChevronUp, Zap, Clock, CheckCircle } from 'lucide-react'
import { executionAPI, agentAPI } from '../utils/api'
import useStore from '../store/useStore'
import { DEPT_COLORS, DEPT_ICONS, STATUS_COLORS } from '../utils/constants'
import clsx from 'clsx'

export default function AgentCard({ agent, onDeleted }) {
  const [expanded, setExpanded] = useState(false)
  const [running, setRunning] = useState(false)
  const { addNotification, addExecution } = useStore()

  const blueprint = typeof agent.blueprint === 'string' ? JSON.parse(agent.blueprint) : agent.blueprint
  const color = DEPT_COLORS[agent.department] || '#4f63f3'
  const icon = DEPT_ICONS[agent.department] || '🤖'
  const steps = blueprint?.steps || []
  const tools = blueprint?.tools || []

  const handleRun = async () => {
    setRunning(true)
    try {
      const result = await executionAPI.run(agent.id, { triggered_by: 'manual' })
      addExecution(result)
      addNotification({ type: 'success', message: `Agent "${agent.name}" executed successfully` })
    } catch (err) {
      addNotification({ type: 'error', message: `Execution failed: ${err.message}` })
    } finally {
      setRunning(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Delete agent "${agent.name}"?`)) return
    try {
      await agentAPI.delete(agent.id)
      onDeleted?.(agent.id)
      addNotification({ type: 'info', message: `Agent "${agent.name}" deleted` })
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  return (
    <div className="card hover:border-gray-300 transition-all duration-300 group animate-fade-in">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
          style={{ background: `${color}10`, border: `1px solid ${color}20` }}
        >
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-gray-900 truncate">{agent.name}</h3>
            <span className={clsx('badge', STATUS_COLORS.active.bg, STATUS_COLORS.active.text)}>
              <span className={clsx('status-dot', STATUS_COLORS.active.dot)} />
              active
            </span>
          </div>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            <span className="text-xs text-gray-600">{agent.department}</span>
            <span className="text-gray-400">·</span>
            <span className="text-xs text-gray-600">{agent.role}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleRun}
            disabled={running}
            className="w-8 h-8 rounded-lg bg-indigo-100 hover:bg-indigo-200 text-indigo-600 flex items-center justify-center transition-all"
            title="Run agent"
          >
            {running ? (
              <div className="w-3 h-3 border border-indigo-400 border-t-indigo-600 rounded-full animate-spin" />
            ) : (
              <Play size={12} />
            )}
          </button>
          <button
            onClick={handleDelete}
            className="w-8 h-8 rounded-lg bg-red-100 hover:bg-red-200 text-red-600 flex items-center justify-center transition-all"
            title="Delete"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>

      {/* Description */}
      {agent.description && (
        <p className="text-xs text-gray-600 mt-2 line-clamp-2">{agent.description}</p>
      )}

      {/* Stats row */}
      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center gap-1.5 text-xs text-gray-600">
          <Zap size={11} style={{ color }} />
          <span>{agent.execution_count || 0} runs</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-gray-600">
          <CheckCircle size={11} className="text-emerald-600" />
          <span>{((agent.success_rate || 0) * 100).toFixed(0)}% success</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-gray-600 ml-auto">
          <Clock size={11} />
          <span>{tools.length} tools</span>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-gray-600 hover:text-gray-900 transition-colors"
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 space-y-3 animate-slide-up">
          {steps.length > 0 && (
            <div>
              <div className="section-title">Workflow Steps</div>
              <ol className="space-y-1">
                {steps.map((step, i) => (
                  <li key={i} className="flex gap-2 text-xs text-gray-700">
                    <span className="text-gray-600 flex-shrink-0 font-mono">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
          {tools.length > 0 && (
            <div>
              <div className="section-title">Tools</div>
              <div className="flex flex-wrap gap-1.5">
                {tools.map((tool) => (
                  <span key={tool} className="badge bg-gray-100 text-gray-700 font-mono">
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

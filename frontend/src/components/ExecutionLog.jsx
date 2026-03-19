import React from 'react'
import { CheckCircle, XCircle, Clock, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const STATUS_ICON = {
  completed: <CheckCircle size={13} className="text-emerald-600" />,
  failed: <XCircle size={13} className="text-red-600" />,
  error: <XCircle size={13} className="text-red-600" />,
  running: <div className="w-3 h-3 border border-amber-400/50 border-t-amber-600 rounded-full animate-spin" />,
  skipped: <Clock size={13} className="text-gray-600" />,
}

export default function ExecutionLog({ execution }) {
  if (!execution) return null

  const stepsLog = typeof execution.steps_log === 'string'
    ? JSON.parse(execution.steps_log || '[]')
    : execution.steps_log || []

  const output = typeof execution.output_data === 'string'
    ? JSON.parse(execution.output_data || '{}')
    : execution.output_data || {}

  return (
    <div className="space-y-3 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {STATUS_ICON[execution.status] || STATUS_ICON.running}
          <span className="text-sm font-medium text-gray-900 capitalize">{execution.status}</span>
        </div>
        {execution.duration_ms && (
          <span className="text-xs text-gray-600 font-mono">{execution.duration_ms}ms</span>
        )}
      </div>

      {/* Steps */}
      {stepsLog.length > 0 && (
        <div className="space-y-2">
          <div className="section-title">Execution Steps</div>
          {stepsLog.map((step, i) => (
            <div key={i} className="flex gap-2.5 items-start">
              <div className="flex-shrink-0 mt-0.5">
                {STATUS_ICON[step.status] || STATUS_ICON.completed}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-gray-900 truncate">{step.step}</div>
                {step.output && (
                  <div className="text-xs text-gray-600 mt-0.5 line-clamp-2">{step.output}</div>
                )}
                {step.tool_used && (
                  <span className="text-[10px] font-mono text-indigo-600 mt-0.5 inline-block">
                    tool: {step.tool_used}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Output */}
      {output.final_output && (
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <div className="section-title">Output</div>
          <p className="text-xs text-gray-700 leading-relaxed">{output.final_output}</p>
        </div>
      )}
    </div>
  )
}

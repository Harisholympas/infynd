import React, { useEffect, useState } from 'react'
import { Pickaxe, TrendingUp, Plus, Loader2 } from 'lucide-react'
import { miningAPI, agentAPI } from '../utils/api'
import useStore from '../store/useStore'

export default function PatternsPage() {
  const { addNotification, addAgent } = useStore()
  const [patterns, setPatterns] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(null)

  useEffect(() => {
    Promise.all([
      miningAPI.patterns().then(d => setPatterns(d.patterns || [])),
      miningAPI.suggestions().then(d => setSuggestions(d.suggestions || []))
    ]).finally(() => setLoading(false))
  }, [])

  const handleCreateFromSuggestion = async (suggestion) => {
    setCreating(suggestion.pattern_id)
    try {
      const result = await agentAPI.generate({
        department: suggestion.department,
        role: suggestion.role,
        task_description: suggestion.task_description
      })
      addAgent({
        id: result.agent_id, name: result.blueprint.agent_name,
        department: suggestion.department, role: suggestion.role,
        description: result.blueprint.description, blueprint: result.blueprint,
        status: 'active', execution_count: 0, success_rate: 0,
        created_at: new Date().toISOString()
      })
      addNotification({ type: 'success', message: `Agent "${result.blueprint.agent_name}" created from pattern!` })
      setSuggestions(s => s.filter(x => x.pattern_id !== suggestion.pattern_id))
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    } finally {
      setCreating(null)
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Pickaxe size={20} className="text-indigo-600" /> Task Pattern Miner
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Automatically detects repeated tasks and suggests agents
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {/* Agent Suggestions */}
          {suggestions.length > 0 && (
            <div className="card border-amber-200 bg-amber-50">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={14} className="text-amber-600" />
                <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
                  Suggested Agents ({suggestions.length})
                </span>
              </div>
              <div className="space-y-3">
                {suggestions.map((s, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-amber-200">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900">{s.suggested_agent_name}</div>
                      <div className="text-xs text-gray-600 mt-0.5">{s.department} · {s.role}</div>
                      <div className="text-xs text-gray-700 mt-1 line-clamp-2">{s.task_description}</div>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="badge bg-amber-100 text-amber-700 text-[10px]">
                          {s.frequency}× repeated
                        </span>
                        <span className="badge bg-indigo-100 text-indigo-700 text-[10px]">
                          {Math.round((s.confidence || 0.7) * 100)}% confidence
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleCreateFromSuggestion(s)}
                      disabled={creating === s.pattern_id}
                      className="btn-primary flex-shrink-0 py-1.5"
                    >
                      {creating === s.pattern_id ? (
                        <Loader2 size={12} className="animate-spin" />
                      ) : (
                        <Plus size={12} />
                      )}
                      Create
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All Patterns */}
          <div className="card">
            <div className="section-title">Detected Task Patterns ({patterns.length})</div>
            {patterns.length === 0 ? (
              <div className="text-center py-8">
                <Pickaxe size={28} className="text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600 text-sm">No patterns detected yet</p>
                <p className="text-gray-500 text-xs mt-1">
                  Patterns emerge as you use the platform. Build more agents first.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {patterns.map((p, i) => (
                  <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-200 last:border-0">
                    <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-bold text-gray-700 font-mono">{p.frequency}x</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-gray-900 truncate">{p.task_description}</div>
                      <div className="text-[10px] text-gray-600">{p.department} · {p.role}</div>
                    </div>
                    <div className="text-[10px] text-gray-600 font-mono flex-shrink-0">
                      {p.last_seen ? new Date(p.last_seen).toLocaleDateString() : ''}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { Zap, Filter } from 'lucide-react'
import { agentAPI } from '../utils/api'
import useStore from '../store/useStore'
import AgentCard from '../components/AgentCard'
import { DEPARTMENTS } from '../utils/constants'

export default function AgentsPage() {
  const { agents, setAgents, removeAgent } = useStore()
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    agentAPI.list().then(d => setAgents(d.agents || [])).catch(console.error).finally(() => setLoading(false))
  }, [])

  const filtered = filter ? agents.filter(a => a.department === filter) : agents

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Zap size={20} className="text-indigo-600" /> My Agents
          </h1>
          <p className="text-sm text-gray-600 mt-1">{agents.length} agents across all departments</p>
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-600" />
          <select className="select w-44 text-sm" value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="">All Departments</option>
            {DEPARTMENTS.map(d => <option key={d}>{d}</option>)}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-16">
          <Zap size={32} className="text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">{filter ? `No agents for ${filter}` : 'No agents created yet'}</p>
          <p className="text-gray-500 text-xs mt-1">Use the Agent Builder to create your first agent</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filtered.map(agent => (
            <AgentCard key={agent.id} agent={agent} onDeleted={removeAgent} />
          ))}
        </div>
      )}
    </div>
  )
}

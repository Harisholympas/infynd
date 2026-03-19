import React, { useEffect, useState } from 'react'
import { BarChart3, TrendingUp, Clock, Target } from 'lucide-react'
import { analyticsAPI, ragAPI } from '../utils/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
         LineChart, Line, CartesianGrid, Cell } from 'recharts'
import { DEPT_COLORS } from '../utils/constants'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs bg-white border border-gray-200">
      <div className="text-gray-900 font-medium mb-1">{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || p.fill || '#6366f1' }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
        </div>
      ))}
    </div>
  )
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null)
  const [ragStats, setRagStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsAPI.summary().then(setSummary),
      ragAPI.stats().then(setRagStats),
    ]).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex justify-center py-16">
      <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
    </div>
  )

  const agentPerfData = (summary?.agent_stats || []).map(a => ({
    name: a.name?.slice(0, 16) + (a.name?.length > 16 ? '…' : ''),
    runs: a.executions || 0,
    success: Math.round((a.success_rate || 0) * 100),
    fill: DEPT_COLORS[a.department] || '#6366f1'
  }))

  const deptData = (summary?.top_departments || []).map(d => ({
    name: d.department, agents: d.count, fill: DEPT_COLORS[d.department] || '#6366f1'
  }))

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 size={20} className="text-indigo-600" /> Analytics
        </h1>
        <p className="text-sm text-gray-600 mt-1">Platform performance and usage insights</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Agents', value: summary?.total_agents ?? 0, icon: Target, color: '#6366f1' },
          { label: 'Executions', value: summary?.total_executions ?? 0, icon: TrendingUp, color: '#0891b2' },
          { label: 'Success Rate', value: `${summary?.success_rate ?? 0}%`, icon: BarChart3, color: '#059669' },
          { label: 'Hours Saved', value: `${summary?.time_saved_hours ?? 0}h`, icon: Clock, color: '#d97706' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card text-center">
            <Icon size={20} className="mx-auto mb-2" style={{ color }} />
            <div className="text-2xl font-bold text-gray-900 font-mono">{value}</div>
            <div className="text-xs text-gray-600 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card">
          <div className="section-title">Agent Executions</div>
          {agentPerfData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={agentPerfData} barSize={20}>
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 9 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey="runs" radius={[3,3,0,0]}>
                  {agentPerfData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-gray-600 text-sm">Run agents to see data</div>
          )}
        </div>

        <div className="card">
          <div className="section-title">Agents per Department</div>
          {deptData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={deptData} barSize={20} layout="vertical">
                <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 9 }} axisLine={false} tickLine={false} width={80} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey="agents" radius={[0,3,3,0]}>
                  {deptData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-gray-600 text-sm">No agents yet</div>
          )}
        </div>
      </div>

      {/* RAG Stats */}
      {ragStats && (
        <div className="card">
          <div className="section-title">RAG Knowledge Base</div>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-gray-900">{ragStats.document_count}</div>
              <div className="text-xs text-gray-600">Documents Indexed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-emerald-600">
                {ragStats.status === 'active' ? '●' : '○'}
              </div>
              <div className="text-xs text-gray-600">
                {ragStats.status === 'active' ? 'Active' : 'Inactive'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold font-mono text-gray-900">FAISS</div>
              <div className="text-xs text-gray-600">Vector Engine</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

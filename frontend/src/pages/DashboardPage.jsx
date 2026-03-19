import React, { useEffect, useState } from 'react'
import { BarChart3, Bot, Zap, Clock, TrendingUp, Activity } from 'lucide-react'
import { analyticsAPI } from '../utils/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { DEPT_COLORS } from '../utils/constants'
import clsx from 'clsx'

const StatCard = ({ icon: Icon, label, value, sub, color = '#4f63f3' }) => (
  <div className="card flex items-start gap-4">
    <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
      style={{ background: `${color}18`, border: `1px solid ${color}25` }}>
      <Icon size={18} style={{ color }} />
    </div>
    <div>
      <div className="text-2xl font-bold text-white font-mono">{value}</div>
      <div className="text-sm text-slate-400 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-slate-600 mt-0.5">{sub}</div>}
    </div>
  </div>
)

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs">
      <div className="text-slate-300 font-medium">{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.fill }}>{p.name}: {p.value}</div>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsAPI.summary().then(setData).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
    </div>
  )

  const deptData = (data?.top_departments || []).map(d => ({
    name: d.department, count: d.count, fill: DEPT_COLORS[d.department] || '#4f63f3'
  }))

  const agentStats = data?.agent_stats || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <BarChart3 size={20} className="text-brand-400" /> Dashboard
        </h1>
        <p className="text-sm text-slate-500 mt-1">Platform overview and key metrics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Bot} label="Active Agents" value={data?.total_agents ?? 0} color="#4f63f3" />
        <StatCard icon={Zap} label="Total Executions" value={data?.total_executions ?? 0} color="#00e5ff" />
        <StatCard icon={TrendingUp} label="Success Rate" value={`${data?.success_rate ?? 0}%`} color="#00ff9d" />
        <StatCard icon={Clock} label="Hours Saved" value={`${data?.time_saved_hours ?? 0}h`}
          sub="est. 30 min/execution" color="#ffb800" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dept Chart */}
        <div className="card">
          <div className="section-title">Agents by Department</div>
          {deptData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={deptData} barSize={24}>
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="count" radius={[4,4,0,0]}>
                  {deptData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-slate-600 text-sm">
              No data yet — create some agents first
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="section-title">Recent Activity</div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {(data?.recent_activity || []).length === 0 ? (
              <div className="text-sm text-slate-600 py-4 text-center">No activity yet</div>
            ) : (
              data.recent_activity.map((event, i) => (
                <div key={i} className="flex items-center gap-3 text-xs py-1.5 border-b border-white/5 last:border-0">
                  <Activity size={11} className="text-brand-400 flex-shrink-0" />
                  <span className={clsx('badge text-[10px]',
                    event.event_type === 'agent_created' ? 'bg-accent-green/10 text-accent-green' : 'bg-brand-500/10 text-brand-400'
                  )}>
                    {event.event_type?.replace('_', ' ')}
                  </span>
                  <span className="text-slate-500 flex-1 truncate">{event.department || '—'}</span>
                  <span className="text-slate-600 font-mono">
                    {event.created_at ? new Date(event.created_at).toLocaleDateString() : ''}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Agent Performance Table */}
      {agentStats.length > 0 && (
        <div className="card">
          <div className="section-title">Top Agents by Usage</div>
          <div className="space-y-2">
            {agentStats.map((agent, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
                <span className="text-xs text-slate-600 font-mono w-4">{i+1}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-slate-300 truncate">{agent.name}</div>
                  <div className="text-[10px] text-slate-600">{agent.department}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-white">{agent.executions} runs</div>
                  <div className="text-[10px] text-accent-green">
                    {((agent.success_rate || 0) * 100).toFixed(0)}% success
                  </div>
                </div>
                <div className="w-16 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                  <div className="h-full bg-brand-500 rounded-full"
                    style={{ width: `${(agent.success_rate || 0) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

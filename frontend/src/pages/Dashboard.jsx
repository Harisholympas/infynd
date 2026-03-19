import React, { useEffect } from 'react'
import { GitBranch, CheckCircle, XCircle, TrendingUp, Plus, Play } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import useStore from '../store/useStore'
import { workflowAPI, analyticsAPI } from '../utils/api'
import { STATUS_STYLES, APP_COLORS } from '../utils/constants'
import clsx from 'clsx'

const Stat = ({ icon: Icon, label, value, color }) => (
  <div className="bg-white border border-gray-200 rounded-xl p-5 flex items-start gap-4 shadow-sm">
    <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
      style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
      <Icon size={18} style={{ color }} />
    </div>
    <div>
      <div className="text-2xl font-bold text-gray-900 font-mono">{value}</div>
      <div className="text-xs text-gray-600 mt-0.5">{label}</div>
    </div>
  </div>
)

export default function Dashboard() {
  const { analytics, setAnalytics, setActiveView, setEditingWorkflow, workflows, notify } = useStore()

  const handleCreateNew = () => { setEditingWorkflow(null); setActiveView('editor') }

  const handleToggle = async (wf, e) => {
    e.stopPropagation()
    try {
      const res = await workflowAPI.toggle(wf.id)
      useStore.getState().updateWorkflow(wf.id, { status: res.status })
      notify(`Workflow "${wf.name}" turned ${res.status}`, 'success')
      analyticsAPI.summary().then(setAnalytics).catch(() => {})
    } catch (err) { notify(err.message, 'error') }
  }

  const dailyData = analytics?.daily_runs || []
  const appData = (analytics?.app_usage || []).map(a => ({ ...a, fill: APP_COLORS[a.app] || '#4f63f3' }))

  return (
    <div className="space-y-6 animate-fade-in max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-600 mt-0.5">Your automation control centre</p>
        </div>
        <button onClick={handleCreateNew} className="btn-primary">
          <Plus size={14} /> New Workflow
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={GitBranch} label="Total Workflows" value={analytics?.total_workflows ?? 0} color="#6366f1" />
        <Stat icon={Play} label="Active" value={analytics?.active_workflows ?? 0} color="#10b981" />
        <Stat icon={CheckCircle} label="Successful Runs" value={analytics?.success_runs ?? 0} color="#06b6d4" />
        <Stat icon={TrendingUp} label="Success Rate" value={`${analytics?.success_rate ?? 0}%`} color="#f59e0b" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Daily runs chart */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-widest mb-4">Runs — Last 7 Days</div>
          {dailyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={dailyData} barSize={20}>
                <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 11, color: '#374151' }} cursor={{ fill: 'rgba(99, 102, 241, 0.05)' }} />
                <Bar dataKey="success" fill="#10b981" radius={[3,3,0,0]} name="Success" />
                <Bar dataKey="runs" fill="#6366f1" radius={[3,3,0,0]} name="Total" opacity={0.5} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-gray-500 text-sm">Run some workflows to see data</div>
          )}
        </div>

        {/* App usage */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-widest mb-4">Most Used Apps</div>
          <div className="space-y-2">
            {appData.length > 0 ? appData.map((a, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="text-xs text-gray-700 flex-1 font-mono">{a.app}</div>
                <div className="text-xs text-gray-600 w-6 text-right">{a.count}</div>
                <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${(a.count / (appData[0]?.count || 1)) * 100}%`, background: a.fill }} />
                </div>
              </div>
            )) : <div className="text-gray-500 text-sm">No data yet</div>}
          </div>
        </div>
      </div>

      {/* Recent workflows */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-widest">Recent Workflows</div>
          <button onClick={() => setActiveView('workflows')} className="text-xs text-indigo-600 hover:text-indigo-700">View all →</button>
        </div>
        {workflows.length === 0 ? (
          <div className="text-center py-8">
            <GitBranch size={28} className="text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">No workflows yet</p>
            <button onClick={handleCreateNew} className="mt-3 btn-primary mx-auto">
              <Plus size={13} /> Create your first workflow
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {workflows.slice(0,8).map(wf => {
              const st = STATUS_STYLES[wf.status] || STATUS_STYLES.off
              return (
                <div key={wf.id} className="flex items-center gap-3 py-2 hover:bg-gray-50 px-2 rounded-lg cursor-pointer transition-colors group"
                  onClick={() => { setEditingWorkflow(wf); setActiveView('editor') }}>
                  <span className={clsx('status-dot', st.dot)} />
                  <span className="text-sm text-gray-900 flex-1 truncate">{wf.name}</span>
                  <span className="text-xs text-gray-600 font-mono">{wf.run_count} runs</span>
                  <button onClick={(e) => handleToggle(wf, e)}
                    className={clsx('text-[10px] px-2 py-0.5 rounded-full border transition-all opacity-0 group-hover:opacity-100', st.bg, st.text, st.border)}>
                    {wf.status === 'on' ? 'Turn Off' : 'Turn On'}
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

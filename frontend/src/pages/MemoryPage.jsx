import React, { useEffect, useState } from 'react'
import { Brain, User, Building2, Bot } from 'lucide-react'
import { memoryAPI } from '../utils/api'
import { DEPARTMENTS } from '../utils/constants'

export default function MemoryPage() {
  const [userMem, setUserMem] = useState(null)
  const [deptMem, setDeptMem] = useState(null)
  const [selectedDept, setSelectedDept] = useState('HR')

  useEffect(() => {
    memoryAPI.getUser('default').then(setUserMem).catch(console.error)
  }, [])

  useEffect(() => {
    memoryAPI.getDepartment(selectedDept).then(setDeptMem).catch(console.error)
  }, [selectedDept])

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Brain size={20} className="text-indigo-600" /> Memory System
        </h1>
        <p className="text-sm text-gray-600 mt-1">3-layer memory: User · Department · Agent</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Layer Labels */}
        {[
          { icon: User, label: 'User Memory', color: '#6366f1', desc: 'Role, preferences, action history' },
          { icon: Building2, label: 'Department Memory', color: '#0891b2', desc: 'Workflows, best practices, SOPs' },
          { icon: Bot, label: 'Agent Memory', color: '#059669', desc: 'Execution history, improvements' },
        ].map(({ icon: Icon, label, color, desc }) => (
          <div key={label} className="card flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: `${color}10`, border: `1px solid ${color}20` }}>
              <Icon size={16} style={{ color }} />
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-900">{label}</div>
              <div className="text-xs text-gray-600 mt-0.5">{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* User Memory */}
      {userMem && (
        <div className="card">
          <div className="section-title flex items-center gap-2">
            <User size={12} /> User Memory (default)
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Department</div>
              <div className="text-sm text-gray-900">{userMem.department || '—'}</div>
            </div>
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Role</div>
              <div className="text-sm text-gray-900">{userMem.role || '—'}</div>
            </div>
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Actions</div>
              <div className="text-sm text-gray-900">{userMem.past_actions?.length || 0} recorded</div>
            </div>
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Last Updated</div>
              <div className="text-sm text-gray-900">
                {userMem.updated_at ? new Date(userMem.updated_at).toLocaleDateString() : '—'}
              </div>
            </div>
          </div>
          {userMem.past_actions?.length > 0 && (
            <div className="mt-4">
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">Recent Actions</div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {userMem.past_actions.slice(-5).reverse().map((a, i) => (
                  <div key={i} className="text-xs text-gray-700 flex items-center gap-2">
                    <span className="text-gray-600 font-mono">
                      {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : ''}
                    </span>
                    <span>{a.action}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Department Memory */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="section-title mb-0 flex items-center gap-2">
            <Building2 size={12} /> Department Memory
          </div>
          <select className="select w-40 text-xs" value={selectedDept} onChange={e => setSelectedDept(e.target.value)}>
            {DEPARTMENTS.map(d => <option key={d}>{d}</option>)}
          </select>
        </div>
        {deptMem ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">Workflows</div>
              <ul className="space-y-1">
                {(deptMem.workflows || []).map((w, i) => (
                  <li key={i} className="text-xs text-gray-700 flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-indigo-600 flex-shrink-0" />
                    {w}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">Best Practices</div>
              <ul className="space-y-1">
                {(deptMem.best_practices || []).map((p, i) => (
                  <li key={i} className="text-xs text-gray-700 flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-emerald-600 flex-shrink-0" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">Common Tools</div>
              <div className="flex flex-wrap gap-1.5">
                {(deptMem.common_tools || []).map((t) => (
                  <span key={t} className="badge bg-gray-100 text-gray-700 font-mono text-[10px]">{t}</span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-gray-600 text-sm">Loading...</div>
        )}
      </div>
    </div>
  )
}

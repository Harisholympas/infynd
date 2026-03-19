import React, { useState, useEffect } from 'react'
import { Bot, Mic, MicOff, Wand2, Loader2, ChevronDown, Sparkles } from 'lucide-react'
import { agentAPI, intentAPI } from '../utils/api'
import { useVoiceRecorder } from '../hooks/useVoiceRecorder'
import useStore from '../store/useStore'
import { DEPARTMENTS, ROLES_BY_DEPT } from '../utils/constants'
import AgentCard from '../components/AgentCard'
import clsx from 'clsx'

const EXAMPLE_TASKS = [
  "Send weekly performance reports to all managers every Monday at 9 AM",
  "Process incoming invoices, extract data via OCR, and route for approval",
  "Onboard new employees: create accounts, send welcome emails, schedule orientation",
  "Monitor social media mentions and send daily sentiment summary",
  "Reconcile bank statements monthly and flag discrepancies over $100",
]

export default function BuilderPage() {
  const {
    department, role, taskDescription,
    setDepartment, setRole, setTaskDescription,
    isGenerating, setIsGenerating,
    agents, setAgents, addAgent, removeAgent,
    addNotification
  } = useStore()

  const [intent, setIntent] = useState(null)
  const [lastBlueprint, setLastBlueprint] = useState(null)
  const [roles, setRoles] = useState([])
  const [exampleIdx, setExampleIdx] = useState(0)

  const { isRecording, isProcessing, toggleRecording } = useVoiceRecorder({
    onTranscript: (text) => setTaskDescription(taskDescription ? `${taskDescription} ${text}` : text),
    onError: (msg) => addNotification({ type: 'error', message: `Voice: ${msg}` }),
  })

  useEffect(() => {
    if (department) setRoles(ROLES_BY_DEPT[department] || [])
  }, [department])

  useEffect(() => {
    const timer = setInterval(() => setExampleIdx(i => (i + 1) % EXAMPLE_TASKS.length), 4000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    agentAPI.list().then(data => setAgents(data.agents || [])).catch(() => {})
  }, [])

  const handleGenerate = async () => {
    if (!department || !role || !taskDescription.trim()) {
      addNotification({ type: 'error', message: 'Please fill in department, role, and task description' })
      return
    }
    setIsGenerating(true)
    setIntent(null)
    setLastBlueprint(null)
    try {
      const result = await agentAPI.generate({ department, role, task_description: taskDescription })
      setLastBlueprint(result.blueprint)
      setIntent(result.intent)
      addAgent({ id: result.agent_id, name: result.blueprint.agent_name, department, role,
        description: result.blueprint.description, blueprint: result.blueprint,
        status: 'active', execution_count: 0, success_rate: 0,
        created_at: new Date().toISOString() })
      addNotification({ type: 'success', message: `Agent "${result.blueprint.agent_name}" created!` })
    } catch (err) {
      addNotification({ type: 'error', message: `Failed: ${err.message}` })
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* LEFT: Builder Form */}
      <div className="space-y-5">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Bot size={20} className="text-indigo-600" /> Agent Builder
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Describe your repetitive task — we'll build an AI agent to automate it
          </p>
        </div>

        <div className="card space-y-4">
          {/* Department */}
          <div>
            <label className="section-title block">Department</label>
            <div className="relative">
              <select className="select pr-8" value={department} onChange={e => setDepartment(e.target.value)}>
                <option value="">Select department...</option>
                {DEPARTMENTS.map(d => <option key={d}>{d}</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none" />
            </div>
          </div>

          {/* Role */}
          <div>
            <label className="section-title block">Role</label>
            <div className="relative">
              <select className="select pr-8" value={role} onChange={e => setRole(e.target.value)} disabled={!department}>
                <option value="">Select role...</option>
                {roles.map(r => <option key={r}>{r}</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none" />
            </div>
          </div>

          {/* Task Description */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="section-title block mb-0">Task Description</label>
              <button
                onClick={toggleRecording}
                disabled={isProcessing}
                className={clsx(
                  'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
                  isRecording
                    ? 'bg-red-100 text-red-600 border border-red-200 animate-pulse'
                    : 'bg-gray-100 text-gray-600 hover:text-gray-900'
                )}
              >
                {isProcessing ? (
                  <Loader2 size={11} className="animate-spin" />
                ) : isRecording ? (
                  <MicOff size={11} />
                ) : (
                  <Mic size={11} />
                )}
                {isProcessing ? 'Processing...' : isRecording ? 'Stop' : 'Voice'}
              </button>
            </div>
            <textarea
              className="input h-32 resize-none"
              placeholder={`e.g. "${EXAMPLE_TASKS[exampleIdx]}"`}
              value={taskDescription}
              onChange={e => setTaskDescription(e.target.value)}
            />
            <div className="flex flex-wrap gap-1.5 mt-2">
              {EXAMPLE_TASKS.slice(0, 3).map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setTaskDescription(ex)}
                  className="text-[10px] px-2 py-1 rounded bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors truncate max-w-[180px]"
                >
                  {ex.slice(0, 40)}…
                </button>
              ))}
            </div>
          </div>

          {/* Generate Button */}
          <button
            className="btn-primary w-full justify-center py-3"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <><Loader2 size={15} className="animate-spin" /> Generating Agent...</>
            ) : (
              <><Wand2 size={15} /> Generate AI Agent</>
            )}
          </button>
        </div>

        {/* Intent Preview */}
        {intent && (
          <div className="card border-indigo-200 animate-slide-up">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={14} className="text-indigo-600" />
              <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">Intent Analysis</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                ['Task', intent.task],
                ['Frequency', intent.frequency],
                ['Complexity', intent.complexity],
                ['Automation', intent.automation_potential],
              ].map(([k, v]) => (
                <div key={k}>
                  <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-0.5">{k}</div>
                  <div className="text-xs text-gray-900 capitalize">{v || '—'}</div>
                </div>
              ))}
            </div>
            {intent.required_tools?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1">
                {intent.required_tools.map(t => (
                  <span key={t} className="badge bg-indigo-100 text-indigo-700 font-mono text-[10px]">{t}</span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* RIGHT: Generated Agents */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">
            Created Agents <span className="text-gray-600 font-normal ml-1">({agents.length})</span>
          </h2>
        </div>
        <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-200px)]">
          {agents.length === 0 ? (
            <div className="card text-center py-12">
              <Bot size={32} className="text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 text-sm">No agents yet</p>
              <p className="text-gray-500 text-xs mt-1">Build your first agent above</p>
            </div>
          ) : (
            agents.map(agent => (
              <AgentCard key={agent.id} agent={agent} onDeleted={removeAgent} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

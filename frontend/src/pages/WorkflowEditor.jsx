import React, { useState, useEffect } from 'react'
import { Plus, Trash2, Play, Save, ChevronLeft, Zap, AlertCircle, CheckCircle, Loader2, Copy, ArrowRight, Sparkles } from 'lucide-react'
import { workflowAPI, connectionAPI, webhookAPI } from '../utils/api'
import useStore from '../store/useStore'
import { APP_COLORS } from '../utils/constants'
import clsx from 'clsx'
import WorkflowAIAssistant from '../components/WorkflowAIAssistant'
import AddConnectionModal from '../components/AddConnectionModal'

const EMPTY_STEP = { app_key: '', action: '', connection_id: '', input_map: {}, output_key: '', halt_on_error: true, conditions: [] }
const TRIGGER_TYPES = [
  { value: 'schedule', label: 'Schedule', desc: 'Run on a timer' },
  { value: 'webhook', label: 'Webhook', desc: 'Trigger via HTTP' },
  { value: 'manual', label: 'Manual', desc: 'Run manually only' },
  { value: 'rss', label: 'RSS Feed', desc: 'When a feed updates' },
]

function FieldLabel({ children }) {
  return <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">{children}</label>
}

function AppPicker({ apps, selected, onSelect }) {
  const [q, setQ] = useState('')
  const filtered = apps.filter(a => !q || a.name.toLowerCase().includes(q.toLowerCase()) || a.key.includes(q))

  return (
    <div className="space-y-3">
      <input className="input text-sm" placeholder="Search apps..." value={q} onChange={e => setQ(e.target.value)} />
      <div className="grid max-h-56 grid-cols-3 gap-2 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/70 p-2">
        {filtered.map(app => (
          <button
            key={app.key}
            onClick={() => onSelect(app.key)}
            className={clsx(
              'flex flex-col items-center gap-1.5 rounded-xl border p-3 text-center transition-all',
              selected === app.key ? 'border-indigo-200 bg-indigo-50 shadow-sm' : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
            )}
          >
            <span className="text-lg">{app.icon}</span>
            <span className="text-[11px] leading-tight text-gray-600">{app.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function InputField({ field, value, onChange }) {
  const handleChange = (v) => onChange(field.key, v)

  if (field.type === 'textarea') {
    return (
      <div>
        <FieldLabel>{field.label}{field.required && <span className="ml-0.5 text-red-500">*</span>}</FieldLabel>
        <textarea
          className="input codeish h-24 resize-none text-xs"
          placeholder={field.help || '{{step1.output}} or static value'}
          value={value || ''}
          onChange={e => handleChange(e.target.value)}
        />
        {field.help && <p className="mt-1 text-[10px] text-gray-500">{field.help}</p>}
      </div>
    )
  }

  if (field.type === 'select') {
    return (
      <div>
        <FieldLabel>{field.label}</FieldLabel>
        <select className="input text-sm" value={value ?? field.default ?? ''} onChange={e => handleChange(e.target.value)}>
          {(field.options || []).map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      </div>
    )
  }

  if (field.type === 'boolean') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5">
        <input
          type="checkbox"
          checked={!!value}
          onChange={e => handleChange(e.target.checked)}
          className="h-3.5 w-3.5 rounded accent-indigo-600"
          id={field.key}
        />
        <label htmlFor={field.key} className="text-sm text-gray-700">{field.label}</label>
      </div>
    )
  }

  if (field.type === 'number') {
    return (
      <div>
        <FieldLabel>{field.label}</FieldLabel>
        <input type="number" className="input text-sm" value={value ?? field.default ?? 0} onChange={e => handleChange(Number(e.target.value))} />
      </div>
    )
  }

  return (
    <div>
      <FieldLabel>{field.label}{field.required && <span className="ml-0.5 text-red-500">*</span>}</FieldLabel>
      <input
        className="input codeish text-xs"
        type={field.type === 'password' ? 'password' : 'text'}
        placeholder={field.help || field.default || '{{trigger.field}} or value'}
        value={value || ''}
        onChange={e => handleChange(e.target.value)}
      />
      {field.help && <p className="mt-1 text-[10px] text-gray-500">{field.help}</p>}
    </div>
  )
}

function WorkflowFlowMap({ trigger, steps, apps, selectedStep, onSelectStep, onAddStep }) {
  const nodes = [
    {
      id: 'trigger',
      label: TRIGGER_TYPES.find(item => item.value === trigger.type)?.label || 'Trigger',
      subtitle: trigger.type === 'webhook'
        ? 'Incoming event'
        : trigger.type === 'schedule'
          ? 'Timed start'
          : trigger.type === 'rss'
            ? 'Feed watcher'
            : 'Run on demand',
      color: '#4f46e5',
      icon: <Zap size={15} className="text-indigo-600" />,
      active: selectedStep === -1,
    },
    ...steps.map((step, idx) => {
      const appMeta = apps.find(app => app.key === step.app_key) || {}
      return {
        id: `step-${idx}`,
        label: step.app_key ? (appMeta.name || step.app_key) : `Step ${idx + 1}`,
        subtitle: step.action || 'Choose action',
        color: APP_COLORS[step.app_key] || '#0f172a',
        icon: <span className="text-base">{appMeta.icon || '*'}</span>,
        active: selectedStep === idx,
      }
    }),
  ]

  const width = Math.max(860, nodes.length * 210)
  const spacing = nodes.length > 1 ? (width - 168) / (nodes.length - 1) : 0

  return (
    <div className="panel overflow-hidden rounded-3xl border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.12),_transparent_28%),linear-gradient(180deg,_#ffffff_0%,_#f8fbff_100%)]">
      <div className="flex items-center justify-between gap-4 border-b border-slate-200/80 px-5 py-4">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Sparkles size={15} className="text-sky-500" />
            Workflow Map
          </div>
          <div className="mt-1 text-sm text-slate-600">The trigger and tools now read as one connected flow. Click any node to jump into it.</div>
        </div>
        <button onClick={onAddStep} className="btn-secondary py-2 text-sm">
          <Plus size={13} />
          Add Node
        </button>
      </div>

      <div className="overflow-x-auto px-5 py-6">
        <div className="relative min-w-[860px]" style={{ width }}>
          <svg className="pointer-events-none absolute left-0 top-0 h-[168px] w-full" viewBox={`0 0 ${width} 168`} preserveAspectRatio="none">
            {nodes.slice(0, -1).map((node, idx) => {
              const next = nodes[idx + 1]
              const startX = 84 + spacing * idx + 140
              const endX = 84 + spacing * (idx + 1)
              const y = 74
              const active = node.active || next.active

              return (
                <g key={`${node.id}-${next.id}`}>
                  <path
                    d={`M ${startX} ${y} C ${startX + 42} ${y}, ${endX - 42} ${y}, ${endX} ${y}`}
                    fill="none"
                    stroke={active ? '#4f46e5' : '#cbd5e1'}
                    strokeDasharray={active ? '0' : '8 8'}
                    strokeWidth={active ? '3' : '2'}
                    strokeLinecap="round"
                  />
                  <circle cx={endX} cy={y} r={active ? '5' : '4'} fill={active ? '#4f46e5' : '#94a3b8'} />
                </g>
              )
            })}
          </svg>

          <div className="relative flex gap-16">
            {nodes.map((node, idx) => (
              <button
                key={node.id}
                type="button"
                onClick={() => onSelectStep(idx - 1)}
                className={clsx(
                  'relative w-36 flex-shrink-0 rounded-[28px] border p-4 text-left shadow-[0_18px_45px_-28px_rgba(15,23,42,0.45)] transition-all',
                  node.active
                    ? 'border-indigo-300 bg-white ring-4 ring-indigo-100'
                    : 'border-slate-200 bg-white/90 hover:-translate-y-1 hover:border-slate-300 hover:shadow-[0_22px_48px_-28px_rgba(79,70,229,0.35)]'
                )}
              >
                <span
                  className="absolute -left-2 top-[4.15rem] h-4 w-4 rounded-full border-4 border-white shadow-sm"
                  style={{ backgroundColor: idx === 0 ? '#4f46e5' : node.color }}
                />
                <span
                  className="absolute -right-2 top-[4.15rem] h-4 w-4 rounded-full border-4 border-white shadow-sm"
                  style={{ backgroundColor: idx === nodes.length - 1 ? '#cbd5e1' : '#0ea5e9' }}
                />
                <span
                  className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl border"
                  style={{ backgroundColor: `${node.color}12`, borderColor: `${node.color}32` }}
                >
                  {node.icon}
                </span>
                <div className="text-sm font-semibold text-slate-900">{node.label}</div>
                <div className="mt-1 text-xs text-slate-500">{node.subtitle}</div>
                {idx < nodes.length - 1 && (
                  <div className="mt-4 flex items-center gap-1 text-[11px] font-medium text-sky-600">
                    <ArrowRight size={11} />
                    passes data
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function StepCard({ step, idx, apps, connections, onUpdate, onDelete, runResult, onRequestConnect, selected, onSelect }) {
  const [expanded, setExpanded] = useState(true)
  const [appDetail, setAppDetail] = useState(null)
  const color = APP_COLORS[step.app_key] || '#4f63f3'
  const appMeta = apps.find(a => a.key === step.app_key) || {}
  const stepResult = runResult?.steps_results?.[idx]

  useEffect(() => {
    if (step.app_key) {
      connectionAPI.getApp(step.app_key).then(setAppDetail).catch(() => {})
    }
  }, [step.app_key])

  useEffect(() => {
    if (selected) setExpanded(true)
  }, [selected])

  const actionFields = appDetail?.actions?.[step.action]?.fields || []
  const availableActions = Object.entries(appDetail?.actions || {})
  const appConns = connections.filter(c => c.app_key === step.app_key)
  const needsAuth = appDetail && appDetail.auth_type !== 'none' && !['formatter', 'filter', 'delay', 'storage', 'paths', 'webhooks', 'schedule', 'rss'].includes(step.app_key)
  const setField = (key, val) => onUpdate({ ...step, input_map: { ...step.input_map, [key]: val } })

  return (
    <div className={clsx(
      'panel relative overflow-hidden rounded-[28px] border transition-all',
      selected ? 'border-indigo-300 shadow-[0_24px_60px_-36px_rgba(79,70,229,0.45)] ring-4 ring-indigo-100' : 'border-slate-200'
    )}>
      <div className="pointer-events-none absolute left-8 top-0 h-6 w-px bg-gradient-to-b from-sky-300 to-transparent" />
      <div className="pointer-events-none absolute left-8 top-full h-6 w-px -translate-y-1 bg-gradient-to-b from-sky-300 to-transparent" />
      <div className="pointer-events-none absolute left-[25px] top-8 h-6 w-6 rounded-full border-4 border-white shadow-sm" style={{ backgroundColor: color }} />

      <div
        className={clsx('flex cursor-pointer items-center gap-3 p-4 transition-colors', selected ? 'bg-indigo-50/70' : 'hover:bg-slate-50/70')}
        onClick={() => {
          onSelect?.()
          setExpanded(prev => !prev)
        }}
      >
        <div
          className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl text-sm shadow-sm"
          style={{ background: `${color}10`, border: `1px solid ${color}20` }}
        >
          {appMeta.icon || '*'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-gray-900">
            {idx + 1}. {step.app_key ? `${appMeta.name || step.app_key} - ${step.action || 'Choose action'}` : 'Choose app'}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            {step.output_key && <div className="font-mono text-[11px] text-gray-500">-&gt; {step.output_key}</div>}
            <div className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500">
              {selected ? 'Focused' : 'Connected'}
            </div>
          </div>
        </div>
        {stepResult && (
          <div className={clsx(
            'rounded-full border px-2 py-0.5 text-[10px] font-medium',
            stepResult.status === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' :
            stepResult.status === 'error' ? 'border-red-200 bg-red-50 text-red-700' :
            'border-amber-200 bg-amber-50 text-amber-700'
          )}>
            {stepResult.status}
          </div>
        )}
        <button
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-gray-500 transition-all hover:bg-red-50 hover:text-red-600"
        >
          <Trash2 size={12} />
        </button>
      </div>

      {expanded && (
        <div className="space-y-4 border-t border-slate-200 p-5">
          {!step.app_key ? (
            <AppPicker apps={apps} selected={step.app_key} onSelect={key => onUpdate({ ...step, app_key: key, action: '', input_map: {} })} />
          ) : (
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5">
              <span className="text-sm text-gray-700">{appMeta.icon} {appMeta.name}</span>
              <button onClick={() => onUpdate({ ...EMPTY_STEP })} className="text-[11px] font-medium text-gray-600 hover:text-gray-900">change app</button>
            </div>
          )}

          {step.app_key && availableActions.length > 0 && (
            <div>
              <FieldLabel>Action *</FieldLabel>
              <select className="input text-sm" value={step.action} onChange={e => onUpdate({ ...step, action: e.target.value, input_map: {} })}>
                <option value="">Choose action...</option>
                {availableActions.map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>
          )}

          {step.app_key && needsAuth && (
            <div>
              <FieldLabel>Account *</FieldLabel>
              {appConns.length > 0 ? (
                <select className="input text-sm" value={step.connection_id} onChange={e => onUpdate({ ...step, connection_id: e.target.value })}>
                  <option value="">Select account...</option>
                  {appConns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center gap-1 text-sm text-amber-700">
                    <AlertCircle size={11} /> No {appMeta.name} account connected yet
                  </div>
                  <button type="button" onClick={() => onRequestConnect?.(step.app_key)} className="btn-secondary w-full justify-center text-sm">
                    Connect {appMeta.name}
                  </button>
                </div>
              )}
            </div>
          )}

          {step.action && actionFields.map(field => (
            <InputField key={field.key} field={field} value={step.input_map?.[field.key]} onChange={setField} />
          ))}

          {step.action && (
            <div>
              <FieldLabel>Output key (reference in later steps)</FieldLabel>
              <input className="input codeish text-xs" placeholder="e.g. step2" value={step.output_key} onChange={e => onUpdate({ ...step, output_key: e.target.value })} />
            </div>
          )}

          {stepResult?.output && (
            <div className="mt-1 rounded-xl bg-slate-50 p-3">
              <div className="mb-1 text-[10px] text-gray-600">Output</div>
              <pre className="max-h-24 overflow-auto font-mono text-[10px] text-gray-700">
                {JSON.stringify(stepResult.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function WorkflowEditor() {
  const { editingWorkflow, setActiveView, setEditingWorkflow, apps, connections, setConnections, notify, updateWorkflow, addWorkflow } = useStore()
  const [name, setName] = useState(editingWorkflow?.name || 'My Workflow')
  const [trigger, setTrigger] = useState(editingWorkflow?.trigger_config || { type: 'manual', config: {} })
  const [steps, setSteps] = useState(editingWorkflow?.steps || [])
  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [lastRun, setLastRun] = useState(null)
  const [webhookInfo, setWebhookInfo] = useState(null)
  const [connectAppKey, setConnectAppKey] = useState(null)
  const [connectAppDetail, setConnectAppDetail] = useState(null)
  const [selectedStep, setSelectedStep] = useState(editingWorkflow?.steps?.length ? 0 : -1)

  const isNew = !editingWorkflow?.id

  useEffect(() => {
    let cancelled = false
    if (!connectAppKey) { setConnectAppDetail(null); return }
    connectionAPI.getApp(connectAppKey)
      .then(d => { if (!cancelled) setConnectAppDetail(d) })
      .catch(() => { if (!cancelled) setConnectAppDetail(null) })
    return () => { cancelled = true }
  }, [connectAppKey])

  useEffect(() => {
    if (steps.length === 0) {
      setSelectedStep(-1)
      return
    }
    if (selectedStep >= steps.length) {
      setSelectedStep(steps.length - 1)
    }
  }, [steps, selectedStep])

  const ensureRunnable = () => {
    for (let i = 0; i < steps.length; i++) {
      const s = steps[i]
      if (!s?.app_key || !s?.action) {
        notify(`Step ${i + 1} is incomplete (choose app + action)`, 'error')
        setSelectedStep(i)
        return false
      }
      const appMeta = apps.find(a => a.key === s.app_key) || {}
      const needsAuth =
        appMeta.auth_type &&
        appMeta.auth_type !== 'none' &&
        !['formatter', 'filter', 'delay', 'storage', 'paths', 'webhooks', 'schedule', 'rss'].includes(s.app_key)
      if (needsAuth && !s.connection_id) {
        notify(`Step ${i + 1} needs a connected account (${appMeta.name || s.app_key})`, 'error')
        setConnectAppKey(s.app_key)
        setSelectedStep(i)
        return false
      }
    }
    return true
  }

  const handleSave = async () => {
    if (!name.trim()) { notify('Please give your workflow a name', 'error'); return }
    if (!ensureRunnable()) return
    setSaving(true)
    try {
      const payload = {
        name,
        description: '',
        trigger: { type: trigger.type, app_key: trigger.app_key || null, connection_id: trigger.connection_id || null, config: trigger.config || {} },
        steps: steps.map(s => ({ ...s, conditions: s.conditions || [], input_map: s.input_map || {} })),
        folder: '',
        tags: [],
      }
      if (isNew) {
        const res = await workflowAPI.create(payload)
        addWorkflow({ ...res, steps, trigger_config: trigger, run_count: 0, error_count: 0, updated_at: new Date().toISOString() })
        setEditingWorkflow({ ...res, steps, trigger_config: trigger })
        notify(`Workflow "${name}" created`, 'success')
      } else {
        const res = await workflowAPI.update(editingWorkflow.id, payload)
        updateWorkflow(editingWorkflow.id, res)
        notify('Saved', 'success')
      }
    } catch (err) {
      notify(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleRun = async () => {
    if (!editingWorkflow?.id) { notify('Save the workflow first', 'error'); return }
    if (!ensureRunnable()) return
    setRunning(true)
    setLastRun(null)
    try {
      const res = await workflowAPI.run(editingWorkflow.id, { trigger: 'manual', ts: Date.now() })
      setLastRun(res)
      notify(res.status === 'success' ? 'Run completed' : `Run ${res.status}`, res.status === 'success' ? 'success' : 'error')
    } catch (err) {
      notify(err.message, 'error')
    } finally {
      setRunning(false)
    }
  }

  const handleCreateWebhook = async () => {
    if (!editingWorkflow?.id) { notify('Save first', 'error'); return }
    try {
      const res = await webhookAPI.create(editingWorkflow.id)
      setWebhookInfo(res)
      setTrigger({ type: 'webhook', config: { url: res.url, endpoint: res.endpoint_path } })
      notify('Webhook URL created', 'success')
    } catch (err) {
      notify(err.message, 'error')
    }
  }

  const addStep = () => setSteps(s => [...s, { ...EMPTY_STEP }])
  const updateStep = (idx, data) => setSteps(s => s.map((step, i) => i === idx ? data : step))
  const deleteStep = (idx) => {
    setSteps(s => s.filter((_, i) => i !== idx))
    setSelectedStep(prev => {
      if (prev === idx) return idx > 0 ? idx - 1 : -1
      if (prev > idx) return prev - 1
      return prev
    })
  }
  const applyAIDraft = (draft) => {
    setName(draft.name || 'AI Workflow')
    setTrigger(draft.trigger_config || { type: 'manual', config: {} })
    setSteps(draft.steps || [])
    setEditingWorkflow(draft)
    setSelectedStep(draft.steps?.length ? 0 : -1)
  }

  return (
    <div className="mx-auto max-w-6xl animate-fade-in space-y-6">
      <WorkflowAIAssistant
        embedded
        title="Build This Workflow With AI"
        subtitle="Give a prompt or voice command and AI will prefill the trigger and workflow steps here for you."
        onApplyDraft={applyAIDraft}
      />

      <div className="panel rounded-3xl p-5">
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={() => setActiveView('workflows')} className="btn-ghost py-1">
            <ChevronLeft size={14} /> Back
          </button>
          <div className="min-w-0 flex-1">
            <input
              className="w-full border-b border-transparent bg-transparent px-1 py-1 text-2xl font-semibold tracking-tight text-gray-900 transition-all hover:border-gray-300 focus:border-indigo-500/50 focus:outline-none"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Workflow name..."
            />
            <p className="mt-1 text-sm text-gray-600">Refine the trigger, steps, and connected tools before saving.</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={handleRun} disabled={running || !editingWorkflow?.id} className="btn-secondary py-2">
              {running ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
              Test Run
            </button>
            <button onClick={handleSave} disabled={saving} className="btn-primary py-2">
              {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
              {isNew ? 'Create' : 'Save'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <WorkflowFlowMap
            trigger={trigger}
            steps={steps}
            apps={apps}
            selectedStep={selectedStep}
            onSelectStep={setSelectedStep}
            onAddStep={() => {
              addStep()
              setSelectedStep(steps.length)
            }}
          />

          <div className="panel overflow-hidden rounded-3xl">
            <div className="flex items-center gap-3 border-b border-indigo-100 bg-gradient-to-r from-indigo-50 to-sky-50 p-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white shadow-sm">
                <Zap size={15} className="text-indigo-600" />
              </div>
              <div>
                <div className="text-sm font-semibold text-indigo-950">Trigger</div>
                <div className="text-sm text-slate-600">Choose how this workflow starts.</div>
              </div>
            </div>

            <div className="space-y-4 p-5">
              <div>
                <FieldLabel>Trigger Type</FieldLabel>
                <div className="grid grid-cols-2 gap-2">
                  {TRIGGER_TYPES.map(t => (
                    <button
                      key={t.value}
                      onClick={() => {
                        setTrigger({ type: t.value, config: {} })
                        setSelectedStep(-1)
                      }}
                      className={clsx(
                        'rounded-2xl border px-3 py-3 text-left transition-all',
                        trigger.type === t.value ? 'border-indigo-200 bg-indigo-50 text-gray-900 shadow-sm' : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                      )}
                    >
                      <div className="text-sm font-semibold">{t.label}</div>
                      <div className="mt-1 text-xs text-gray-500">{t.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {trigger.type === 'schedule' && (
                <div className="space-y-3">
                  <div>
                    <FieldLabel>Schedule Type</FieldLabel>
                    <select
                      className="input text-sm"
                      value={trigger.config?.trigger_action || ''}
                      onChange={e => setTrigger(t => ({ ...t, config: { ...t.config, trigger_action: e.target.value } }))}
                    >
                      <option value="">Choose...</option>
                      <option value="every_x_minutes">Every X Minutes</option>
                      <option value="every_hour">Every Hour</option>
                      <option value="every_day">Every Day</option>
                      <option value="every_week">Every Week</option>
                      <option value="every_month">Every Month</option>
                      <option value="custom_cron">Custom Cron</option>
                    </select>
                  </div>

                  {trigger.config?.trigger_action === 'every_day' && (
                    <div>
                      <FieldLabel>Time (HH:MM)</FieldLabel>
                      <input className="input text-sm" placeholder="09:00" value={trigger.config?.time || ''} onChange={e => setTrigger(t => ({ ...t, config: { ...t.config, time: e.target.value } }))} />
                    </div>
                  )}

                  {trigger.config?.trigger_action === 'every_x_minutes' && (
                    <div>
                      <FieldLabel>Every N minutes</FieldLabel>
                      <input type="number" className="input text-sm" placeholder="15" value={trigger.config?.interval || 15} onChange={e => setTrigger(t => ({ ...t, config: { ...t.config, interval: Number(e.target.value) } }))} />
                    </div>
                  )}

                  {trigger.config?.trigger_action === 'custom_cron' && (
                    <div>
                      <FieldLabel>Cron Expression</FieldLabel>
                      <input className="input codeish text-xs" placeholder="0 9 * * 1" value={trigger.config?.cron || ''} onChange={e => setTrigger(t => ({ ...t, config: { ...t.config, cron: e.target.value } }))} />
                      <p className="mt-1 text-[10px] text-gray-500">min hour day month weekday</p>
                    </div>
                  )}

                  {trigger.config?.trigger_action === 'every_week' && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <FieldLabel>Day</FieldLabel>
                        <select className="input text-sm" value={trigger.config?.day || 'monday'} onChange={e => setTrigger(t => ({ ...t, config: { ...t.config, day: e.target.value } }))}>
                          {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map(d => <option key={d}>{d}</option>)}
                        </select>
                      </div>
                      <div>
                        <FieldLabel>Time</FieldLabel>
                        <input className="input text-sm" placeholder="09:00" value={trigger.config?.time || ''} onChange={e => setTrigger(t => ({ ...t, config: { ...t.config, time: e.target.value } }))} />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {trigger.type === 'webhook' && (
                <div>
                  {webhookInfo || trigger.config?.url ? (
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <div className="mb-1 text-[10px] text-gray-600">POST to this URL</div>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 break-all font-mono text-[10px] text-indigo-600">
                          {webhookInfo?.url || trigger.config?.url}
                        </code>
                        <button onClick={() => navigator.clipboard.writeText(webhookInfo?.url || trigger.config?.url)} className="rounded p-1 text-gray-600 hover:bg-gray-200 hover:text-gray-900">
                          <Copy size={11} />
                        </button>
                      </div>
                      {webhookInfo?.secret && (
                        <div className="mt-1 text-[10px] text-gray-600">Secret: <code className="font-mono text-gray-700">{webhookInfo.secret}</code></div>
                      )}
                    </div>
                  ) : (
                    <button onClick={handleCreateWebhook} className="btn-secondary w-full justify-center text-sm">
                      Generate Webhook URL
                    </button>
                  )}
                </div>
              )}

              {trigger.type === 'rss' && (
                <div>
                  <FieldLabel>Feed URL</FieldLabel>
                  <input className="input text-sm" placeholder="https://example.com/feed.xml" value={trigger.config?.feed_url || ''} onChange={e => setTrigger(t => ({ ...t, config: { ...t.config, feed_url: e.target.value } }))} />
                </div>
              )}
            </div>
          </div>

          {steps.map((step, idx) => (
            <StepCard
              key={idx}
              step={step}
              idx={idx}
              apps={apps}
              connections={connections}
              onUpdate={data => updateStep(idx, data)}
              onDelete={() => deleteStep(idx)}
              runResult={lastRun}
              onRequestConnect={(appKey) => setConnectAppKey(appKey)}
              selected={selectedStep === idx}
              onSelect={() => setSelectedStep(idx)}
            />
          ))}

          <button
            onClick={() => {
              addStep()
              setSelectedStep(steps.length)
            }}
            className="flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-gray-300 py-4 text-sm text-gray-600 transition-all hover:border-gray-400 hover:text-gray-900"
          >
            <Plus size={14} /> Add Step
          </button>
        </div>

        <div className="space-y-4">
          <div className="panel rounded-3xl p-5">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">Focused Node</div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              {selectedStep === -1 ? (
                <>
                  <div className="text-sm font-semibold text-slate-900">{TRIGGER_TYPES.find(item => item.value === trigger.type)?.label || 'Trigger'}</div>
                  <div className="mt-1 text-sm text-slate-600">This is the entry point for the whole workflow.</div>
                </>
              ) : (
                <>
                  <div className="text-sm font-semibold text-slate-900">
                    Step {selectedStep + 1}: {steps[selectedStep]?.app_key ? (apps.find(app => app.key === steps[selectedStep]?.app_key)?.name || steps[selectedStep]?.app_key) : 'Choose app'}
                  </div>
                  <div className="mt-1 text-sm text-slate-600">
                    {steps[selectedStep]?.action || 'Pick an action to wire this node into the flow.'}
                  </div>
                </>
              )}
            </div>
          </div>

          {lastRun && (
            <div className="panel rounded-3xl p-5">
              <div className="mb-3 flex items-center gap-2">
                {lastRun.status === 'success' ? <CheckCircle size={14} className="text-emerald-500" /> : <AlertCircle size={14} className="text-red-500" />}
                <span className={clsx('text-sm font-semibold', lastRun.status === 'success' ? 'text-emerald-700' : 'text-red-700')}>
                  {lastRun.status} · {lastRun.duration_ms}ms
                </span>
              </div>
              {lastRun.error_message && (
                <div className="mb-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{lastRun.error_message}</div>
              )}
              <div className="space-y-3">
                {(lastRun.steps_results || []).map((sr, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <div className={clsx(
                      'mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full',
                      sr.status === 'success' ? 'bg-emerald-500' : sr.status === 'error' ? 'bg-red-500' : 'bg-amber-500'
                    )} />
                    <div className="min-w-0 flex-1">
                      <div className="text-[11px] text-gray-600">{sr.app_key} · {sr.action}</div>
                      {sr.output && (
                        <pre className="mt-1 max-h-20 overflow-auto font-mono text-[10px] text-gray-700">
                          {JSON.stringify(sr.output, null, 2).slice(0, 200)}
                        </pre>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="panel rounded-3xl p-5">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">Context Variables</div>
            <div className="space-y-1 font-mono text-[11px] text-gray-700">
              <div>{'{{trigger.*}}'} - trigger data</div>
              {steps.map((s, i) => s.output_key && (
                <div key={i}>{`{{${s.output_key}.*}}`} - step {i + 1}</div>
              ))}
              {steps.map((s, i) => !s.output_key && (
                <div key={i}>{`{{step${i + 1}.*}}`} - step {i + 1}</div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {connectAppKey && connectAppDetail && (
        <AddConnectionModal
          app={connectAppDetail}
          onClose={() => setConnectAppKey(null)}
          onAdded={(newConn) => {
            setConnections([...connections, newConn])
            setSteps(prev => prev.map(s => (s.app_key === newConn.app_key && !s.connection_id ? { ...s, connection_id: newConn.id } : s)))
          }}
        />
      )}
    </div>
  )
}

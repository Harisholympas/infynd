import React from 'react'
import { BarChart3, Activity, Briefcase, Users, ShieldCheck, ArrowUpRight, Layers3, Workflow, Clock3 } from 'lucide-react'
import useStore from '../store/useStore'
import clsx from 'clsx'

const DEPARTMENT_RULES = [
  { key: 'HR', terms: ['hr', 'resume', 'recruit', 'candidate', 'employee', 'payroll', 'hiring', 'interview'] },
  { key: 'Sales', terms: ['sales', 'lead', 'crm', 'pipeline', 'deal', 'prospect', 'account executive'] },
  { key: 'Marketing', terms: ['marketing', 'campaign', 'seo', 'content', 'social', 'newsletter', 'brand'] },
  { key: 'Finance', terms: ['finance', 'invoice', 'budget', 'expense', 'billing', 'payment', 'accounting'] },
  { key: 'Support', terms: ['support', 'ticket', 'customer', 'helpdesk', 'service', 'incident'] },
  { key: 'Operations', terms: ['ops', 'operations', 'approval', 'sync', 'handoff', 'inventory', 'logistics'] },
]

function normalize(value) {
  return String(value || '').toLowerCase()
}

function classifyDepartment(workflow) {
  const text = [
    workflow.name,
    workflow.description,
    ...(Array.isArray(workflow.tags) ? workflow.tags : []),
    ...(Array.isArray(workflow.steps) ? workflow.steps.map(step => step.app_key).filter(Boolean) : []),
  ].join(' ').toLowerCase()

  let best = { key: 'General', score: 0 }

  for (const rule of DEPARTMENT_RULES) {
    const score = rule.terms.reduce((sum, term) => sum + (text.includes(term) ? 1 : 0), 0)
    if (score > best.score) best = { key: rule.key, score }
  }

  return best.key
}

function classifyWorker(workflow, department) {
  const stepKeys = (workflow.steps || []).map(step => normalize(step.app_key))
  const triggerType = normalize(workflow.trigger_config?.type || workflow.trigger_type)

  if (department === 'HR') return 'Recruiting / People Ops'
  if (department === 'Sales') return 'Revenue Ops'
  if (department === 'Marketing') return 'Marketing Ops'
  if (department === 'Finance') return 'Finance Ops'
  if (department === 'Support') return 'Support Ops'
  if (triggerType === 'schedule') return 'Scheduled Operator'
  if (triggerType === 'webhook') return 'Event-driven Worker'
  if (stepKeys.some(key => key.includes('email') || key.includes('slack'))) return 'Communication Worker'
  return 'General Automation Worker'
}

function StatCard({ icon: Icon, label, value, tone = 'slate', hint }) {
  const tones = {
    indigo: 'from-indigo-500/24 via-slate-900 to-slate-950 border-indigo-400/35 text-indigo-300',
    emerald: 'from-emerald-500/24 via-slate-900 to-slate-950 border-emerald-400/35 text-emerald-300',
    amber: 'from-amber-400/24 via-slate-900 to-slate-950 border-amber-300/35 text-amber-200',
    sky: 'from-sky-500/24 via-slate-900 to-slate-950 border-sky-400/35 text-sky-300',
    slate: 'from-slate-700/40 via-slate-900 to-slate-950 border-slate-500/35 text-slate-200',
  }

  return (
    <div className={clsx('rounded-3xl border bg-gradient-to-br p-5 shadow-[0_24px_70px_-36px_rgba(15,23,42,0.95)] backdrop-blur-md', tones[tone])}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</div>
          <div className="mt-2 text-3xl font-semibold text-white">{value}</div>
          {hint && <div className="mt-2 text-sm text-slate-300">{hint}</div>}
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/10 shadow-sm backdrop-blur-md">
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

function AnalyzeScene() {
  return (
    <div className="relative h-[320px] w-full max-w-[430px] overflow-hidden rounded-[36px] border border-cyan-300/25 bg-[radial-gradient(circle_at_25%_20%,_rgba(34,211,238,0.35),_transparent_24%),radial-gradient(circle_at_85%_18%,_rgba(99,102,241,0.42),_transparent_28%),linear-gradient(160deg,_#020617_0%,_#0f172a_40%,_#111827_100%)] shadow-[0_45px_120px_-45px_rgba(14,165,233,0.55)]">
      <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(148,163,184,0.14)_1px,transparent_1px),linear-gradient(rgba(148,163,184,0.14)_1px,transparent_1px)] bg-[size:30px_30px]" />
      <div className="absolute left-1/2 top-[68%] h-52 w-[150%] -translate-x-1/2 rounded-full border border-cyan-300/35 opacity-90 [transform:perspective(1000px)_rotateX(76deg)]" />
      <div className="absolute left-1/2 top-[68%] h-36 w-[105%] -translate-x-1/2 rounded-full border border-indigo-300/50 opacity-90 [transform:perspective(1000px)_rotateX(76deg)] animate-pulse-glow" />
      <div className="absolute left-[18%] top-[18%] h-24 w-24 rounded-full bg-cyan-300/50 blur-3xl" />
      <div className="absolute right-[14%] top-[14%] h-28 w-28 rounded-full bg-indigo-400/45 blur-3xl" />

      <div className="absolute left-10 top-12 h-24 w-24 rounded-[26px] border border-white/20 bg-white/10 shadow-[0_25px_60px_-25px_rgba(79,70,229,0.85)] backdrop-blur-md [transform:perspective(900px)_rotateX(58deg)_rotateY(-22deg)_rotateZ(-18deg)] animate-float-drift-slow" />
      <div className="absolute right-10 top-12 h-28 w-28 rounded-[30px] border border-white/20 bg-white/10 shadow-[0_25px_60px_-25px_rgba(14,165,233,0.85)] backdrop-blur-md [transform:perspective(900px)_rotateX(60deg)_rotateY(22deg)_rotateZ(20deg)] animate-float-drift" />
      <div className="absolute left-[34%] top-[22%] h-32 w-32 rounded-[32px] border border-cyan-200/25 bg-[linear-gradient(180deg,rgba(255,255,255,0.18)_0%,rgba(99,102,241,0.12)_100%)] shadow-[0_40px_100px_-35px_rgba(34,211,238,0.85)] [transform:perspective(1200px)_rotateX(62deg)_rotateY(-10deg)_rotateZ(-8deg)] animate-float-drift" />

      <div className="absolute bottom-8 left-7 right-7 rounded-[28px] border border-white/15 bg-white/10 p-4 shadow-[0_20px_60px_-35px_rgba(0,0,0,0.95)] backdrop-blur-md">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-200">Live Depth</div>
        <div className="mt-2 flex items-end gap-2">
          <div className="h-10 w-10 rounded-2xl bg-cyan-400 shadow-[0_12px_28px_rgba(34,211,238,0.45)]" />
          <div className="h-16 w-10 rounded-2xl bg-indigo-400 shadow-[0_12px_28px_rgba(99,102,241,0.45)]" />
          <div className="h-12 w-10 rounded-2xl bg-emerald-400 shadow-[0_12px_28px_rgba(16,185,129,0.45)]" />
          <div className="h-20 w-10 rounded-2xl bg-amber-300 shadow-[0_12px_28px_rgba(251,191,36,0.45)]" />
        </div>
      </div>

      <div className="absolute right-8 top-8 h-3 w-20 rounded-full bg-cyan-400/70 blur-md animate-pulse-glow" />
      <div className="absolute left-10 bottom-20 h-3 w-24 rounded-full bg-indigo-400/60 blur-md animate-pulse-glow" />
    </div>
  )
}

export default function AnalyzePage() {
  const { workflows, connections, analytics, apps } = useStore()

  const enriched = workflows.map(workflow => {
    const department = classifyDepartment(workflow)
    const worker = classifyWorker(workflow, department)
    const stepCount = Array.isArray(workflow.steps) ? workflow.steps.length : 0
    const runCount = workflow.run_count || 0
    const errorCount = workflow.error_count || 0
    const successWeight = runCount > 0 ? Math.max(0, ((runCount - errorCount) / runCount) * 100) : 55
    const automationDepth = Math.min(100, stepCount * 18)
    const activationWeight = workflow.status === 'on' ? 100 : 45
    const efficiency = Math.round(successWeight * 0.45 + automationDepth * 0.25 + activationWeight * 0.3)

    return { ...workflow, department, worker, stepCount, efficiency }
  })

  const departmentCounts = enriched.reduce((acc, workflow) => {
    acc[workflow.department] = (acc[workflow.department] || 0) + 1
    return acc
  }, {})

  const workerCounts = enriched.reduce((acc, workflow) => {
    acc[workflow.worker] = (acc[workflow.worker] || 0) + 1
    return acc
  }, {})

  const topDepartments = Object.entries(departmentCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  const topWorkers = Object.entries(workerCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)

  const usedApps = new Set(
    enriched.flatMap(workflow => (workflow.steps || []).map(step => step.app_key).filter(Boolean))
  )

  const activeWorkflows = workflows.filter(workflow => workflow.status === 'on').length
  const totalWorkflows = workflows.length
  const totalRuns = analytics?.total_runs || 0
  const successRate = analytics?.success_rate || 0
  const averageEfficiency = enriched.length
    ? Math.round(enriched.reduce((sum, workflow) => sum + workflow.efficiency, 0) / enriched.length)
    : 0
  const automationCoverage = totalWorkflows ? Math.round((activeWorkflows / totalWorkflows) * 100) : 0
  const appCoverage = usedApps.size ? Math.round((connections.length / usedApps.size) * 100) : 0

  const healthLabel =
    averageEfficiency >= 80 ? 'Strong operational usage'
      : averageEfficiency >= 60 ? 'Healthy but improvable'
        : 'Early-stage adoption'

  const insights = [
    `${topDepartments[0]?.name || 'General'} is the main department using the platform right now.`,
    `${topWorkers[0]?.name || 'General Automation Worker'} is the most common worker pattern inferred from workflow behavior.`,
    `${automationCoverage}% of workflows are active, which reflects how much of the platform is running in production.`,
    `${appCoverage || 0}% connection coverage suggests how well connected the active automations are to the apps they use.`,
  ]

  const topWorkflowRows = enriched
    .slice()
    .sort((a, b) => b.efficiency - a.efficiency)
    .slice(0, 6)

  return (
    <div className="relative mx-auto max-w-7xl space-y-6 overflow-hidden rounded-[40px] border border-slate-800 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.12),_transparent_18%),radial-gradient(circle_at_top_right,_rgba(99,102,241,0.18),_transparent_22%),linear-gradient(180deg,_#020617_0%,_#0f172a_48%,_#111827_100%)] p-5 animate-fade-in shadow-[0_38px_120px_-50px_rgba(0,0,0,0.95)]">
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden rounded-[36px]">
        <div className="absolute left-[-8%] top-10 h-56 w-56 rounded-full bg-cyan-400/24 blur-3xl animate-float-drift" />
        <div className="absolute right-[6%] top-6 h-72 w-72 rounded-full bg-indigo-400/22 blur-3xl animate-float-drift-slow" />
        <div className="absolute bottom-16 left-[24%] h-52 w-52 rounded-full bg-emerald-400/18 blur-3xl animate-float-drift" />
        <div className="absolute bottom-10 right-[18%] h-40 w-40 rounded-full bg-amber-300/24 blur-3xl animate-float-drift-slow" />

        <div className="absolute inset-x-[-12%] top-28 h-80 origin-center animate-tilt-plane opacity-70">
          <div className="h-full w-full rounded-[999px] border border-cyan-300/18 bg-[linear-gradient(90deg,rgba(148,163,184,0.18)_1px,transparent_1px),linear-gradient(rgba(148,163,184,0.18)_1px,transparent_1px)] bg-[size:38px_38px] shadow-[0_40px_120px_rgba(56,189,248,0.16)]" />
        </div>

        <div className="absolute left-[11%] top-[18%] h-24 w-24 rounded-[28px] border border-white/50 bg-white/30 shadow-[0_25px_80px_rgba(99,102,241,0.18)] backdrop-blur-md [transform:rotateX(58deg)_rotateY(-20deg)_rotateZ(-18deg)] animate-float-drift-slow" />
        <div className="absolute right-[12%] top-[32%] h-20 w-20 rounded-[24px] border border-white/50 bg-white/30 shadow-[0_25px_80px_rgba(14,165,233,0.18)] backdrop-blur-md [transform:rotateX(58deg)_rotateY(18deg)_rotateZ(24deg)] animate-float-drift" />
        <div className="absolute bottom-[20%] left-[12%] h-3 w-24 rounded-full bg-cyan-400/40 blur-md animate-pulse-glow" />
        <div className="absolute top-[22%] right-[20%] h-3 w-20 rounded-full bg-indigo-400/40 blur-md animate-pulse-glow" />
      </div>

      <div className="relative z-10 rounded-[34px] border border-cyan-300/18 bg-[radial-gradient(circle_at_top_right,_rgba(56,189,248,0.14),_transparent_26%),linear-gradient(135deg,_rgba(15,23,42,0.9)_0%,_rgba(15,23,42,0.72)_100%)] p-7 shadow-[0_28px_80px_-40px_rgba(0,0,0,0.95)] backdrop-blur-xl">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 text-sm font-semibold text-cyan-300">
              <BarChart3 size={16} />
              Platform Analysis
            </div>
            <h1 className="mt-2 text-4xl font-semibold tracking-tight text-white">How efficiently your users are using the platform</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              This replaces the old AI Power tab with a usage analysis view. It estimates department adoption, worker patterns, and workflow efficiency from your live workflows, triggers, runs, and connected apps.
            </p>
          </div>
          <div className="flex flex-col items-end gap-4">
            <AnalyzeScene />
            <div className="w-full rounded-3xl border border-white/10 bg-white/10 px-5 py-4 shadow-[0_18px_45px_-28px_rgba(0,0,0,0.95)] backdrop-blur-md">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Overall Health</div>
              <div className="mt-2 text-3xl font-semibold text-white">{averageEfficiency}/100</div>
              <div className="mt-1 text-sm text-slate-300">{healthLabel}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Activity} label="Efficiency Score" value={averageEfficiency} tone="indigo" hint="Weighted by reliability, activation, and workflow depth" />
        <StatCard icon={Briefcase} label="Top Department" value={topDepartments[0]?.name || 'General'} tone="sky" hint={`${topDepartments[0]?.count || 0} workflows inferred`} />
        <StatCard icon={Users} label="Main Worker Type" value={topWorkers[0]?.name || 'General'} tone="emerald" hint={`${topWorkers[0]?.count || 0} workflow patterns`} />
        <StatCard icon={ShieldCheck} label="Success Rate" value={`${successRate}%`} tone="amber" hint={`${analytics?.success_runs || 0} successful runs out of ${totalRuns}`} />
      </div>

      <div className="relative z-10 grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
        <div className="rounded-3xl border border-white/10 bg-white/8 p-6 shadow-[0_24px_60px_-34px_rgba(0,0,0,0.95)] backdrop-blur-md">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-sm font-semibold text-white">Usage Breakdown</div>
              <div className="mt-1 text-sm text-slate-300">Department and worker signals inferred from workflows and app usage.</div>
            </div>
            <div className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-200">
              <ArrowUpRight size={13} />
              Live from current workspace
            </div>
          </div>

          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div>
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                <Briefcase size={15} className="text-indigo-300" />
                Departments
              </div>
              <div className="space-y-3">
                {topDepartments.length === 0 && <div className="text-sm text-slate-400">No workflows available yet.</div>}
                {topDepartments.map(item => (
                  <div key={item.name}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-100">{item.name}</span>
                      <span className="text-slate-400">{item.count}</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10">
                      <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${totalWorkflows ? (item.count / totalWorkflows) * 100 : 0}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                <Users size={15} className="text-emerald-300" />
                Worker Personas
              </div>
              <div className="space-y-3">
                {topWorkers.length === 0 && <div className="text-sm text-slate-400">No worker patterns inferred yet.</div>}
                {topWorkers.map(item => (
                  <div key={item.name}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-100">{item.name}</span>
                      <span className="text-slate-400">{item.count}</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10">
                      <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${totalWorkflows ? (item.count / totalWorkflows) * 100 : 0}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/8 p-6 shadow-[0_24px_60px_-34px_rgba(0,0,0,0.95)] backdrop-blur-md">
          <div className="text-sm font-semibold text-white">Operational Signals</div>
          <div className="mt-1 text-sm text-slate-300">A quick read on adoption and platform efficiency.</div>

          <div className="mt-5 space-y-4">
            <div className="rounded-2xl bg-white/8 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                <Workflow size={15} className="text-indigo-300" />
                Workflow Activation
              </div>
              <div className="mt-2 text-2xl font-semibold text-white">{automationCoverage}%</div>
              <div className="mt-1 text-sm text-slate-300">{activeWorkflows} of {totalWorkflows} workflows are currently on.</div>
            </div>

            <div className="rounded-2xl bg-white/8 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                <Layers3 size={15} className="text-sky-300" />
                App Footprint
              </div>
              <div className="mt-2 text-2xl font-semibold text-white">{usedApps.size}</div>
              <div className="mt-1 text-sm text-slate-300">{connections.length} connections mapped across {apps.length} available apps.</div>
            </div>

            <div className="rounded-2xl bg-white/8 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                <Clock3 size={15} className="text-amber-300" />
                Run Intensity
              </div>
              <div className="mt-2 text-2xl font-semibold text-white">{totalRuns}</div>
              <div className="mt-1 text-sm text-slate-300">Total runs recorded, with {analytics?.active_workflows || 0} active workflows contributing.</div>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 grid gap-6 lg:grid-cols-[1.25fr_0.95fr]">
        <div className="rounded-3xl border border-white/10 bg-white/8 p-6 shadow-[0_24px_60px_-34px_rgba(0,0,0,0.95)] backdrop-blur-md">
          <div className="text-sm font-semibold text-white">Most Efficient Workflow Patterns</div>
          <div className="mt-1 text-sm text-slate-300">Estimated using depth, reliability, and whether the workflow is live.</div>

          <div className="mt-5 space-y-3">
            {topWorkflowRows.length === 0 && <div className="text-sm text-slate-400">No workflows to analyze yet.</div>}
            {topWorkflowRows.map(workflow => (
              <div key={workflow.id} className="rounded-2xl border border-white/10 bg-white/8 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-white">{workflow.name}</div>
                    <div className="mt-1 text-sm text-slate-300">{workflow.department} - {workflow.worker}</div>
                  </div>
                  <div className="rounded-full bg-white/12 px-3 py-1 text-sm font-semibold text-white shadow-sm">
                    {workflow.efficiency}/100
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-200">
                  <span className="rounded-full bg-white/10 px-2.5 py-1">{workflow.stepCount} steps</span>
                  <span className="rounded-full bg-white/10 px-2.5 py-1">{workflow.run_count || 0} runs</span>
                  <span className="rounded-full bg-white/10 px-2.5 py-1">{workflow.status === 'on' ? 'active' : 'inactive'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/8 p-6 shadow-[0_24px_60px_-34px_rgba(0,0,0,0.95)] backdrop-blur-md">
          <div className="text-sm font-semibold text-white">Key Insights</div>
          <div className="mt-1 text-sm text-slate-300">Fast summary of who is using the platform and how well.</div>

          <div className="mt-5 space-y-3">
            {insights.map((insight, index) => (
              <div key={index} className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3 text-sm text-slate-200">
                {insight}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

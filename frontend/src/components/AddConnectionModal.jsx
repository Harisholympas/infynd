import React, { useMemo, useRef, useState } from 'react'
import { Plug, Loader2, CheckCircle, Upload, FileText, Sparkles } from 'lucide-react'
import clsx from 'clsx'
import { connectionAPI } from '../utils/api'
import useStore from '../store/useStore'
import { APP_COLORS } from '../utils/constants'

export default function AddConnectionModal({ app, onClose, onAdded }) {
  const [name, setName] = useState(`My ${app?.name || 'App'}`)
  const [creds, setCreds] = useState({})
  const [saving, setSaving] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [resumeFile, setResumeFile] = useState(null)
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const { notify } = useStore()
  const fileInputRef = useRef(null)

  const fields = useMemo(() => app?.credential_fields || [], [app])
  const color = APP_COLORS[app?.key] || '#6366f1'
  const isResumeScreener = app?.key === 'resume_screener'

  const handleResumePick = (file) => {
    if (!file) return
    setResumeFile(file)
    setAnalysis(null)
  }

  const handleAnalyzeResume = async () => {
    if (!resumeFile) {
      notify('Upload a resume first', 'error')
      return
    }
    setAnalyzing(true)
    try {
      const res = await connectionAPI.analyzeResume(resumeFile, jobTitle, jobDescription)
      setAnalysis(res.analysis)
      notify('Resume analyzed successfully', 'success')
    } catch (err) {
      notify(err.message, 'error')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSave = async () => {
    if (!app?.key) return
    if (!name.trim()) return
    setSaving(true)
    try {
      const res = await connectionAPI.create({ app_key: app.key, name, credentials: creds })
      onAdded?.(res)
      notify(`Connected to ${app.name}`, 'success')
      onClose?.()
    } catch (err) {
      notify(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  if (!app) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm">
      <div className="panel w-full max-w-lg animate-slide-up rounded-3xl">
        <div className="flex items-center gap-3 border-b border-slate-200 bg-slate-50/80 p-5">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-2xl text-xl shadow-sm"
            style={{ background: `${color}15` }}
          >
            {app.icon}
          </div>
          <div className="min-w-0">
            <div className="truncate text-base font-semibold text-gray-900">Connect {app.name}</div>
            <div className="truncate text-sm text-gray-600">{app.description}</div>
          </div>
          <button onClick={onClose} className="ml-auto rounded-full p-2 text-gray-500 transition hover:bg-white hover:text-gray-700">
            ×
          </button>
        </div>

        <div className="space-y-5 p-6">
          <div>
            <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">Account Label</label>
            <input
              className="input text-sm"
              placeholder={`e.g. Work ${app.name}`}
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>

          {isResumeScreener ? (
            <div className="space-y-4">
              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setDragging(false)
                  handleResumePick(e.dataTransfer.files?.[0])
                }}
                onClick={() => fileInputRef.current?.click()}
                className={clsx(
                  'cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition-all',
                  dragging ? 'border-indigo-500 bg-indigo-50 shadow-sm' : 'border-gray-300 bg-gray-50 hover:border-indigo-300'
                )}
              >
                <Upload className="mx-auto mb-2 h-8 w-8 text-indigo-600" />
                <div className="text-sm font-semibold text-gray-900">Drag and drop a resume here</div>
                <div className="mt-1 text-sm text-gray-600">or click to upload PDF, DOCX, or TXT</div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                  onChange={(e) => handleResumePick(e.target.files?.[0])}
                />
              </div>

              {resumeFile && (
                <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
                  <FileText size={15} className="text-indigo-600" />
                  <span className="font-medium">{resumeFile.name}</span>
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">Job Title</label>
                <input
                  className="input text-sm"
                  placeholder="e.g. Frontend Developer"
                  value={jobTitle}
                  onChange={e => setJobTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">Job Description</label>
                <textarea
                  className="input h-28 resize-none text-sm leading-6"
                  placeholder="Paste the role description for better candidate fit analysis"
                  value={jobDescription}
                  onChange={e => setJobDescription(e.target.value)}
                />
              </div>

              <button onClick={handleAnalyzeResume} disabled={analyzing || !resumeFile} className="btn-primary w-full justify-center">
                {analyzing ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                Analyze Resume
              </button>

              {analysis && (
                <div className="space-y-3 rounded-2xl border border-indigo-200 bg-indigo-50 p-4">
                  <div className="text-sm font-semibold text-indigo-900">Resume Summary</div>
                  <div className="text-sm leading-6 text-gray-800">{analysis.summary}</div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <div className="text-gray-500">Candidate</div>
                      <div className="font-medium text-gray-900">{analysis.candidate_name || 'Unknown'}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Fit Score</div>
                      <div className="font-medium text-gray-900">{analysis.job_fit_score ?? 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Grade</div>
                      <div className="font-medium text-gray-900">{analysis.grade || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Shortlist</div>
                      <div className="font-medium capitalize text-gray-900">{analysis.shortlist_decision || 'maybe'}</div>
                    </div>
                    {analysis.email && (
                      <div>
                        <div className="text-gray-500">Email</div>
                        <div className="break-all font-medium text-gray-900">{analysis.email}</div>
                      </div>
                    )}
                    {analysis.experience_years != null && (
                      <div>
                        <div className="text-gray-500">Experience</div>
                        <div className="font-medium text-gray-900">{analysis.experience_years} years</div>
                      </div>
                    )}
                  </div>
                  {analysis.skills?.length > 0 && (
                    <div>
                      <div className="mb-1 text-xs text-gray-500">Key Skills</div>
                      <div className="flex flex-wrap gap-1.5">
                        {analysis.skills.map(skill => (
                          <span key={skill} className="rounded-full border border-indigo-200 bg-white px-2 py-1 text-[11px] text-indigo-800">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {analysis.strengths?.length > 0 && (
                    <div>
                      <div className="mb-1 text-xs text-gray-500">Strengths</div>
                      <div className="space-y-1">
                        {analysis.strengths.map(item => (
                          <div key={item} className="text-xs text-gray-700">- {item}</div>
                        ))}
                      </div>
                    </div>
                  )}
                  {analysis.risks?.length > 0 && (
                    <div>
                      <div className="mb-1 text-xs text-gray-500">Risks</div>
                      <div className="space-y-1">
                        {analysis.risks.map(item => (
                          <div key={item} className="text-xs text-gray-700">- {item}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : app.auth_type === 'none' ? (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700">
              <CheckCircle size={13} className="text-emerald-600" />
              No authentication required for {app.name}
            </div>
          ) : (
            fields.map(field => (
              <div key={field.key}>
                <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500">{field.label}</label>
                {field.type === 'textarea' ? (
                  <textarea
                    className="input codeish h-28 resize-none text-xs"
                    placeholder={field.help || ''}
                    value={creds[field.key] || ''}
                    onChange={e => setCreds(c => ({ ...c, [field.key]: e.target.value }))}
                  />
                ) : (
                  <input
                    className="input text-sm"
                    type={field.type === 'password' ? 'password' : 'text'}
                    placeholder={field.help || ''}
                    value={creds[field.key] || ''}
                    onChange={e => setCreds(c => ({ ...c, [field.key]: e.target.value }))}
                  />
                )}
                {field.help && <p className="mt-1 text-[10px] text-gray-500">{field.help}</p>}
              </div>
            ))
          )}
        </div>

        <div className={clsx('flex items-center gap-3 border-t border-slate-200 p-5', saving && 'opacity-95')}>
          <button onClick={onClose} className="btn-secondary flex-1 justify-center" disabled={saving}>
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 justify-center">
            {saving ? <Loader2 size={13} className="animate-spin" /> : <Plug size={13} />}
            {isResumeScreener ? 'Save Tool' : 'Connect'}
          </button>
        </div>
      </div>
    </div>
  )
}

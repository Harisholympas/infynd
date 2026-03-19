import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Brain, Loader2, Mic, MicOff, Sparkles, Wand2, CheckCircle2, ArrowRight, AlertCircle, Upload, FileText } from 'lucide-react'
import { aiAPI, connectionAPI } from '../utils/api'
import { createWorkflowDraft, normalizeAIResult } from '../utils/aiWorkflow'
import useStore from '../store/useStore'

const SWEAR_WORDS = [
  'arse',
  'arsehole',
  'ass',
  'assface',
  'asshat',
  'asshole',
  'asswipe',
  'bastard',
  'beeyotch',
  'biatch',
  'bimbo',
  'bitch',
  'bitchy',
  'bloody',
  'blowjob',
  'bollocks',
  'boner',
  'boob',
  'boobs',
  'booty',
  'bs',
  'bugger',
  'bullcrap',
  'bullshit',
  'buttface',
  'chutiya',
  'clusterfuck',
  'cock',
  'crap',
  'crappy',
  'cunt',
  'dammit',
  'damn',
  'darn',
  'dick',
  'dickhead',
  'dildo',
  'dipshit',
  'douche',
  'douchebag',
  'dumbarse',
  'dumbass',
  'effing',
  'fag',
  'faggot',
  'fck',
  'feck',
  'flipping',
  'freaking',
  'frigging',
  'fuck',
  'fucked',
  'fucker',
  'fuckers',
  'fucking',
  'goddamn',
  'gonna',
  'gotta',
  'hell',
  'hooker',
  'idiot',
  'jackass',
  'jerk',
  'jerkoff',
  'kamina',
  'knob',
  'knobhead',
  'lmao',
  'lmfao',
  'loser',
  'mf',
  'mofo',
  'moron',
  'motherfucker',
  'nigga',
  'nuts',
  'pissed',
  'piss',
  'pissing',
  'prick',
  'pussy',
  'retard',
  'screwup',
  'sexist',
  'shag',
  'shit',
  'shite',
  'shitface',
  'shithead',
  'shitty',
  'slut',
  'sonofabitch',
  'stfu',
  'suck',
  'sucks',
  'sucker',
  'suckup',
  'tit',
  'tits',
  'twat',
  'wanker',
  'whore',
  'wtf',
  'yakka',
  'you suck',
  'zandu',
]

function PreviewPill({ label, value }) {
  return (
    <div className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-[11px] text-indigo-800 shadow-sm">
      <span className="font-semibold">{label}:</span> {value}
    </div>
  )
}

export default function WorkflowAIAssistant({
  embedded = false,
  title = 'AI Workflow Builder',
  subtitle = 'Describe the job in text or voice and AI will prepare the workflow for you.',
  onApplyDraft,
}) {
  const { apps, setEditingWorkflow, setActiveView, notify } = useStore()
  const [prompt, setPrompt] = useState('')
  const [mode, setMode] = useState('text')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [supportsBrowserSTT, setSupportsBrowserSTT] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [result, setResult] = useState(null)
  const [draft, setDraft] = useState(null)
  const [error, setError] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [resumeJobTitle, setResumeJobTitle] = useState('')
  const [resumeJobDescription, setResumeJobDescription] = useState('')
  const [resumeAnalysis, setResumeAnalysis] = useState(null)
  const [analyzingResume, setAnalyzingResume] = useState(false)
  const [draggingResume, setDraggingResume] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)
  const recognitionRef = useRef(null)
  const resumeInputRef = useRef(null)

  const activeInput = useMemo(() => {
    if (mode === 'voice') return transcript.trim() || prompt.trim()
    return prompt.trim() || transcript.trim()
  }, [mode, prompt, transcript])
  const aiSummary = useMemo(() => normalizeAIResult(result || {}), [result])
  const detectedSwearWords = useMemo(() => {
    const text = prompt.toLowerCase()
    return SWEAR_WORDS.filter(word => new RegExp(`\\b${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i').test(text))
  }, [prompt])
  const needsResumeUpload = useMemo(() => {
    const text = `${activeInput} ${draft?.aiDraft?.task || ''}`.toLowerCase()
    const hasResumeStep = (draft?.steps || []).some(step => step.app_key === 'resume_screener')
    return hasResumeStep || text.includes('resume') || text.includes('cv') || text.includes('candidate')
  }, [activeInput, draft])

  useEffect(() => {
    // Cleanup media stream on unmount
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  useEffect(() => {
    // Detect browser speech recognition support once on mount
    if (typeof window === 'undefined') return
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    try {
      const rec = new SR()
      rec.continuous = false
      rec.interimResults = false
      rec.lang = 'en-US'
      recognitionRef.current = rec
      setSupportsBrowserSTT(true)
    } catch {
      recognitionRef.current = null
      setSupportsBrowserSTT(false)
    }
  }, [])

  const applyDraft = (nextDraft, successMessage) => {
    setDraft(nextDraft)
    if (onApplyDraft) {
      onApplyDraft(nextDraft)
    } else {
      setEditingWorkflow(nextDraft)
      setActiveView('editor')
    }
    notify(successMessage, 'success')
  }

  const applyResumeAnalysisToDraft = (analysis, fileName = '') => {
    if (!draft) return
    const nextDraft = {
      ...draft,
      steps: (draft.steps || []).map(step => (
        step.app_key === 'resume_screener'
          ? {
              ...step,
              input_map: {
                ...step.input_map,
                resume_text: analysis.resume_text_preview || step.input_map?.resume_text || '',
                job_title: resumeJobTitle || step.input_map?.job_title || '',
                job_description: resumeJobDescription || step.input_map?.job_description || '',
              },
            }
          : step
      )),
      aiDraft: {
        ...draft.aiDraft,
        resumeAnalysis: analysis.analysis,
        resumeFileName: fileName,
      },
    }
    setResumeAnalysis(analysis.analysis)
    applyDraft(nextDraft, 'Resume analysis added to workflow draft')
  }

  const generateDraft = async (inputText) => {
    const cleaned = inputText.trim()
    if (!cleaned) {
      setError('Describe the workflow you want to automate first')
      return
    }
    if (detectedSwearWords.length > 0) {
      const message = `Please remove inappropriate language from the prompt: ${detectedSwearWords.join(', ')}`
      setError(message)
      notify(message, 'error')
      return
    }

    setIsGenerating(true)
    setError('')

    try {
      const dept = await aiAPI.inferDepartment(cleaned).catch(() => ({ inferred_department: 'general' }))
      const config = await aiAPI.configureAgent(cleaned, dept.inferred_department || 'general')
      const merged = { ...config, department: dept.inferred_department }
      setResult(merged)
      const nextDraft = createWorkflowDraft(merged, apps, cleaned)
      applyDraft(nextDraft, 'AI prepared a workflow draft for review')
    } catch (err) {
      const fallbackResponse = {
        parsed: { intent: cleaned, department: 'general', confidence: 0.35 },
        confidence: 0.35,
      }
      setResult(fallbackResponse)
      const nextDraft = createWorkflowDraft(fallbackResponse, apps, cleaned)
      setError(err.message || 'AI configuration failed, so a fallback draft was created')
      applyDraft(nextDraft, 'Fallback workflow draft created for review')
    } finally {
      setIsGenerating(false)
    }
  }

  const transcribeBlob = async (blob) => {
    setIsGenerating(true)
    setError('')
    try {
      const reader = new FileReader()
      const base64Audio = await new Promise((resolve, reject) => {
        reader.onloadend = () => {
          const output = reader.result
          if (typeof output !== 'string') {
            reject(new Error('Unable to read recorded audio'))
            return
          }
          resolve(output.split(',')[1])
        }
        reader.onerror = () => reject(new Error('Unable to read recorded audio'))
        reader.readAsDataURL(blob)
      })

      const transcription = await aiAPI.transcribeAudio(base64Audio)
      const spokenText = transcription.transcribed_text || ''
      if (!spokenText.trim()) {
        throw new Error('No speech was detected in the recording')
      }
      setTranscript(spokenText)
      setPrompt(spokenText)

      const voiceResult = await aiAPI.processVoiceCommand(spokenText, true).catch(() => ({
        parsed: transcription.parsed,
        confidence: transcription.confidence,
      }))

      const merged = { ...voiceResult, parsed: voiceResult.parsed || transcription.parsed, voice_input: spokenText }
      setResult(merged)
      const nextDraft = createWorkflowDraft(merged, apps, spokenText)
      applyDraft(nextDraft, 'Voice command converted into a workflow draft')
    } catch (err) {
      setError(err.message || 'Voice command could not be processed')
    } finally {
      setIsGenerating(false)
    }
  }

  const startRecordingWithWhisper = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []
      const preferredMime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : undefined
      const mediaRecorder = preferredMime ? new MediaRecorder(stream, { mimeType: preferredMime }) : new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      mediaRecorder.onstop = async () => {
        const mime = preferredMime || mediaRecorder.mimeType || 'audio/webm'
        const audioBlob = new Blob(chunksRef.current, { type: mime })
        await transcribeBlob(audioBlob)
      }
      mediaRecorder.start()
      setMode('voice')
      setIsRecording(true)
      setError('')
    } catch (err) {
      setError(err.message || 'Microphone access was denied')
    }
  }

  const stopRecordingWithWhisper = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    setIsRecording(false)
  }

  const startBrowserSpeech = () => {
    const rec = recognitionRef.current
    if (!rec) {
      // Fallback to Whisper-based recording if STT not available
      startRecordingWithWhisper()
      return
    }
    try {
      setMode('voice')
      setIsRecording(true)
      setError('')

      rec.onresult = (event) => {
        try {
          const text = event.results[0][0]?.transcript || ''
          const cleaned = text.trim()
          if (!cleaned) {
            setError('No speech was detected')
          } else {
            setTranscript(cleaned)
            setPrompt(cleaned)
            // Directly generate a draft from recognized text
            generateDraft(cleaned)
          }
        } finally {
          setIsRecording(false)
        }
      }

      rec.onerror = (e) => {
        setError(e.error || 'Browser speech recognition failed')
        setIsRecording(false)
      }

      rec.onend = () => {
        setIsRecording(false)
      }

      rec.start()
    } catch (err) {
      setError(err.message || 'Browser speech recognition failed to start')
      setIsRecording(false)
    }
  }

  const stopBrowserSpeech = () => {
    const rec = recognitionRef.current
    if (rec) {
      try {
        rec.stop()
      } catch {
        // ignore
      }
    }
    setIsRecording(false)
  }

  const handleVoiceToggle = () => {
    if (isRecording) {
      if (supportsBrowserSTT && recognitionRef.current) {
        stopBrowserSpeech()
      } else {
        stopRecordingWithWhisper()
      }
    } else {
      if (supportsBrowserSTT && recognitionRef.current) {
        startBrowserSpeech()
      } else {
        startRecordingWithWhisper()
      }
    }
  }

  const handleResumePick = (file) => {
    if (!file) return
    setResumeFile(file)
    setResumeAnalysis(null)
  }

  const analyzeResumeInWorkflow = async () => {
    if (!resumeFile) {
      setError('Upload a resume file first')
      return
    }
    setAnalyzingResume(true)
    setError('')
    try {
      const response = await connectionAPI.analyzeResume(resumeFile, resumeJobTitle, resumeJobDescription)
      applyResumeAnalysisToDraft(response, resumeFile.name)
    } catch (err) {
      setError(err.message || 'Resume analysis failed')
    } finally {
      setAnalyzingResume(false)
    }
  }

  return (
    <div className={`panel overflow-hidden rounded-3xl ${embedded ? 'border-indigo-200/80 bg-white/95' : 'bg-white/95'}`}>
      <div className={`${embedded ? 'bg-gradient-to-r from-indigo-50 to-sky-50' : 'bg-gradient-to-r from-indigo-600 via-indigo-600 to-sky-600'} p-6 ${embedded ? 'text-gray-900' : 'text-white'}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2">
              <Brain className={`h-5 w-5 ${embedded ? 'text-indigo-600' : 'text-white'}`} />
              <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
            </div>
            <p className={`mt-2 text-sm leading-6 ${embedded ? 'text-gray-600' : 'text-indigo-100'}`}>{subtitle}</p>
          </div>
          <div className={`rounded-full px-3 py-1.5 text-[11px] font-semibold shadow-sm ${embedded ? 'border border-indigo-200 bg-white text-indigo-700' : 'bg-white/15 text-white'}`}>
            Prompt or voice
          </div>
        </div>
      </div>

      <div className="space-y-6 p-6">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setMode('text')}
            className={`rounded-full px-3.5 py-2 text-xs font-semibold transition-all ${mode === 'text' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
          >
            Text prompt
          </button>
          <button
            type="button"
            onClick={() => setMode('voice')}
            className={`rounded-full px-3.5 py-2 text-xs font-semibold transition-all ${mode === 'voice' ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
          >
            Voice command
          </button>
        </div>

        <div className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <label className="text-sm font-semibold text-slate-900">Describe the workflow</label>
                <span className="text-xs text-slate-500">Plain language works best</span>
              </div>
              <p className="text-sm leading-6 text-slate-600">
                Explain what should happen, which tools to use, and the result you want. The AI will draft the workflow structure for you.
              </p>
            </div>

            <textarea
              rows="5"
              value={prompt}
              onChange={(e) => {
                setMode('text')
                setPrompt(e.target.value)
                if (error) setError('')
              }}
              className="input min-h-[168px] resize-none leading-7"
              placeholder="Example: Every weekday at 9am collect new sales leads, score them, add them to Airtable, and send a Slack summary to the team."
            />

            {detectedSwearWords.length > 0 && (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                Inappropriate language detected in the prompt: {detectedSwearWords.join(', ')}. Please edit the text before continuing.
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => generateDraft(activeInput)}
                disabled={isGenerating || !activeInput || detectedSwearWords.length > 0}
                className="btn-primary"
              >
                {isGenerating ? <Loader2 size={14} className="animate-spin" /> : <Wand2 size={14} />}
                Generate Workflow
              </button>

              <button
                type="button"
                onClick={handleVoiceToggle}
                disabled={isGenerating}
                className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all ${isRecording ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}
              >
                {isRecording ? <MicOff size={14} /> : <Mic size={14} />}
                {isRecording ? 'Stop Recording' : 'Record Voice'}
              </button>
            </div>

            {transcript && (
              <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-700">Voice transcript</div>
                <p className="mt-2 text-sm leading-6 text-sky-950">{transcript}</p>
              </div>
            )}

            {error && (
              <div className="flex items-start gap-2 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {needsResumeUpload && (
              <div className="space-y-4 rounded-3xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 p-5">
                <div>
                  <div className="text-sm font-semibold text-amber-950">Resume Upload For Workflow</div>
                  <div className="mt-1 text-sm leading-6 text-amber-900/80">
                    Upload the resume here and the workflow will use the extracted text in the Resume Screener step.
                  </div>
                </div>

                <div
                  onDragOver={(e) => { e.preventDefault(); setDraggingResume(true) }}
                  onDragLeave={() => setDraggingResume(false)}
                  onDrop={(e) => {
                    e.preventDefault()
                    setDraggingResume(false)
                    handleResumePick(e.dataTransfer.files?.[0])
                  }}
                  onClick={() => resumeInputRef.current?.click()}
                  className={`cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition-all ${draggingResume ? 'border-amber-500 bg-white shadow-sm' : 'border-amber-300 bg-white/85 hover:border-amber-400'}`}
                >
                  <Upload className="mx-auto mb-2 h-7 w-7 text-amber-700" />
                  <div className="text-sm font-semibold text-gray-900">Drag and drop resume here</div>
                  <div className="mt-1 text-sm text-gray-600">PDF, DOCX, or TXT</div>
                  <input
                    ref={resumeInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt"
                    className="hidden"
                    onChange={(e) => handleResumePick(e.target.files?.[0])}
                  />
                </div>

                {resumeFile && (
                  <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-white p-3 text-sm text-gray-800 shadow-sm">
                    <FileText size={15} className="text-amber-700" />
                    <span className="font-medium">{resumeFile.name}</span>
                  </div>
                )}

                <input
                  className="input text-sm"
                  placeholder="Target job title"
                  value={resumeJobTitle}
                  onChange={(e) => setResumeJobTitle(e.target.value)}
                />

                <textarea
                  rows="3"
                  className="input resize-none leading-6"
                  placeholder="Optional job description for better screening"
                  value={resumeJobDescription}
                  onChange={(e) => setResumeJobDescription(e.target.value)}
                />

                <button
                  type="button"
                  onClick={analyzeResumeInWorkflow}
                  disabled={analyzingResume || !resumeFile}
                  className="btn-primary"
                >
                  {analyzingResume ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  Analyze Resume In Workflow
                </button>

                {resumeAnalysis && (
                  <div className="space-y-3 rounded-2xl border border-amber-200 bg-white p-4 shadow-sm">
                    <div className="text-sm font-semibold text-gray-900">Resume Summary</div>
                    <div className="text-sm leading-6 text-gray-700">{resumeAnalysis.summary}</div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      {resumeAnalysis.candidate_name && <PreviewPill label="Candidate" value={resumeAnalysis.candidate_name} />}
                      {resumeAnalysis.job_fit_score != null && <PreviewPill label="Fit" value={resumeAnalysis.job_fit_score} />}
                      {resumeAnalysis.grade && <PreviewPill label="Grade" value={resumeAnalysis.grade} />}
                      {resumeAnalysis.shortlist_decision && <PreviewPill label="Shortlist" value={resumeAnalysis.shortlist_decision} />}
                      {resumeAnalysis.experience_years != null && <PreviewPill label="Years" value={resumeAnalysis.experience_years} />}
                    </div>
                    {resumeAnalysis.strengths?.length > 0 && (
                      <div>
                        <div className="mb-1 text-xs text-gray-500">Strengths</div>
                        <div className="space-y-1">
                          {resumeAnalysis.strengths.map(item => (
                            <div key={item} className="text-xs text-gray-700">- {item}</div>
                          ))}
                        </div>
                      </div>
                    )}
                    {resumeAnalysis.risks?.length > 0 && (
                      <div>
                        <div className="mb-1 text-xs text-gray-500">Risks</div>
                        <div className="space-y-1">
                          {resumeAnalysis.risks.map(item => (
                            <div key={item} className="text-xs text-gray-700">- {item}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-50/85 p-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
              <Sparkles size={15} className="text-indigo-600" />
              AI Preview
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Review the generated trigger and steps before saving or editing the workflow.
            </p>

            {draft ? (
              <div className="mt-4 space-y-4">
                <div className="space-y-3">
                  <div className="text-base font-semibold text-gray-900">{draft.name}</div>
                  <div className="flex flex-wrap gap-2">
                    <PreviewPill label="Dept" value={aiSummary.department || 'general'} />
                    <PreviewPill label="Trigger" value={draft.trigger_config?.type || 'manual'} />
                    <PreviewPill label="Steps" value={draft.steps.length} />
                  </div>
                </div>

                {draft.steps.length > 0 && (
                  <div className="space-y-2.5">
                    {draft.steps.map((step, index) => (
                      <div key={`${step.app_key}-${index}`} className="rounded-2xl border border-slate-200 bg-white px-3 py-3 shadow-sm">
                        <div className="flex items-center gap-2 text-sm text-gray-700">
                          <CheckCircle2 size={14} className="text-emerald-500" />
                          <span className="font-medium capitalize">{step.app_key.replace(/_/g, ' ')}</span>
                          <ArrowRight size={12} className="text-gray-400" />
                          <span className="text-gray-500">{step.action || 'choose action'}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {draft.aiDraft?.reasoning && (
                  <div className="rounded-2xl border border-slate-200 bg-white p-3 text-sm leading-6 text-gray-600 shadow-sm">
                    {draft.aiDraft.reasoning}
                  </div>
                )}
              </div>
            ) : (
              <p className="mt-4 text-sm leading-6 text-gray-500">
                AI will infer the trigger, choose likely apps, and draft the workflow steps here.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

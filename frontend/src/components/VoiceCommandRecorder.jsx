import React from 'react'
import WorkflowAIAssistant from './WorkflowAIAssistant'

export default function VoiceCommandRecorder() {
  return (
    <WorkflowAIAssistant
      title="Voice Workflow Builder"
      subtitle="Speak the task out loud or paste the transcript. AI will turn it into an editable workflow draft."
    />
  )
}

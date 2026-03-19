import React, { useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Notifications from './components/Notifications'
import Dashboard from './pages/Dashboard'
import WorkflowsPage from './pages/WorkflowsPage'
import WorkflowEditor from './pages/WorkflowEditor'
import ConnectionsPage from './pages/ConnectionsPage'
import HistoryPage from './pages/HistoryPage'
import AnalyzePage from './pages/AnalyzePage'
import useStore from './store/useStore'
import { workflowAPI, connectionAPI, analyticsAPI } from './utils/api'

const PAGES = {
  dashboard: Dashboard,
  workflows: WorkflowsPage,
  editor: WorkflowEditor,
  connections: ConnectionsPage,
  history: HistoryPage,
  analyze: AnalyzePage,
  aipower: AnalyzePage,
}

export default function App() {
  const { activeView, setWorkflows, setConnections, setApps, setAnalytics } = useStore()
  const Page = PAGES[activeView] || Dashboard

  useEffect(() => {
    workflowAPI.list().then(d => setWorkflows(d.workflows || [])).catch(() => {})
    connectionAPI.list().then(d => setConnections(d.connections || [])).catch(() => {})
    connectionAPI.listApps().then(d => setApps(d.apps || [])).catch(() => {})
    analyticsAPI.summary().then(setAnalytics).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen flex text-gray-900 font-sans">
      <Sidebar />
      <main className="flex-1 ml-56 flex min-h-screen flex-col">
        <div className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/88 px-6 py-4 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 shadow-sm">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-900">AutoFlow Workspace</div>
                <div className="text-xs text-slate-500">Build and review automations in one place</div>
              </div>
            </div>
            <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
              AutoFlow v2 · Local · Private
            </div>
          </div>
        </div>

        <div className="flex-1 p-6">
          <Page />
        </div>
      </main>
      <Notifications />
    </div>
  )
}

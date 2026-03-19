import React from 'react'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import useStore from '../store/useStore'
import clsx from 'clsx'

const STYLES = {
  success: { icon: CheckCircle, cls: 'border-emerald-200 bg-emerald-50 text-emerald-800' },
  error:   { icon: AlertCircle, cls: 'border-red-200 bg-red-50 text-red-800' },
  info:    { icon: Info,         cls: 'border-indigo-200 bg-indigo-50 text-indigo-800' },
}

export default function Notifications() {
  const { notifications, dismissNotif } = useStore()
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {notifications.map(n => {
        const { icon: Icon, cls } = STYLES[n.type] || STYLES.info
        return (
          <div key={n.id}
            className={clsx('flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-lg animate-slide-up shadow-2xl pointer-events-auto', cls)}>
            <Icon size={15} className="flex-shrink-0" />
            <span className="text-sm font-medium flex-1">{n.msg}</span>
            <button onClick={() => dismissNotif(n.id)} className="opacity-50 hover:opacity-100 transition-opacity">
              <X size={13} />
            </button>
          </div>
        )
      })}
    </div>
  )
}

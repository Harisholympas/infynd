export const APP_COLORS = {
  gmail: '#EA4335', slack: '#4A154B', google_sheets: '#0F9D58',
  notion: '#000000', airtable: '#18BFFF', webhooks: '#FF6B35',
  formatter: '#6366f1', filter: '#8B5CF6', delay: '#F59E0B',
  storage: '#10B981', paths: '#3B82F6', schedule: '#EF4444',
  rss: '#F97316', trello: '#0052CC', github: '#24292E',
}

export const APP_CATEGORIES = {
  'Built-in Tools': ['formatter','filter','delay','storage','paths','schedule','webhooks'],
  'Email': ['gmail'],
  'Team Chat': ['slack'],
  'Spreadsheets': ['google_sheets'],
  'Productivity': ['notion'],
  'Databases': ['airtable'],
  'Project Management': ['trello'],
  'Developer Tools': ['webhooks','github'],
  'Content': ['rss'],
}

export const STATUS_STYLES = {
  on:      { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500' },
  off:     { bg: 'bg-gray-50',   text: 'text-gray-700',   border: 'border-gray-200',   dot: 'bg-gray-400' },
  error:   { bg: 'bg-red-50',     text: 'text-red-700',     border: 'border-red-200',     dot: 'bg-red-500' },
  success: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500' },
  running: { bg: 'bg-amber-50',   text: 'text-amber-700',   border: 'border-amber-200',   dot: 'bg-amber-500' },
  halted:  { bg: 'bg-orange-50',  text: 'text-orange-700',  border: 'border-orange-200',  dot: 'bg-orange-500' },
  skipped: { bg: 'bg-gray-50',   text: 'text-gray-700',   border: 'border-gray-200',   dot: 'bg-gray-400' },
}

export const OPERATOR_LABELS = {
  equals: '=', not_equals: '≠', contains: 'contains', not_contains: 'not contains',
  starts_with: 'starts with', ends_with: 'ends with',
  greater_than: '>', less_than: '<', is_empty: 'is empty', is_not_empty: 'is not empty',
  matches_regex: 'matches regex',
}

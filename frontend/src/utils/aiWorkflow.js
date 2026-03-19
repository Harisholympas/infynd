const DEFAULT_TRIGGER = { type: 'manual', config: {} }

const TOOL_TO_APP = {
  crm_query: 'airtable',
  lead_scorer: 'formatter',
  pipeline_analyzer: 'formatter',
  email_campaign: 'gmail',
  deal_tracker: 'trello',
  employee_database: 'airtable',
  job_matcher: 'formatter',
  payroll_processor: 'google_sheets',
  training_scheduler: 'google_calendar',
  performance_evaluator: 'notion',
  onboarding_manager: 'trello',
  campaign_builder: 'notion',
  content_generator: 'notion',
  analytics_tracker: 'google_sheets',
  audience_segmenter: 'formatter',
  social_manager: 'slack',
  seo_optimizer: 'formatter',
  invoice_generator: 'google_sheets',
  expense_analyzer: 'google_sheets',
  budget_planner: 'google_sheets',
  financial_reporter: 'notion',
  payment_processor: 'webhooks',
  tax_calculator: 'formatter',
  ticket_manager: 'trello',
  knowledge_base_search: 'notion',
  chatbot_integrator: 'webhooks',
  customer_feedback: 'formatter',
  issue_predictor: 'formatter',
  response_generator: 'gmail',
  email_sender: 'gmail',
  file_manager: 'notion',
  calendar_manager: 'google_calendar',
  slack_notifier: 'slack',
  data_analyzer: 'formatter',
  report_generator: 'notion',
  spreadsheet_processor: 'google_sheets',
  database_query: 'airtable',
  web_scraper: 'webhooks',
  notification_sender: 'slack',
}

const APP_ALIASES = {
  resume_screener: ['resume', 'cv', 'candidate', 'applicant', 'screening', 'shortlist'],
  gmail: ['gmail', 'email', 'mail', 'campaign', 'outreach', 'follow up'],
  slack: ['slack', 'notify', 'notification', 'message', 'alert'],
  google_sheets: ['sheet', 'spreadsheet', 'excel', 'row', 'report', 'budget', 'invoice'],
  notion: ['notion', 'document', 'doc', 'knowledge', 'wiki', 'page', 'report'],
  airtable: ['airtable', 'crm', 'database', 'record', 'table', 'lead'],
  webhooks: ['webhook', 'api', 'endpoint', 'http', 'request', 'integration'],
  formatter: ['format', 'transform', 'analyze', 'score', 'parser', 'processor'],
  filter: ['filter', 'condition', 'qualify', 'if'],
  rss: ['rss', 'feed', 'news'],
  github: ['github', 'issue', 'pull request', 'pr', 'repo'],
  trello: ['trello', 'card', 'board', 'task'],
}

const APP_ACTIONS = {
  resume_screener: {
    default: 'analyze_resume',
  },
  gmail: {
    default: 'send_email',
    search: 'find_email',
    draft: 'create_draft',
  },
  slack: {
    default: 'post_message',
    direct: 'send_dm',
  },
  google_sheets: {
    create: 'create_spreadsheet',
    default: 'append_row',
    search: 'lookup_row',
    update: 'update_row',
  },
  notion: {
    default: 'create_page',
    append: 'append_to_page',
    update: 'update_page',
  },
  airtable: {
    default: 'create_record',
    search: 'find_record',
    update: 'update_record',
  },
  webhooks: {
    default: 'post_request',
    fetch: 'get_request',
  },
  formatter: {
    default: 'text',
    numbers: 'numbers',
    dates: 'date_time',
    json: 'json',
  },
  filter: {
    default: 'only_continue_if',
  },
  github: {
    default: 'create_issue',
    comment: 'create_comment',
  },
  trello: {
    default: 'create_card',
    move: 'move_card',
    comment: 'add_comment',
  },
}

const SPECIAL_APPS = new Set(['google_calendar'])

function slugifyName(text = '') {
  const clean = text
    .replace(/[^a-z0-9\s-]/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  if (!clean) return 'AI Workflow'
  return clean
    .split(' ')
    .slice(0, 6)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function extractScheduleConfig(prompt) {
  const lower = prompt.toLowerCase()
  const timeMatch = lower.match(/\b(at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/)
  const twentyFourHour = lower.match(/\b(\d{1,2}):(\d{2})\b/)
  const time = timeMatch
    ? normalizeTime(timeMatch[2], timeMatch[3] || '00', timeMatch[4])
    : twentyFourHour
      ? `${String(Number(twentyFourHour[1])).padStart(2, '0')}:${twentyFourHour[2]}`
      : '09:00'

  if (lower.includes('every hour') || lower.includes('hourly')) {
    return { type: 'schedule', config: { trigger_action: 'every_hour' } }
  }
  if (lower.includes('every') && lower.includes('minute')) {
    const intervalMatch = lower.match(/every\s+(\d+)\s+minute/)
    return {
      type: 'schedule',
      config: { trigger_action: 'every_x_minutes', interval: Number(intervalMatch?.[1] || 15) },
    }
  }
  if (lower.includes('every week') || lower.includes('weekly')) {
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    const day = days.find(entry => lower.includes(entry)) || 'monday'
    return { type: 'schedule', config: { trigger_action: 'every_week', day, time } }
  }
  if (lower.includes('every month') || lower.includes('monthly')) {
    return { type: 'schedule', config: { trigger_action: 'every_month', time } }
  }
  return { type: 'schedule', config: { trigger_action: 'every_day', time } }
}

function normalizeTime(hours, minutes, meridian) {
  let normalizedHours = Number(hours)
  if (meridian === 'pm' && normalizedHours < 12) normalizedHours += 12
  if (meridian === 'am' && normalizedHours === 12) normalizedHours = 0
  return `${String(normalizedHours).padStart(2, '0')}:${String(Number(minutes)).padStart(2, '0')}`
}

function inferTrigger(prompt = '', parsed = {}) {
  const lower = prompt.toLowerCase()
  if (lower.includes('webhook') || lower.includes('api call') || lower.includes('endpoint')) {
    return { type: 'webhook', config: {} }
  }
  if (lower.includes('rss') || lower.includes('feed')) {
    return { type: 'rss', config: { feed_url: '' } }
  }
  // Explicit schedule keywords (strong signal)
  const hasScheduleKeyword =
    lower.includes('every ') ||
    lower.includes('daily') ||
    lower.includes('weekly') ||
    lower.includes('monthly') ||
    lower.includes('hourly') ||
    lower.includes('at ') ||
    lower.includes('on ')

  // Explicit time patterns (e.g. "at 9am", "09:30")
  const timePattern = /\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/
  const twentyFourPattern = /\b(\d{1,2}):(\d{2})\b/
  const hasTime =
    timePattern.test(lower) ||
    twentyFourPattern.test(lower) ||
    /\b\d{4}-\d{1,2}-\d{1,2}\b/.test(lower) // simple ISO date

  // If either we see clear schedule words or explicit time/date, treat as schedule
  if (hasScheduleKeyword && hasTime) {
    return extractScheduleConfig(prompt)
  }
  if (hasScheduleKeyword && !hasTime) {
    // More conservative: require explicit schedule words even without time
    return extractScheduleConfig(prompt)
  }
  if (parsed?.parameters?.schedule) {
    return { type: 'schedule', config: parsed.parameters.schedule }
  }
  return DEFAULT_TRIGGER
}

function chooseAppFromText(text = '', apps = []) {
  const lower = text.toLowerCase()
  let bestMatch = null

  for (const app of apps) {
    const appKey = app.key
    const aliases = APP_ALIASES[appKey] || []
    const haystack = [app.name, app.description, app.category, ...aliases].join(' ').toLowerCase()
    const score = aliases.reduce((sum, alias) => sum + (lower.includes(alias) ? 2 : 0), 0)
      + (lower.includes(appKey.replace('_', ' ')) ? 3 : 0)
      + (lower.includes((app.name || '').toLowerCase()) ? 3 : 0)

    if (!bestMatch || score > bestMatch.score) {
      bestMatch = { appKey, score, haystack }
    }
  }

  if (bestMatch?.score > 0) return bestMatch.appKey
  return null
}

function chooseAction(appKey, text = '') {
  const variants = APP_ACTIONS[appKey]
  if (!variants) return ''

  const lower = text.toLowerCase()
  if (appKey === 'gmail') {
    if (
      lower.includes('draft') ||
      lower.includes('compose') ||
      lower.includes('write an email') ||
      lower.includes('write a mail')
    ) return variants.draft
    if (lower.includes('send') || lower.includes('email')) return variants.default
    if (lower.includes('draft')) return variants.draft
    if (lower.includes('find') || lower.includes('search')) return variants.search
  }
  if (appKey === 'resume_screener') {
    return variants.default
  }
  if (appKey === 'slack' && (lower.includes('dm') || lower.includes('direct message'))) {
    return variants.direct
  }
  if (appKey === 'google_sheets') {
    if (
      lower.includes('create google sheet') ||
      lower.includes('create google sheets') ||
      lower.includes('create spreadsheet') ||
      lower.includes('make a spreadsheet') ||
      lower.includes('new spreadsheet')
    ) return variants.create
    if (lower.includes('lookup') || lower.includes('find')) return variants.search
    if (lower.includes('update')) return variants.update
  }
  if (appKey === 'notion') {
    if (lower.includes('append')) return variants.append
    if (lower.includes('update')) return variants.update
  }
  if (appKey === 'airtable') {
    if (lower.includes('find') || lower.includes('lookup') || lower.includes('search')) return variants.search
    if (lower.includes('update')) return variants.update
  }
  if (appKey === 'webhooks' && (lower.includes('get') || lower.includes('fetch'))) {
    return variants.fetch
  }
  if (appKey === 'formatter') {
    if (lower.includes('json')) return variants.json
    if (lower.includes('date') || lower.includes('time')) return variants.dates
    if (lower.includes('score') || lower.includes('number')) return variants.numbers
  }
  if (appKey === 'github' && lower.includes('comment')) return variants.comment
  if (appKey === 'trello') {
    if (lower.includes('move')) return variants.move
    if (lower.includes('comment')) return variants.comment
  }
  return variants.default
}

function cleanSentence(text = '') {
  return text.replace(/\s+/g, ' ').replace(/^["'\s]+|["'\s]+$/g, '').trim()
}

function extractQuotedValue(task, keyword) {
  const patterns = [
    new RegExp(`${keyword}\\s*[:=-]?\\s*["“]([^"”]+)["”]`, 'i'),
    new RegExp(`${keyword}\\s*[:=-]?\\s*'([^']+)'`, 'i'),
  ]

  for (const pattern of patterns) {
    const match = task.match(pattern)
    if (match?.[1]) return cleanSentence(match[1])
  }

  return ''
}

function extractRecipient(task) {
  const emailMatch = task.match(/\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b/)
  if (emailMatch) return emailMatch[0]

  const namedRecipient = task.match(/\bto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b/)
  if (namedRecipient?.[1]) return namedRecipient[1]

  const genericRecipient = task.match(/\bto\s+the\s+([a-z][a-z\s]+?)(?:\s+(?:with|about|regarding|subject|body|saying)\b|$)/i)
  if (genericRecipient?.[1]) return `the ${cleanSentence(genericRecipient[1])}`

  return '{{trigger.email}}'
}

function inferEmailSubject(task) {
  const explicit =
    extractQuotedValue(task, 'subject') ||
    extractQuotedValue(task, 'title') ||
    extractQuotedValue(task, 'topic')
  if (explicit) return explicit

  const aboutMatch = task.match(/\b(?:about|regarding|for)\s+(.+?)(?:\s+(?:and|with|to|body|message)\b|$)/i)
  if (aboutMatch?.[1]) {
    return cleanSentence(aboutMatch[1])
      .split(' ')
      .slice(0, 8)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  return `${slugifyName(task)} Update`
}

function inferEmailBody(task, subject, recipient) {
  const explicit =
    extractQuotedValue(task, 'body') ||
    extractQuotedValue(task, 'message') ||
    extractQuotedValue(task, 'content') ||
    extractQuotedValue(task, 'saying')
  if (explicit) return explicit

  const purposeMatch = task.match(/\b(?:about|regarding|for)\s+(.+?)(?:\s+(?:and|with|to|subject|body)\b|$)/i)
  const purpose = cleanSentence(purposeMatch?.[1] || task)
  const greeting = recipient && !recipient.includes('@') && recipient !== '{{trigger.email}}'
    ? `Hi ${recipient},`
    : 'Hello,'

  if (/follow[\s-]?up/i.test(task)) {
    return `${greeting}\n\nI wanted to follow up regarding ${purpose || subject}. Please let me know if you need anything else from me.\n\nBest regards,`
  }
  if (/thank/i.test(task)) {
    return `${greeting}\n\nThank you for your time and support regarding ${purpose || subject}. I really appreciate it.\n\nBest regards,`
  }
  if (/reminder/i.test(task)) {
    return `${greeting}\n\nThis is a quick reminder about ${purpose || subject}. Please review it when you have a moment.\n\nBest regards,`
  }

  return `${greeting}\n\nI’m reaching out regarding ${purpose || subject}. Please review the details and let me know the next steps.\n\nBest regards,`
}

function inferEmailDraft(task) {
  const recipient = extractRecipient(task)
  const subject = inferEmailSubject(task)
  const body = inferEmailBody(task, subject, recipient)

  return {
    to: recipient,
    subject,
    body,
  }
}

function findKeywordIndex(lower, keywords = []) {
  const indexes = keywords
    .map(keyword => lower.indexOf(keyword))
    .filter(index => index >= 0)
  return indexes.length > 0 ? Math.min(...indexes) : Number.POSITIVE_INFINITY
}

function inferSequenceFromPrompt(task = '', apps = []) {
  const lower = task.toLowerCase()
  const candidates = [
    { app: 'google_sheets', keywords: ['google sheet', 'google sheets', 'spreadsheet', 'sheet', 'excel'] },
    { app: 'airtable', keywords: ['airtable', 'crm', 'database', 'table', 'record'] },
    { app: 'notion', keywords: ['notion', 'doc', 'document', 'page', 'wiki', 'knowledge base'] },
    { app: 'github', keywords: ['github', 'issue', 'pull request', 'repo', 'comment on issue'] },
    { app: 'trello', keywords: ['trello', 'board', 'card', 'task'] },
    { app: 'webhooks', keywords: ['webhook', 'api', 'endpoint', 'http request'] },
    { app: 'formatter', keywords: ['analyze', 'format', 'transform', 'clean', 'summarize', 'score', 'parse'] },
    { app: 'filter', keywords: ['only if', 'if approved', 'if qualified', 'condition', 'filter'] },
    { app: 'gmail', keywords: ['gmail', 'email', 'mail', 'draft', 'send email', 'mail it'] },
    { app: 'slack', keywords: ['slack', 'notify', 'notification', 'message', 'alert', 'post to channel'] },
  ]

  const scored = candidates
    .filter(candidate => apps.some(app => app.key === candidate.app))
    .map(candidate => ({
      app: candidate.app,
      index: findKeywordIndex(lower, candidate.keywords),
    }))
    .filter(candidate => candidate.index !== Number.POSITIVE_INFINITY)
    .sort((a, b) => a.index - b.index)

  const orderedApps = []
  for (const candidate of scored) {
    if (!orderedApps.includes(candidate.app)) orderedApps.push(candidate.app)
  }

  if (
    (lower.includes('mail it') || lower.includes('email it') || lower.includes('send it by email')) &&
    !orderedApps.includes('gmail') &&
    apps.some(app => app.key === 'gmail')
  ) {
    orderedApps.push('gmail')
  }

  if (
    (lower.includes('notify in slack') || lower.includes('send to slack') || lower.includes('post in slack')) &&
    !orderedApps.includes('slack') &&
    apps.some(app => app.key === 'slack')
  ) {
    orderedApps.push('slack')
  }

  return orderedApps
}

function buildInputMap(appKey, action, task, index, previousStep = null) {
  const reference = previousStep ? `{{${previousStep.output_key}.*}}` : '{{trigger.payload}}'
  const baseTitle = slugifyName(task)

  if (appKey === 'gmail') {
    const draft = inferEmailDraft(task)
    const previousLink = previousStep?.app_key === 'google_sheets'
      ? `{{${previousStep.output_key}.spreadsheet_url}}`
      : previousStep?.app_key === 'github'
        ? `{{${previousStep.output_key}.url}}`
        : previousStep?.app_key === 'trello'
          ? `{{${previousStep.output_key}.url}}`
          : reference
    const contextualBody = previousStep
      ? `${draft.body}\n\nReference: ${previousLink}`
      : `${draft.body}\n\nContext: ${reference}`
    return {
      to: draft.to,
      subject: draft.subject,
      body: contextualBody,
    }
  }
  if (appKey === 'slack') {
    return {
      channel: '#automation',
      text: `Workflow update for "${task}"\n\nContext: ${reference}`,
    }
  }
  if (appKey === 'google_sheets') {
    if (action === 'create_spreadsheet') {
      return {
        title: `${baseTitle} Sheet`,
        sheet_name: 'Sheet1',
      }
    }
    return {
      spreadsheet_id: previousStep?.app_key === 'google_sheets'
        ? `{{${previousStep.output_key}.spreadsheet_id}}`
        : '',
      sheet_name: 'Sheet1',
      values: `[\"${baseTitle}\", \"${reference}\"]`,
    }
  }
  if (appKey === 'notion') {
    return {
      parent_id: '',
      title: baseTitle,
      content: `Workflow generated from AI request:\n\n${task}\n\nContext: ${reference}`,
    }
  }
  if (appKey === 'airtable') {
    return {
      base_id: '',
      table_name: 'Tasks',
      fields: `{"name":"${baseTitle}","source":"${reference}"}`,
    }
  }
  if (appKey === 'webhooks') {
    return {
      url: '',
      payload: `{"task":"${task}","context":"${reference}"}`,
    }
  }
  if (appKey === 'formatter') {
    if (action === 'numbers') {
      return { operation: 'format_currency', value_a: '0', options: '{}' }
    }
    if (action === 'date_time') {
      return { operation: 'now', format: '%Y-%m-%d %H:%M', options: '{}' }
    }
    if (action === 'json') {
      return { operation: 'stringify', input: reference, options: '{}' }
    }
    return { operation: 'trim', input: task, options: '{}' }
  }
  if (appKey === 'filter') {
    return {
      conditions: `[{"field":"${reference}","operator":"exists","value":true}]`,
    }
  }
  if (appKey === 'github') {
    return {
      owner: '',
      repo: '',
      title: baseTitle,
      body: `Created from AI workflow request:\n\n${task}`,
    }
  }
  if (appKey === 'trello') {
    return {
      board_id: '',
      list_name: 'To Do',
      name: baseTitle,
      description: task,
    }
  }
  if (appKey === 'resume_screener') {
    return {
      resume_text: '',
      job_title: '',
      job_description: '',
    }
  }
  return {}
}

function findAppKey(toolName = '', apps = [], task = '') {
  const normalizedTool = toolName.toLowerCase().trim()
  if (apps.some(app => app.key === normalizedTool)) return normalizedTool
  const direct = TOOL_TO_APP[normalizedTool]
  if (direct && apps.some(app => app.key === direct)) return direct
  const fuzzy = chooseAppFromText(`${toolName} ${task}`, apps)
  if (fuzzy) return fuzzy
  if (apps.some(app => app.key === 'formatter')) return 'formatter'
  return apps[0]?.key || ''
}

function buildSteps(sequence = [], task = '', apps = []) {
  return sequence
    .map((toolName, index) => {
      const app_key = findAppKey(toolName, apps, task)
      if (!app_key || SPECIAL_APPS.has(app_key)) return null
      const action = chooseAction(app_key, `${toolName} ${task}`)
      const previousStep = index > 0 ? sequence.slice(0, index)
        .map((prevTool, prevIndex) => {
          const prevAppKey = findAppKey(prevTool, apps, task)
          return prevAppKey ? { app_key: prevAppKey, output_key: `step${prevIndex + 1}` } : null
        })
        .filter(Boolean)
        .slice(-1)[0] : null
      return {
        app_key,
        action,
        connection_id: '',
        input_map: buildInputMap(app_key, action, task, index, previousStep),
        output_key: `step${index + 1}`,
        halt_on_error: true,
        conditions: [],
      }
    })
    .filter(Boolean)
}

function deriveSequence(config = {}, parsed = {}, task = '', apps = []) {
  const explicitSequence = config?.tool_sequence || config?.execution_plan?.map(step => step.tool) || []
  if (explicitSequence.length > 0) return explicitSequence

  const selectedTools = config?.tools || config?.selected_tools || []
  if (selectedTools.length > 0) {
    return selectedTools.map(tool => tool.tool_name || tool.name).filter(Boolean)
  }
  return inferSequenceFromPrompt(task, apps)
}

export function normalizeAIResult(raw = {}) {
  const parsed = raw?.parsed || {}
  const config = raw?.agent_config || raw?.configuration || {}
  const task = config?.task || parsed?.intent || raw?.voice_input || ''
  return {
    task,
    parsed,
    config,
    confidence: config?.confidence ?? parsed?.confidence ?? raw?.confidence ?? 0,
    department: config?.department || parsed?.department || 'general',
  }
}

export function createWorkflowDraft(raw = {}, apps = [], promptFallback = '') {
  const normalized = normalizeAIResult(raw)
  const task = normalized.task || promptFallback
  const sequence = deriveSequence(normalized.config, normalized.parsed, task, apps)
  const trigger = inferTrigger(task, normalized.parsed)
  const steps = buildSteps(sequence, task, apps)
  const promptApp = chooseAppFromText(task, apps)

  if (steps.length === 0 && promptApp) {
    const action = chooseAction(promptApp, task)
    steps.push({
      app_key: promptApp,
      action,
      connection_id: '',
      input_map: buildInputMap(promptApp, action, task, 0),
      output_key: 'step1',
      halt_on_error: true,
      conditions: [],
    })
  }

  return {
    id: null,
    name: slugifyName(task),
    description: task,
    trigger_config: trigger,
    steps,
    status: 'draft',
    aiDraft: {
      task,
      department: normalized.department,
      confidence: normalized.confidence,
      sequence,
      reasoning: normalized.config?.reasoning || '',
    },
  }
}

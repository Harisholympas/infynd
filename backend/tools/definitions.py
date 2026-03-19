"""Department-specific tool definitions for different teams"""

SALES_TOOLS = {
    "crm_query": {
        "name": "CRM Query",
        "description": "Query customer data from CRM (Salesforce, HubSpot)",
        "params": ["customer_id", "query_type", "fields"],
        "returns": ["customer_data", "interactions", "deals"]
    },
    "lead_scorer": {
        "name": "Lead Scorer",
        "description": "Score leads based on engagement and fit",
        "params": ["lead_id", "scoring_model"],
        "returns": ["score", "recommendation", "next_steps"]
    },
    "pipeline_analyzer": {
        "name": "Sales Pipeline Analyzer",
        "description": "Analyze sales pipeline and forecast revenue",
        "params": ["time_period", "team_id"],
        "returns": ["forecast", "bottlenecks", "recommendations"]
    },
    "email_campaign": {
        "name": "Email Campaign Manager",
        "description": "Create and send targeted email campaigns",
        "params": ["recipient_list", "template", "variables"],
        "returns": ["campaign_id", "scheduled_time", "status"]
    },
    "deal_tracker": {
        "name": "Deal Tracker",
        "description": "Track deal progress and send follow-up reminders",
        "params": ["deal_id", "action"],
        "returns": ["deal_status", "next_milestone", "alert"]
    }
}

HR_TOOLS = {
    "resume_screener": {
        "name": "Resume Screener",
        "description": "Screen resumes against role requirements and rank the best candidates",
        "params": ["resume_text", "job_description", "must_have_skills", "experience_level"],
        "returns": ["match_score", "shortlist_decision", "skill_match", "missing_requirements", "summary"]
    },
    "employee_database": {
        "name": "Employee Database",
        "description": "Access employee records, skills, performance data",
        "params": ["employee_id", "query_type", "filters"],
        "returns": ["employee_info", "skills", "performance_scores"]
    },
    "job_matcher": {
        "name": "Job Matcher",
        "description": "Match employees to internal job openings",
        "params": ["employee_id", "skill_requirements"],
        "returns": ["matched_jobs", "skill_gaps", "training_needs"]
    },
    "payroll_processor": {
        "name": "Payroll Processor",
        "description": "Calculate payroll, deductions, and benefits",
        "params": ["employee_id", "period", "adjustments"],
        "returns": ["gross_pay", "deductions", "net_pay"]
    },
    "training_scheduler": {
        "name": "Training Scheduler",
        "description": "Schedule and track employee training programs",
        "params": ["employee_id", "training_type", "dates"],
        "returns": ["schedule", "completion_tracking", "certificates"]
    },
    "performance_evaluator": {
        "name": "Performance Evaluator",
        "description": "Generate performance reviews and feedback",
        "params": ["employee_id", "period", "metrics"],
        "returns": ["review", "ratings", "recommendations"]
    },
    "onboarding_manager": {
        "name": "Onboarding Manager",
        "description": "Manage new employee onboarding process",
        "params": ["new_hire_id", "department", "start_date"],
        "returns": ["onboarding_plan", "tasks", "milestones"]
    }
}

MARKETING_TOOLS = {
    "campaign_builder": {
        "name": "Campaign Builder",
        "description": "Design and launch marketing campaigns across channels",
        "params": ["campaign_type", "target_audience", "channels"],
        "returns": ["campaign_id", "content", "schedule"]
    },
    "content_generator": {
        "name": "Content Generator",
        "description": "Generate marketing copy, emails, social posts",
        "params": ["content_type", "topic", "style", "length"],
        "returns": ["content", "variations", "seo_score"]
    },
    "analytics_tracker": {
        "name": "Analytics Tracker",
        "description": "Track campaign performance and ROI",
        "params": ["campaign_id", "metric_type", "date_range"],
        "returns": ["metrics", "trends", "insights"]
    },
    "audience_segmenter": {
        "name": "Audience Segmenter",
        "description": "Segment audiences for targeted messaging",
        "params": ["dataset", "segmentation_type", "criteria"],
        "returns": ["segments", "sizes", "characteristics"]
    },
    "social_manager": {
        "name": "Social Media Manager",
        "description": "Auto-post to social media and manage engagement",
        "params": ["platforms", "content", "schedule"],
        "returns": ["post_ids", "scheduled_time", "engagement_forecast"]
    },
    "seo_optimizer": {
        "name": "SEO Optimizer",
        "description": "Optimize content for search engines",
        "params": ["content", "target_keywords", "competitors"],
        "returns": ["optimized_content", "keywords", "improvement_score"]
    }
}

FINANCE_TOOLS = {
    "invoice_generator": {
        "name": "Invoice Generator",
        "description": "Generate and send invoices automatically",
        "params": ["client_id", "items", "terms"],
        "returns": ["invoice_id", "pdf_url", "sent_status"]
    },
    "expense_analyzer": {
        "name": "Expense Analyzer",
        "description": "Analyze expenses and identify cost savings",
        "params": ["period", "department", "categories"],
        "returns": ["total_expenses", "breakdown", "savings_opportunities"]
    },
    "budget_planner": {
        "name": "Budget Planner",
        "description": "Create and manage department budgets",
        "params": ["department", "period", "historical_data"],
        "returns": ["budget", "allocations", "forecast"]
    },
    "financial_reporter": {
        "name": "Financial Reporter",
        "description": "Generate financial reports (P&L, balance sheet)",
        "params": ["report_type", "period", "currency"],
        "returns": ["report", "charts", "key_metrics"]
    },
    "payment_processor": {
        "name": "Payment Processor",
        "description": "Process vendor payments and manage cash flow",
        "params": ["invoice_id", "payment_method", "amount"],
        "returns": ["transaction_id", "confirmation", "status"]
    },
    "tax_calculator": {
        "name": "Tax Calculator",
        "description": "Calculate taxes and generate tax reports",
        "params": ["income", "deductions", "jurisdiction"],
        "returns": ["tax_amount", "breakdown", "filing_status"]
    }
}

SUPPORT_TOOLS = {
    "ticket_manager": {
        "name": "Ticket Manager",
        "description": "Create, manage, and resolve support tickets",
        "params": ["customer_id", "issue_type", "priority"],
        "returns": ["ticket_id", "status", "assigned_agent"]
    },
    "knowledge_base_search": {
        "name": "Knowledge Base Search",
        "description": "Search knowledge base for solutions",
        "params": ["query", "category", "language"],
        "returns": ["articles", "relevance_score", "solutions"]
    },
    "chatbot_integrator": {
        "name": "Chatbot Integrator",
        "description": "Deploy AI chatbot for instant support",
        "params": ["questions", "context", "language"],
        "returns": ["response", "confidence", "escalation_flag"]
    },
    "customer_feedback": {
        "name": "Customer Feedback Analyzer",
        "description": "Analyze customer feedback and sentiment",
        "params": ["feedback_text", "source"],
        "returns": ["sentiment", "topics", "actions"]
    },
    "issue_predictor": {
        "name": "Issue Predictor",
        "description": "Predict customer issues before they occur",
        "params": ["customer_id", "product_id"],
        "returns": ["predicted_issues", "probability", "recommendations"]
    },
    "response_generator": {
        "name": "Response Generator",
        "description": "Generate AI-powered support responses",
        "params": ["ticket_id", "tone", "include_resources"],
        "returns": ["response", "suggestions", "resolution_time"]
    }
}

# Department to tools mapping
DEPARTMENT_TOOLS = {
    "sales": SALES_TOOLS,
    "hr": HR_TOOLS,
    "marketing": MARKETING_TOOLS,
    "finance": FINANCE_TOOLS,
    "support": SUPPORT_TOOLS,
}

# Generic tools available to all
COMMON_TOOLS = {
    "email_sender": {
        "name": "Email Sender",
        "description": "Send professional emails with attachments",
        "params": ["to", "subject", "body", "attachments"],
        "returns": ["message_id", "sent_time", "status"]
    },
    "file_manager": {
        "name": "File Manager",
        "description": "Create, read, update, delete files",
        "params": ["action", "file_path", "content"],
        "returns": ["file_info", "location", "size"]
    },
    "calendar_manager": {
        "name": "Calendar Manager",
        "description": "Schedule meetings and manage calendar",
        "params": ["action", "title", "attendees", "time"],
        "returns": ["event_id", "confirmation", "reminders"]
    },
    "slack_notifier": {
        "name": "Slack Notifier",
        "description": "Send notifications to Slack channels",
        "params": ["channel", "message", "attachments"],
        "returns": ["message_id", "sent_time", "reactions"]
    },
    "data_analyzer": {
        "name": "Data Analyzer",
        "description": "Analyze data and generate insights",
        "params": ["data", "analysis_type", "metrics"],
        "returns": ["analysis", "charts", "insights"]
    },
    "report_generator": {
        "name": "Report Generator",
        "description": "Generate professional reports (PDF, Excel)",
        "params": ["data", "template", "format"],
        "returns": ["report_id", "file_url", "generated_at"]
    },
    "spreadsheet_processor": {
        "name": "Spreadsheet Processor",
        "description": "Process and analyze spreadsheet data",
        "params": ["file_path", "sheet_name", "operations"],
        "returns": ["data", "summary", "export_url"]
    },
    "database_query": {
        "name": "Database Query",
        "description": "Execute queries on company databases",
        "params": ["query", "database", "params"],
        "returns": ["results", "row_count", "execution_time"]
    },
    "web_scraper": {
        "name": "Web Scraper",
        "description": "Scrape data from websites",
        "params": ["url", "selectors", "format"],
        "returns": ["data", "raw_html", "parsed_json"]
    },
    "notification_sender": {
        "name": "Notification Sender",
        "description": "Send notifications via multiple channels",
        "params": ["channels", "message", "priority"],
        "returns": ["notification_id", "sent_to", "status"]
    },
    "task_tracker": {
        "name": "Task Tracker",
        "description": "Create and track tasks and projects",
        "params": ["task_name", "assignee", "deadline"],
        "returns": ["task_id", "assigned_at", "tracking_url"]
    }
}

def get_tools_for_department(department: str) -> dict:
    """Get all tools available for a department"""
    dept_lower = department.lower()
    return {
        **COMMON_TOOLS,
        **(DEPARTMENT_TOOLS.get(dept_lower, {}))
    }

def get_all_tools() -> dict:
    """Get all available tools across all departments"""
    all_tools = {**COMMON_TOOLS}
    for dept_tools in DEPARTMENT_TOOLS.values():
        all_tools.update(dept_tools)
    return all_tools

def get_recommended_tools(department: str, task_type: str) -> list:
    """Get recommended tools for a specific task"""
    recommendations = {
        ("sales", "lead_generation"): ["lead_scorer", "email_campaign", "crm_query"],
        ("sales", "deal_management"): ["deal_tracker", "pipeline_analyzer", "crm_query"],
        ("hr", "recruitment"): ["resume_screener", "job_matcher", "employee_database", "email_sender"],
        ("hr", "payroll"): ["payroll_processor", "spreadsheet_processor", "database_query"],
        ("marketing", "campaign"): ["campaign_builder", "content_generator", "social_manager"],
        ("marketing", "analysis"): ["analytics_tracker", "audience_segmenter", "data_analyzer"],
        ("finance", "invoicing"): ["invoice_generator", "email_sender", "payment_processor"],
        ("finance", "reporting"): ["financial_reporter", "expense_analyzer", "budget_planner"],
        ("support", "issue_resolution"): ["ticket_manager", "knowledge_base_search", "response_generator"],
        ("support", "customer_service"): ["chatbot_integrator", "customer_feedback", "issue_predictor"],
    }
    
    key = (department.lower(), task_type.lower())
    return recommendations.get(key, [])

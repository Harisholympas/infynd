"""Auto-Configuration API Routes - Voice commands and auto-tool configuration"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from agents.auto_configure import AutoToolConfigurator
from agents.voice_processor import VoiceProcessor

router = APIRouter(prefix="/api/auto-config", tags=["auto_config"])

# Initialize components
configurator = AutoToolConfigurator()
voice_processor = VoiceProcessor()


@router.post("/task-analysis")
async def analyze_task_for_config(
    task: str,
    department: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Analyze a task and auto-generate tool configuration"""
    try:
        config = await configurator.analyze_task(task, department, context)
        return {
            "status": "success",
            "task": task,
            "department": department,
            "configuration": config
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/voice-command")
async def process_voice_command(
    voice_text: str,
    auto_execute: bool = False
) -> Dict[str, Any]:
    """Process voice command and optionally auto-configure agent"""
    try:
        # Parse voice command
        parsed = await configurator.parse_voice_command(voice_text)
        
        response = {
            "status": "success",
            "voice_input": voice_text,
            "parsed": parsed,
            "confidence": parsed.get('confidence', 0),
            "requires_approval": parsed.get('requires_human_approval', True)
        }
        
        # Auto-configure if requested and confidence is high
        if auto_execute and parsed.get('confidence', 0) > 0.7 and not parsed.get('requires_human_approval'):
            agent_config = await configurator.configure_agent_for_task(
                parsed['intent'],
                parsed['department']
            )
            response['agent_config'] = agent_config
            response['auto_configured'] = True
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



class VoiceTranscribeRequest(BaseModel):
    audio_base64: str
    language: str = "en"
    audio_format: str = "webm"


@router.post("/voice-transcribe")
async def transcribe_audio_command(
    data: VoiceTranscribeRequest,
) -> Dict[str, Any]:
    """Transcribe audio to text and process as voice command"""
    try:
        # Decode base64 audio
        import base64
        audio_bytes = base64.b64decode(data.audio_base64)
        
        # Transcribe using Whisper
        voice_processor.load_model()
        result = await voice_processor.transcribe_audio(
            audio_bytes,
            data.language,
            audio_format=data.audio_format,
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Transcription failed'))
        
        # Process as voice command
        voice_text = result['text']
        parsed = await configurator.parse_voice_command(voice_text)
        
        return {
            "status": "success",
            "transcribed_text": voice_text,
            "parsed": parsed,
            "confidence": parsed.get('confidence', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/configure-agent")
async def auto_configure_agent(
    task: str,
    department: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Full agent auto-configuration for a task"""
    try:
        agent_config = await configurator.configure_agent_for_task(task, department, user_id)
        
        # Validate configuration
        valid, issues = await configurator.validate_configuration(agent_config)
        
        return {
            "status": "success",
            "agent_config": agent_config,
            "valid": valid,
            "issues": issues,
            "ready_for_execution": valid and agent_config.get('confidence', 0) > 0.7
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/optimize-sequence")
async def optimize_tool_sequence(
    tools: list,
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Optimize the execution sequence of tools"""
    try:
        optimized = await configurator.optimize_tool_sequence(tools, constraints)
        
        return {
            "status": "success",
            "original_sequence": tools,
            "optimized_sequence": optimized,
            "changes": tools != optimized
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-config")
async def validate_agent_config(
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate an agent configuration"""
    try:
        valid, issues = await configurator.validate_configuration(config)
        
        return {
            "status": "success",
            "valid": valid,
            "issues": issues,
            "config_id": config.get('agent_id', 'unknown')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/suggest-improvements")
async def suggest_config_improvements(
    config: Dict[str, Any],
    execution_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Get improvement suggestions based on execution results"""
    try:
        suggestions = await configurator.suggest_improvements(config, execution_result)
        
        return {
            "status": "success",
            "suggestions": suggestions,
            "has_improvements": any(suggestions.values())
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/infer-department")
async def infer_department_from_task(
    task: str
) -> Dict[str, Any]:
    """Infer the department from a task description"""
    try:
        # Simple keyword matching
        task_lower = task.lower()
        
        dept_keywords = {
            "sales": ["sales", "lead", "deal", "pipeline", "customer", "prospect"],
            "hr": ["employee", "hiring", "recruitment", "payroll", "onboarding", "performance"],
            "marketing": ["marketing", "campaign", "content", "social", "email", "brand"],
            "finance": ["finance", "budget", "invoice", "expense", "payment", "tax"],
            "support": ["support", "ticket", "customer service", "issue", "feedback", "help"]
        }
        
        detected_depts = {}
        for dept, keywords in dept_keywords.items():
            matches = sum(1 for kw in keywords if kw in task_lower)
            if matches > 0:
                detected_depts[dept] = matches
        
        # Get highest match
        if detected_depts:
            top_dept = max(detected_depts, key=detected_depts.get)
            confidence = detected_depts[top_dept] / len(dept_keywords.get(top_dept, []))
        else:
            top_dept = "general"
            confidence = 0.0
        
        return {
            "status": "success",
            "task": task,
            "inferred_department": top_dept,
            "confidence": min(confidence, 1.0),
            "all_matches": detected_depts
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/supported-departments")
async def get_supported_departments() -> Dict[str, Any]:
    """Get list of supported departments"""
    try:
        from tools.definitions import DEPARTMENT_TOOLS
        
        departments = list(DEPARTMENT_TOOLS.keys())
        
        return {
            "status": "success",
            "supported_departments": departments,
            "count": len(departments)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

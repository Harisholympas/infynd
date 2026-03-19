"""Auto-Tool Configuration Engine - Automatically selects and configures tools for tasks"""
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from core.llm import llm_client
from tools.definitions import (
    get_tools_for_department, get_recommended_tools, get_all_tools
)

logger = logging.getLogger(__name__)

AUTO_CONFIG_PROMPT = """You are an AI agent configuration expert. Based on the task requirements, 
automatically configure the optimal set of tools needed.

Task: {task}
Department: {department}
Available Tools: {available_tools}
Previous Successful Patterns: {patterns}

Generate a tool configuration in JSON format:
{{
  "selected_tools": [
    {{"tool_name": "tool1", "priority": "high", "config": {{"param": "value"}}}},
    {{"tool_name": "tool2", "priority": "medium", "config": {{}}}}
  ],
  "tool_sequence": ["tool1", "tool2"],
  "fallback_tools": ["alt_tool1"],
  "required_connections": ["connection_1"],
  "estimated_time_minutes": 5,
  "confidence": 0.95,
  "reasoning": "Brief explanation of tool selection"
}}

Consider:
1. Task complexity and required outcomes
2. Available tools and their capabilities
3. Tool dependencies and sequence
4. Performance and efficiency
5. Fallback options for reliability"""

VOICE_COMMAND_PARSE_PROMPT = """Extract the structured information from this voice command:

Voice Command: "{voice_input}"

Return JSON:
{{
  "intent": "clear intent of what to do",
  "department": "sales|hr|marketing|finance|support|general",
  "task_type": "lead_generation|reporting|processing|analysis|communication",
  "parameters": {{"key": "value"}},
  "priority": "low|normal|high",
  "requires_human_approval": boolean,
  "confidence": 0.0-1.0
}}"""


class AutoToolConfigurator:
    """Automatically selects and configures tools for a given task"""
    
    async def analyze_task(self, task_description: str, department: str, 
                          user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze task and recommend tool configuration"""
        
        # Get available tools for department
        available_tools = get_tools_for_department(department)
        tool_names = list(available_tools.keys())
        
        # Get recommended tools
        task_type = self._infer_task_type(task_description)
        recommended = get_recommended_tools(department, task_type)
        
        # Get patterns if available (from persistent memory)
        patterns = []
        if user_context and 'agent_id' in user_context:
            # Would fetch from persistent memory in real implementation
            patterns = []
        
        # Call LLM for auto-configuration
        prompt = AUTO_CONFIG_PROMPT.format(
            task=task_description,
            department=department,
            available_tools=json.dumps(tool_names[:10]),  # Limit for token count
            patterns=json.dumps(patterns)
        )
        
        try:
            response = await llm_client.generate_text(prompt, max_tokens=1000)
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group())
                config['available_tools'] = available_tools
                config['recommended_tools'] = recommended
                return config
        except Exception as e:
            logger.error(f"Error in auto-configuration: {e}")
        
        # Fallback configuration
        return {
            "selected_tools": [
                {"tool_name": tool, "priority": "high", "config": {}}
                for tool in recommended[:3]
            ],
            "tool_sequence": recommended[:3],
            "fallback_tools": recommended[3:],
            "confidence": 0.7,
            "reasoning": "Fallback configuration based on department and task type"
        }
    
    async def parse_voice_command(self, voice_text: str) -> Dict[str, Any]:
        """Parse voice command to extract intent and parameters"""
        
        prompt = VOICE_COMMAND_PARSE_PROMPT.format(voice_input=voice_text)
        
        try:
            response = await llm_client.generate_text(prompt, max_tokens=500)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
        except Exception as e:
            logger.error(f"Error parsing voice command: {e}")
        
        return {
            "intent": "unknown",
            "department": "general",
            "task_type": "unknown",
            "parameters": {},
            "priority": "normal",
            "requires_human_approval": True,
            "confidence": 0.0
        }
    
    async def configure_agent_for_task(self, task: str, department: str, 
                                      user_id: str = None) -> Dict[str, Any]:
        """Full agent auto-configuration for task execution"""
        
        # Analyze task
        task_analysis = await self.analyze_task(task, department)
        
        # Get tool definitions
        tools_config = {}
        for tool in task_analysis.get('selected_tools', []):
            tool_name = tool['tool_name']
            if tool_name in task_analysis['available_tools']:
                tools_config[tool_name] = task_analysis['available_tools'][tool_name]
        
        # Generate agent blueprint
        agent_config = {
            "agent_id": self._generate_id(),
            "task": task,
            "department": department,
            "tools": task_analysis.get('selected_tools', []),
            "tool_sequence": task_analysis.get('tool_sequence', []),
            "fallback_tools": task_analysis.get('fallback_tools', []),
            "required_connections": task_analysis.get('required_connections', []),
            "estimated_time_minutes": task_analysis.get('estimated_time_minutes', 10),
            "confidence": task_analysis.get('confidence', 0.7),
            "status": "configured",
            "execution_plan": self._generate_execution_plan(task_analysis),
            "parameters": {}
        }
        
        return agent_config
    
    def _infer_task_type(self, description: str) -> str:
        """Infer task type from description"""
        desc_lower = description.lower()
        
        type_keywords = {
            "lead_generation": ["lead", "prospect", "potential", "generate"],
            "recruitment": ["resume", "candidate", "applicant", "screening", "shortlist", "job description", "hiring"],
            "reporting": ["report", "summary", "analyze", "dashboard", "metrics"],
            "processing": ["process", "batch", "handle", "manage", "execute"],
            "analysis": ["analyze", "analyze", "breakdown", "understand", "insights"],
            "communication": ["email", "message", "notify", "send", "alert"],
        }
        
        for task_type, keywords in type_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                return task_type
        
        return "general"
    
    def _generate_execution_plan(self, config: Dict) -> List[Dict]:
        """Generate execution plan from configuration"""
        plan = []
        
        for i, tool_name in enumerate(config.get('tool_sequence', []), 1):
            plan.append({
                "step": i,
                "tool": tool_name,
                "inputs": {},
                "expected_output": "result",
                "error_handler": "fallback",
                "timeout_seconds": 60
            })
        
        return plan
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    async def optimize_tool_sequence(self, tools: List[str], 
                                    constraints: Dict = None) -> List[str]:
        """Optimize the execution sequence of tools"""
        
        dependencies = {
            "crm_query": [],
            "lead_scorer": ["crm_query"],
            "email_campaign": ["audience_segmenter"],
            "pipeline_analyzer": ["crm_query"],
            "report_generator": []
        }
        
        # Topological sort to determine optimal sequence
        optimized = []
        remaining = set(tools)
        
        while remaining:
            for tool in remaining:
                deps = dependencies.get(tool, [])
                if all(dep in optimized for dep in deps):
                    optimized.append(tool)
                    remaining.remove(tool)
                    break
            else:
                # If circular dependency, just add remaining
                optimized.extend(list(remaining))
                break
        
        return optimized
    
    async def validate_configuration(self, config: Dict) -> Tuple[bool, List[str]]:
        """Validate tool configuration for correctness"""
        issues = []
        
        # Check tool existence
        all_tools = get_all_tools()
        for tool in config.get('selected_tools', []):
            tool_name = tool.get('tool_name')
            if tool_name not in all_tools:
                issues.append(f"Tool '{tool_name}' not found")
        
        # Check required connections
        required_conn = config.get('required_connections', [])
        if required_conn:
            # In real implementation, would check if connections exist
            pass
        
        # Check sequence is not empty
        if not config.get('tool_sequence'):
            issues.append("Tool sequence cannot be empty")
        
        # Check confidence threshold
        if config.get('confidence', 0) < 0.3:
            issues.append("Confidence level too low for auto-execution")
        
        return len(issues) == 0, issues
    
    async def suggest_improvements(self, config: Dict, execution_result: Dict) -> Dict:
        """Suggest improvements based on execution results"""
        
        suggestions = {
            "efficiency_improvements": [],
            "tool_alternatives": [],
            "parameter_optimizations": [],
            "timing_improvements": []
        }
        
        if execution_result.get('execution_time', 0) > config.get('estimated_time_minutes', 10) * 60:
            suggestions['timing_improvements'].append(
                "Consider parallelizing certain tool calls if possible"
            )
        
        if not execution_result.get('success'):
            suggestions['tool_alternatives'].append(
                "Consider using fallback tools for more reliability"
            )
        
        return suggestions


# Singleton instance
_configurator = None

async def get_configurator() -> AutoToolConfigurator:
    """Get or create the auto-tool configurator"""
    global _configurator
    if _configurator is None:
        _configurator = AutoToolConfigurator()
    return _configurator

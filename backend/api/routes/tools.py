"""Tools API Routes - List, configure, and manage available tools for agents"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from tools.definitions import (
    get_tools_for_department, get_all_tools, get_recommended_tools,
    DEPARTMENT_TOOLS, COMMON_TOOLS
)

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/all")
async def get_all_available_tools() -> Dict[str, Any]:
    """Get all available tools across all departments"""
    try:
        all_tools = get_all_tools()
        return {
            "status": "success",
            "tools": all_tools,
            "total_count": len(all_tools),
            "categories": list(DEPARTMENT_TOOLS.keys()) + ["common"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/department/{department}")
async def get_department_tools(department: str) -> Dict[str, Any]:
    """Get tools available for a specific department"""
    try:
        dept_tools = get_tools_for_department(department)
        
        if not dept_tools:
            raise HTTPException(status_code=404, detail=f"Department '{department}' not found")
        
        return {
            "status": "success",
            "department": department,
            "tools": dept_tools,
            "total_count": len(dept_tools)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommended/{department}")
async def get_recommended_tools_for_task(
    department: str,
    task_type: str = None
) -> Dict[str, Any]:
    """Get recommended tools for a specific task"""
    try:
        if task_type:
            tools = get_recommended_tools(department, task_type)
            message = f"Recommended tools for {task_type} in {department}"
        else:
            # Get all department tools
            all_dept_tools = get_tools_for_department(department)
            tools = list(all_dept_tools.keys())[:5]  # Top 5 tools
            message = f"Popular tools for {department} department"
        
        return {
            "status": "success",
            "department": department,
            "task_type": task_type or "general",
            "recommended_tools": tools,
            "count": len(tools),
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search_tools(
    query: str,
    department: str = None
) -> Dict[str, Any]:
    """Search tools by name or description"""
    try:
        all_tools = get_all_tools()
        query_lower = query.lower()
        
        # Get all tools first
        search_pool = all_tools
        
        # Filter by department if specified
        if department:
            search_pool = get_tools_for_department(department)
        
        # Search
        results = {}
        for tool_name, tool_info in search_pool.items():
            name_match = query_lower in tool_name.lower()
            desc_match = query_lower in tool_info.get('description', '').lower()
            
            if name_match or desc_match:
                results[tool_name] = tool_info
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/details/{tool_name}")
async def get_tool_details(tool_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific tool"""
    try:
        all_tools = get_all_tools()
        
        if tool_name not in all_tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool_info = all_tools[tool_name]
        
        # Find which departments have this tool
        departments = []
        for dept_name, dept_tools in DEPARTMENT_TOOLS.items():
            if tool_name in dept_tools:
                departments.append(dept_name)
        
        # Add if it's a common tool
        if tool_name in COMMON_TOOLS:
            departments.append("common")
        
        return {
            "status": "success",
            "tool_name": tool_name,
            "tool_info": tool_info,
            "available_in_departments": departments,
            "is_common": tool_name in COMMON_TOOLS
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/configure")
async def configure_tool(
    tool_name: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate and prepare a tool configuration"""
    try:
        all_tools = get_all_tools()
        
        if tool_name not in all_tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool_def = all_tools[tool_name]
        
        # Validate required params
        required_params = tool_def.get('params', [])
        provided_params = list(config.keys())
        
        missing_params = [p for p in required_params if p not in provided_params]
        extra_params = [p for p in provided_params if p not in required_params]
        
        return {
            "status": "success",
            "tool_name": tool_name,
            "configured_params": config,
            "missing_params": missing_params,
            "extra_params": extra_params,
            "valid": len(missing_params) == 0,
            "warnings": [f"Missing required parameter: {p}" for p in missing_params]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/departments")
async def get_all_departments() -> Dict[str, Any]:
    """Get list of all departments"""
    try:
        departments = list(DEPARTMENT_TOOLS.keys())
        
        # Get tool count per department
        dept_stats = {}
        for dept in departments:
            tools = get_tools_for_department(dept)
            dept_stats[dept] = len(tools)
        
        return {
            "status": "success",
            "departments": departments,
            "department_stats": dept_stats,
            "total_departments": len(departments)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories")
async def get_tool_categories() -> Dict[str, Any]:
    """Get tool categories and grouping"""
    try:
        categories = {
            "department_specific": list(DEPARTMENT_TOOLS.keys()),
            "common": list(COMMON_TOOLS.keys()),
            "total_unique": len(get_all_tools())
        }
        
        return {
            "status": "success",
            "categories": categories,
            "total_tools": categories["total_unique"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-chain")
async def validate_tool_chain(
    tools: List[str],
    department: str = None
) -> Dict[str, Any]:
    """Validate a chain/sequence of tools can work together"""
    try:
        all_tools = get_all_tools()
        
        # Check all tools exist
        invalid_tools = [t for t in tools if t not in all_tools]
        if invalid_tools:
            return {
                "status": "invalid",
                "valid": False,
                "invalid_tools": invalid_tools,
                "message": f"Tools not found: {invalid_tools}"
            }
        
        # Check if all tools are compatible with department
        if department:
            dept_tools = get_tools_for_department(department)
            incompatible = [t for t in tools if t not in dept_tools and t not in COMMON_TOOLS]
            
            if incompatible:
                return {
                    "status": "warning",
                    "valid": True,
                    "incompatible_tools": incompatible,
                    "message": f"Some tools are not recommended for the {department} department"
                }
        
        return {
            "status": "success",
            "valid": True,
            "tools_count": len(tools),
            "message": "Tool chain is valid"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

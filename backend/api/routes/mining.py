"""Task pattern mining routes"""
from fastapi import APIRouter
from mining.pattern_miner import pattern_miner

router = APIRouter()


@router.get("/patterns")
async def get_patterns(min_frequency: int = 2, department: str = None):
    patterns = await pattern_miner.get_patterns(min_frequency, department)
    return {"patterns": patterns, "total": len(patterns)}


@router.get("/suggestions")
async def get_suggestions():
    suggestions = await pattern_miner.suggest_agents()
    return {"suggestions": suggestions}


@router.get("/stats")
async def get_mining_stats():
    return await pattern_miner.get_stats()

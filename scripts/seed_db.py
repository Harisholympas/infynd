"""Seed the database with sample agents and knowledge"""
import asyncio, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core.database import init_db, DB_PATH
from rag.pipeline import RAGPipeline
from memory.manager import MemoryManager
import aiosqlite
from datetime import datetime


async def seed():
    print("Initializing database...")
    await init_db()

    print("Seeding sample agents...")
    sample_path = Path(__file__).parent.parent / 'data' / 'agents' / 'sample_agents.json'
    if sample_path.exists():
        try:
            with open(sample_path) as f:
                agents = json.load(f)
            async with aiosqlite.connect(DB_PATH) as db:
                # Check if agents table exists
                cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
                table_exists = await cursor.fetchone()
                if table_exists:
                    for agent in agents:
                        existing = await db.execute("SELECT id FROM agents WHERE id = ?", (agent["id"],))
                        row = await existing.fetchone()
                        if not row:
                            await db.execute(
                                "INSERT INTO agents (id, name, department, role, description, blueprint, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                                (agent["id"], agent["name"], agent["department"], agent["role"],
                                 agent["description"], json.dumps(agent["blueprint"]), "active",
                                 datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
                            )
                            print(f"  Seeded: {agent['name']}")
                    await db.commit()
                else:
                    print("  Agents table not in schema, skipping")
        except Exception as e:
            print(f"  Error seeding agents: {e}")
    
    try:
        print("Initializing memory...")
        memory = MemoryManager()
        await memory.initialize()
    except Exception as e:
        print(f"  Memory init skipped: {e}")

    try:
        print("Initializing RAG...")
        rag = RAGPipeline()
        await rag.initialize()
        print(f"  Indexed documents")
    except Exception as e:
        print(f"  RAG init skipped: {e}")
    print("Done! Database seeded.")

if __name__ == "__main__":
    asyncio.run(seed())

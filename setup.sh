#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${BLUE}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║  AutoFlow — Workflow Automation Platform     ║"
echo "  ║  Zapier-equivalent, fully local & offline    ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

command -v python3 &>/dev/null || { echo -e "${RED}✗ Python 3 required${NC}"; exit 1; }
command -v node &>/dev/null    || { echo -e "${RED}✗ Node.js required${NC}"; exit 1; }
echo -e "${GREEN}✓ Python $(python3 --version 2>&1 | cut -d' ' -f2)${NC}"
echo -e "${GREEN}✓ Node $(node --version)${NC}"

echo -e "\n${BLUE}Installing backend dependencies...${NC}"
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Backend ready${NC}"

echo -e "\n${BLUE}Seeding demo data...${NC}"
cd ../scripts
python seed_workflows.py
echo -e "${GREEN}✓ Demo workflows seeded${NC}"

echo -e "\n${BLUE}Installing frontend dependencies...${NC}"
cd ../frontend
npm install --silent
echo -e "${GREEN}✓ Frontend ready${NC}"

echo -e "\n${GREEN}"
echo "  ╔════════════════════════════════════════════╗"
echo "  ║   Setup complete!                          ║"
echo "  ╠════════════════════════════════════════════╣"
echo "  ║  Start 2 terminals:                        ║"
echo "  ║                                            ║"
echo "  ║  Terminal 1 (Backend):                     ║"
echo "  ║    cd backend                              ║"
echo "  ║    source .venv/bin/activate               ║"
echo "  ║    uvicorn main:app --reload               ║"
echo "  ║                                            ║"
echo "  ║  Terminal 2 (Frontend):                    ║"
echo "  ║    cd frontend && npm run dev              ║"
echo "  ║                                            ║"
echo "  ║  Open: http://localhost:5173               ║"
echo "  ╚════════════════════════════════════════════╝"
echo -e "${NC}"

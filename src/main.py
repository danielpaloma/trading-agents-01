# src/main.py
import asyncio
import logging
from src.config import load_config
from src.agents.orchestrator import TradingOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def main() -> None:
    config = load_config()
    orchestrator = TradingOrchestrator(config)
    await orchestrator.start()

if __name__ == "__main__":
    asyncio.run(main())
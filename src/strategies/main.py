"""Independent trading session entry point."""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv
from ib_async import MarketOrder

from src.config import load_config
from src.state import TradingSessionState
from src.strategies import StrategyExecutor, StrategyFactory
from src.tools.ibkr_tools import IBKRClient
from src.tools.reporting import PositionTracker, log_final_report

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def create_contract(config, client: IBKRClient):
    """Create instrument contract based on configuration."""
    instr = config.instrument
    if instr.instrument_type == "FOREX":
        return client.create_forex_contract(instr.symbol, instr.exchange)
    elif instr.instrument_type == "CFD":
        return client.create_cfd_contract(instr.symbol, instr.currency, instr.exchange)
    elif instr.instrument_type == "STOCK":
        return client.create_stock_contract(instr.symbol, instr.currency, instr.exchange)
    else:
        raise ValueError(f"Unknown instrument type: {instr.instrument_type}")


def get_current_position(client: IBKRClient, contract) -> float:
    """Get current position for the contract."""
    for pos in client.ib.positions():
        if pos.contract.conId == contract.conId:
            return float(pos.position)
    return 0.0


def execute_trade(client: IBKRClient, contract, target: float, current_pos: float, config) -> None:
    """Execute trade to reach target position."""
    trades = target - current_pos

    if trades == 0:
        logger.info("No trade needed - position aligned with target")
        return

    action = "BUY" if trades > 0 else "SELL"
    qty = abs(trades)

    current_price = client.get_current_price(contract)
    if current_price <= 0:
        client.ib.placeOrder(contract, MarketOrder(action, qty))
        logger.info("Placed market order: %s %s", action, qty)
        return

    stop_loss_pct = config.risk.stop_loss_pct
    take_profit_pct = config.risk.take_profit_pct

    if action == "BUY":
        stop_loss = current_price * (1 - stop_loss_pct)
        take_profit = current_price * (1 + take_profit_pct)
    else:
        stop_loss = current_price * (1 + stop_loss_pct)
        take_profit = current_price * (1 - take_profit_pct)

    client.place_bracket_order(contract, action, qty, stop_loss, take_profit)
    logger.info(
        "Placed bracket order: %s %s | Entry: %.5f | SL: %.5f | TP: %.5f",
        action, qty, current_price, stop_loss, take_profit,
    )


async def run_session():
    """Run an independent trading session."""
    config = load_config()
    logger.info("Starting trading session for %s", config.instrument.symbol)

    client = IBKRClient(
        host=config.ibkr.host,
        port=config.ibkr.port,
        client_id=config.ibkr.client_id,
    )

    await client.connect()
    logger.info("Connected to IBKR at %s:%s", config.ibkr.host, config.ibkr.port)

    contract = await create_contract(config, client)
    await client.qualify(contract)
    logger.info("Contract qualified: %s", contract.symbol)

    strategy = StrategyFactory.create(
        config.strategy.name,
        contract,
        config.strategy.params_file,
    )
    logger.info("Strategy created: %s", strategy.name)

    executor = StrategyExecutor(strategy)

    state = TradingSessionState(symbol=config.instrument.symbol)

    bars = await client.request_historical_bars(
        contract,
        bar_size=config.session.bar_size,
        duration="2 D",
    )
    logger.info("Fetched %d historical bars", len(bars))

    for bar in bars:
        state.history.append(bar)
    state.current_price = bars[-1].close if bars else 0.0

    session_start = datetime.now(UTC)
    session_end = session_start + timedelta(hours=config.session.session_duration_hours)
    logger.info(
        "Session duration: %.2f hours | End time: %s",
        config.session.session_duration_hours,
        session_end.strftime("%H:%M:%S"),
    )

    # Initialize position tracker
    position_tracker = PositionTracker()
    last_fill_count = 0

    # Get initial fills from pre-session
    initial_fills = client.ib.fills()

    # Initial target position
    target = executor.compute_target(state)
    logger.info("Initial target position: %d units", target)

    current_pos = get_current_position(client, contract)
    logger.info("Current position: %.2f units", current_pos)

    execute_trade(client, contract, target, current_pos, config)

    # Main trading loop
    logger.info("Entering trading loop...")
    while True:
        await asyncio.sleep(5)  # Check every 5 seconds

        if datetime.now(UTC) >= session_end:
            logger.info("End time reached - closing session")
            break

        # Refresh bars
        try:
            bars = await client.request_historical_bars(
                contract,
                bar_size=config.session.bar_size,
                duration="1 D",
            )
        except Exception as e:
            logger.warning("Failed to fetch bars: %s", e)
            continue

        # Update state with new bars
        for bar in bars:
            state.history.append(bar)
        state.current_price = bars[-1].close if bars else 0.0

        # Compute new target
        target = executor.compute_target(state)
        current_pos = get_current_position(client, contract)

        # Execute if position changed
        if target != current_pos:
            execute_trade(client, contract, target, current_pos, config)
        else:
            logger.debug("Position unchanged at %d", current_pos)

        # Check for new fills and log trade confirmation only when new fills occur
        current_fills = client.ib.fills()
        new_fill_count = len(current_fills)

        if new_fill_count > last_fill_count:
            # Process new fills
            for fill in current_fills[last_fill_count:]:
                position_tracker.add_fill(fill)
                logger.info(
                    "TRADE CONFIRMED: %s %.0f @ %.5f | Realized P&L: %.2f",
                    "BUY" if fill.execution.side == "BOT" else "SELL",
                    fill.execution.shares,
                    fill.execution.price,
                    position_tracker.realized_pnl
                )
            last_fill_count = new_fill_count

    # Stop trading session
    logger.info("Closing all positions...")
    execute_trade(client, contract, 0, get_current_position(client, contract), config)

    # Wait for order fills and pick up any remaining fills
    await asyncio.sleep(10)

    # Pick up any final fills
    final_fills = client.ib.fills()
    for fill in final_fills[last_fill_count:]:
        position_tracker.add_fill(fill)

    # Final reporting - only at end of session
    log_final_report(position_tracker, session_start)

    stats = position_tracker.get_stats()
    logger.info("SESSION COMPLETE - Net P&L: %.2f (after commissions: %.2f)",
                stats["realized_pnl"], stats["net_pnl"])

    client.disconnect()
    logger.info("Session stopped")


if __name__ == "__main__":
    asyncio.run(run_session())

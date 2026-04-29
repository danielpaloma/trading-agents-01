"""Independent trading session entry point."""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List

from dotenv import load_dotenv
from ib_async import MarketOrder, Fill

from src.config import load_config
from src.tools.ibkr_tools import IBKRClient
from src.strategies import StrategyFactory, StrategyExecutor
from src.state import TradingSessionState

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class PositionTracker:
    """Track fills and calculate realized P&L using FIFO matching."""
    fills: List[Fill] = field(default_factory=list)
    realized_pnl: float = 0.0
    total_commissions: float = 0.0

    def add_fill(self, fill: Fill) -> None:
        """Add a new fill and update realized P&L."""
        self.fills.append(fill)
        self._update_pnl(fill)

    def _update_pnl(self, new_fill: Fill) -> None:
        """Calculate realized P&L using FIFO matching for opposite sides."""
        new_side = new_fill.execution.side
        new_qty = new_fill.execution.shares
        new_price = new_fill.execution.price

        # Match against existing fills of opposite side
        for fill in self.fills[:-1]:  # Exclude the new fill
            if new_qty <= 0:
                break

            existing_side = fill.execution.side
            existing_qty = fill.execution.shares
            existing_price = fill.execution.price

            # Skip if same side or already fully matched
            if existing_side == new_side:
                continue

            # Calculate matched quantity
            matched_qty = min(new_qty, existing_qty)

            # Calculate P&L: SELL price - BUY price (positive = profit)
            if new_side == "SLD" and existing_side == "BOT":
                trade_pnl = (new_price - existing_price) * matched_qty
            elif new_side == "BOT" and existing_side == "SLD":
                trade_pnl = (existing_price - new_price) * matched_qty
            else:
                continue

            self.realized_pnl += trade_pnl
            new_qty -= matched_qty

        # Track commission
        if new_fill.commissionReport:
            self.total_commissions += new_fill.commissionReport.commission

    def get_stats(self) -> dict:
        """Return trading statistics."""
        buy_fills = [f for f in self.fills if f.execution.side == "BOT"]
        sell_fills = [f for f in self.fills if f.execution.side == "SLD"]

        total_bought = sum(f.execution.shares for f in buy_fills)
        total_sold = sum(f.execution.shares for f in sell_fills)
        avg_buy_price = (
            sum(f.execution.price * f.execution.shares for f in buy_fills) / total_bought
            if total_bought > 0 else 0.0
        )
        avg_sell_price = (
            sum(f.execution.price * f.execution.shares for f in sell_fills) / total_sold
            if total_sold > 0 else 0.0
            )

        return {
            "total_fills": len(self.fills),
            "realized_pnl": self.realized_pnl,
            "net_pnl": self.realized_pnl - self.total_commissions,
            "total_commissions": self.total_commissions,
            "total_bought": total_bought,
            "total_sold": total_sold,
            "avg_buy_price": avg_buy_price,
            "avg_sell_price": avg_sell_price,
        }

    def to_records(self) -> List[dict]:
        """Convert fills to dictionary records for reporting."""
        records = []
        running_pnl = 0.0

        # Group fills by time and calculate cumulative P&L
        for fill in self.fills:
            side = "BOT" if fill.execution.side == "BOT" else "SELL"
            qty = fill.execution.shares
            price = fill.execution.price
            time = fill.execution.time

            records.append({
                "time": time,
                "side": side,
                "qty": qty,
                "price": price,
            })

        return records


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


def log_final_report(tracker: PositionTracker, session_start: datetime) -> None:
    """Log the final trade report at end of session."""
    stats = tracker.get_stats()
    records = tracker.to_records()

    if not records:
        logger.info("=== FINAL TRADE REPORT ===")
        logger.info("No trades executed during this session.")
        logger.info("=== END REPORT ===")
        return

    logger.info("=" * 60)
    logger.info("FINAL TRADE REPORT - Session: %s", session_start.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)
    logger.info("SUMMARY:")
    logger.info("  Total Fills: %d", stats["total_fills"])
    logger.info("  Quantity Bought: %.0f @ avg %.5f", stats["total_bought"], stats["avg_buy_price"])
    logger.info("  Quantity Sold:   %.0f @ avg %.5f", stats["total_sold"], stats["avg_sell_price"])
    logger.info("  Gross Realized P&L: %.2f", stats["realized_pnl"])
    logger.info("  Total Commissions:  %.2f", stats["total_commissions"])
    logger.info("  Net P&L:            %.2f", stats["net_pnl"])
    logger.info("-" * 60)
    logger.info("TRADE DETAILS:")
    logger.info("  %-20s | %-6s | %8s | %10s", "Time", "Side", "Qty", "Price")
    logger.info("  " + "-" * 50)

    for r in records:
        time_str = r["time"].strftime("%H:%M:%S") if isinstance(r["time"], datetime) else str(r["time"])
        logger.info(
            "  %-20s | %-6s | %8.0f | %10.5f",
            time_str, r["side"], r["qty"], r["price"]
        )

    logger.info("=" * 60)


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

    session_start = datetime.now(timezone.utc)
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

        if datetime.now(timezone.utc) >= session_end:
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

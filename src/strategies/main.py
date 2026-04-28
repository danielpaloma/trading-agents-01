"""Independent trading session entry point."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from ib_async import MarketOrder

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


def trade_reporting(client: IBKRClient, session_start: datetime) -> dict:
    """Generate trade report from fills and P&L data."""
    try:
        fills = client.ib.fills()
        if not fills:
            return {"status": "no_fills", "message": "No fills recorded yet"}

        fill_records = []
        for fs in fills:
            exec_data = fs.execution
            fill_records.append({
                "execId": exec_data.execId,
                "time": exec_data.time,
                "side": exec_data.side,
                "cumQty": exec_data.cumQty,
                "avgPrice": exec_data.avgPrice,
            })

        pnl_records = []
        for fs in fills:
            comm = fs.commissionReport
            pnl_records.append({
                "execId": comm.execId,
                "realizedPNL": comm.realizedPNL,
            })

        import pandas as pd
        fill_df = pd.DataFrame(fill_records).set_index("execId")
        pnl_df = pd.DataFrame(pnl_records).set_index("execId")
        report = pd.concat([fill_df, pnl_df], axis=1).loc[fill_df.index]
        report = report.loc[pd.to_datetime(report["time"]) >= session_start]

        if report.empty:
            return {"status": "no_fills", "message": "No fills since session start"}

        report = report.groupby("time").agg({
            "side": "first",
            "cumQty": "max",
            "avgPrice": "mean",
            "realizedPNL": "sum",
        })
        report["cumPNL"] = report["realizedPNL"].cumsum()

        report_dict = {
            "status": "success",
            "total_trades": len(report),
            "final_cumPNL": float(report["cumPNL"].iloc[-1]) if not report.empty else 0.0,
            "details": report.to_dict("records"),
        }

        logger.info("=== TRADE REPORT ===")
        logger.info("Total Trades: %d", report_dict["total_trades"])
        logger.info("Final Cumulative P&L: %.2f", report_dict["final_cumPNL"])
        logger.info("Details:")
        for record in report_dict["details"]:
            logger.info(
                "  %s | Qty: %.0f | Price: %.5f | P&L: %.2f | CumPNL: %.2f",
                record["side"], record["cumQty"], record["avgPrice"],
                record["realizedPNL"], record["cumPNL"],
            )
        logger.info("=== END REPORT ===")

        return report_dict

    except Exception as e:
        logger.warning("Trade reporting error: %s", e)
        return {"status": "error", "message": str(e)}


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

        # Periodic reporting
        trade_reporting(client, session_start)

    # Stop trading session
    logger.info("Closing all positions...")
    execute_trade(client, contract, 0, get_current_position(client, contract), config)

    await asyncio.sleep(10)  # Wait for order fills

    # Final reporting
    logger.info("Generating final report...")
    report = trade_reporting(client, session_start)
    if report["status"] == "success":
        logger.info("Session Final P&L: %.2f", report["final_cumPNL"])

    client.disconnect()
    logger.info("Session stopped")


if __name__ == "__main__":
    asyncio.run(run_session())

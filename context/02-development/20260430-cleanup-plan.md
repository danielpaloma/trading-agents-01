# Codebase Cleanup Plan - Preserve Strategies Feature

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all agent-based and unused code while preserving the independent strategies trading session functionality.

**Architecture:** The strategies module (`src/strategies/main.py`) is a standalone entry point that does NOT use the agent framework. It directly connects to IBKR and runs strategies. The agent framework (`src/agents/`, `src/main.py`) and related unused tools can be safely removed.

**Tech Stack:** Python 3.12+, pandas, numpy, ib_async, PyYAML, pytest

---

## Dependency Analysis Summary

### Files REQUIRED by `src/strategies/main.py`

**Core Strategy Module:**
- `src/strategies/__init__.py` - exports Strategy, StrategyFactory, StrategyExecutor
- `src/strategies/strategy_base.py` - Strategy ABC with `calculate_position(bars) -> int`
- `src/strategies/factory.py` - StrategyFactory.create() for instantiating strategies
- `src/strategies/executor.py` - StrategyExecutor.compute_target(state) -> int
- `src/strategies/sma_crossover.py` - SMACrossoverStrategy implementation
- `src/strategies/bollinger_bands.py` - BollingerBandsStrategy implementation
- `src/strategies/contrarian.py` - ContrarianStrategy implementation
- `src/strategies/tanh_strategy.py` - TanhStrategy implementation
- `src/strategies/main.py` - Entry point for trading sessions

**Configuration & State:**
- `src/config.py` - Config dataclasses, load_config() from environment
- `src/state.py` - TradingSessionState with OHLCVHistory

**Models:**
- `src/models/__init__.py` - Models package marker
- `src/models/market_data.py` - Bar, OHLCVHistory classes
- `src/models/signals.py` - Signal, Direction enums (used by state.py)
- `src/models/orders.py` - OrderFill class (used by state.py)

**Tools:**
- `src/tools/__init__.py` - Tools package marker
- `src/tools/ibkr_tools.py` - IBKRClient for broker connection
- `src/tools/switch-model.sh` - Developer utility, switch LLM models

**Config Files:**
- `config/strategies/*.yaml` - Strategy parameter files

**Tests:**
- `tests/strategies/test_tanh_strategy.py` - Strategy unit tests
- `tests/test_models_market_data.py` - Bar/OHLCVHistory tests
- `tests/test_state.py` - TradingSessionState tests
- `tests/tools/test_ibkr_tools.py` - IBKRClient tests
- `tests/conftest.py` - Shared pytest fixtures

### Files NOT USED by Strategies (Safe to Remove)

**Agent Framework (entirely unused):**
- `src/main.py` - Orchestrator entry point
- `src/agents/orchestrator.py` - TradingOrchestrator
- `src/agents/market_data_agent.py` - Agent for market data
- `src/agents/analysis_agent.py` - Agent for analysis
- `src/agents/strategy_agent.py` - Agent for strategy
- `src/agents/risk_agent.py` - Agent for risk
- `src/agents/execution_agent.py` - Agent for execution
- `src/agents/monitor_agent.py` - Agent for monitoring
- `src/agents/backtest_agent.py` - Agent for backtesting
- `src/agents/__init__.py` - Agents package

**Unused Tools:**
- `src/tools/analysis_tools.py` - Analysis functions (unused by strategies)
- `src/tools/risk_tools.py` - Risk functions (unused by strategies)

**Unused Models:**
- `src/models/portfolio.py` - Position, SessionSummary (unused)

**Unused Tests:**
- `tests/agents/` - Entire agents test directory
- `tests/tools/test_analysis_tools.py` - Analysis tools tests
- `tests/tools/test_risk_tools.py` - Risk tools tests

---

## Task Breakdown

### Task 1: Backup Current State

**Files:**
- Create: `context/02-development/backup-branch-marker.txt`

- [ ] **Step 1: Create backup branch**

```bash
git checkout -b backup/pre-cleanup-agents-main
git push -u origin backup/pre-cleanup-agents-main
git checkout feat/strategies
```

Expected: Branch created and pushed, back on feat/strategies

- [ ] **Step 2: Document backup location**

Create `context/02-development/backup-branch-marker.txt`:
```
Backup branch created before cleanup:
- Branch: backup/pre-cleanup-agents-main
- Date: 2026-04-30
- Contains: Full agent framework before removal
```

- [ ] **Step 3: Commit marker file**

```bash
git add context/02-development/backup-branch-marker.txt
git commit -m "docs: document backup branch before cleanup"
```

---

### Task 2: Remove Agent Framework

**Files:**
- Delete: `src/main.py`
- Delete: `src/agents/` (entire directory)

- [ ] **Step 1: Remove src/main.py**

```bash
git rm src/main.py
```

- [ ] **Step 2: Remove agents directory**

```bash
git rm -r src/agents/
```

- [ ] **Step 3: Commit changes**

```bash
git commit -m "chore(cleanup): remove agent framework - unused by strategies module

Removes:
- src/main.py (orchestrator entry point)
- src/agents/ (entire agent framework)

Strategies module uses src/strategies/main.py directly"
```

---

### Task 3: Remove Unused Tools

**Files:**
- Delete: `src/tools/analysis_tools.py`
- Delete: `src/tools/risk_tools.py`

- [ ] **Step 1: Verify ibkr_tools.py is NOT being removed**

Confirm this file is NOT in the deletion list:
- `src/tools/ibkr_tools.py` - KEEP (required by strategies)

- [ ] **Step 2: Remove analysis_tools.py**

```bash
git rm src/tools/analysis_tools.py
```

- [ ] **Step 3: Remove risk_tools.py**

```bash
git rm src/tools/risk_tools.py
```

- [ ] **Step 4: Commit changes**

```bash
git commit -m "chore(cleanup): remove unused analysis and risk tools

These tools were used by the removed agent framework.
Strategies module handles risk internally in src/strategies/main.py"
```

---

### Task 4: Remove Unused Models

**Files:**
- Delete: `src/models/portfolio.py`

- [ ] **Step 1: Verify required models are NOT being removed**

Confirm these files are NOT deleted:
- `src/models/market_data.py` - KEEP (required)
- `src/models/signals.py` - KEEP (required by state.py)
- `src/models/orders.py` - KEEP (required by state.py)

- [ ] **Step 2: Remove portfolio.py**

```bash
git rm src/models/portfolio.py
```

- [ ] **Step 3: Commit changes**

```bash
git commit -m "chore(cleanup): remove unused portfolio models

Position and SessionSummary were used by agent framework.
Strategies module tracks positions internally via PositionTracker."
```

---

### Task 5: Remove Unused Tests

**Files:**
- Delete: `tests/agents/` (entire directory)
- Delete: `tests/tools/test_analysis_tools.py`
- Delete: `tests/tools/test_risk_tools.py`

- [ ] **Step 1: Verify required tests are NOT being removed**

Confirm these files/directories are NOT deleted:
- `tests/strategies/` - KEEP (strategy tests)
- `tests/test_models_market_data.py` - KEEP (required)
- `tests/test_state.py` - KEEP (required)
- `tests/tools/test_ibkr_tools.py` - KEEP (required)
- `tests/conftest.py` - KEEP (shared fixtures)

- [ ] **Step 2: Remove agent tests**

```bash
git rm -r tests/agents/
```

- [ ] **Step 3: Remove unused tool tests**

```bash
git rm tests/tools/test_analysis_tools.py
git rm tests/tools/test_risk_tools.py
```

- [ ] **Step 4: Check if tools directory is empty**

```bash
ls tests/tools/
```

If only `__init__.py` and `test_ibkr_tools.py` remain, that's correct.

- [ ] **Step 5: Commit changes**

```bash
git commit -m "chore(cleanup): remove unused agent and tool tests

Removes tests for:
- agents/ (entire framework removed)
- analysis_tools.py (removed)
- risk_tools.py (removed)

Keeps tests for strategies and required dependencies."
```

---

### Task 6: Verify Tests Still Pass

**Files:**
- Run: `tests/` directory

- [ ] **Step 1: Run all remaining tests**

```bash
uv run pytest tests/ -v
```

Expected: All tests pass (6 files should run)
- tests/test_models_market_data.py
- tests/test_state.py
- tests/tools/test_ibkr_tools.py
- tests/strategies/test_tanh_strategy.py

- [ ] **Step 2: Verify no import errors**

If tests fail, check for orphaned imports from removed files.

- [ ] **Step 3: Fix any import issues**

Check files for imports from removed modules:
- `from src.agents.*` - should not exist
- `from src.tools.analysis_tools` - should not exist
- `from src.tools.risk_tools` - should not exist
- `from src.models.portfolio` - should not exist

Grep to verify:
```bash
grep -r "from src.agents" src/ tests/ || echo "No agent imports found - good"
grep -r "from src.tools.analysis_tools" src/ tests/ || echo "No analysis_tools imports found - good"
grep -r "from src.tools.risk_tools" src/ tests/ || echo "No risk_tools imports found - good"
grep -r "from src.models.portfolio" src/ tests/ || echo "No portfolio imports found - good"
```

---

### Task 7: Verify Strategies Entry Point Works

**Files:**
- Run: `src/strategies/main.py`

- [ ] **Step 1: Verify imports resolve**

```bash
uv run python -c "from src.strategies.main import run_session; print('Import successful')"
```

Expected: "Import successful"

- [ ] **Step 2: Verify module structure**

```bash
uv run python -c "
from src.strategies import Strategy, StrategyFactory, StrategyExecutor
from src.strategies import SMACrossoverStrategy, BollingerBandsStrategy
from src.strategies import ContrarianStrategy, TanhStrategy
print('All strategy imports successful')
print('Available strategies:', list(StrategyFactory._STRATEGY_CLASSES.keys()))
"
```

Expected: All imports succeed, 4 strategies listed

---

### Task 8: Update Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current README.md**

Check if README.md references removed components.

- [ ] **Step 2: Update README to reflect strategies-only architecture**

Remove or update sections referencing:
- Agents framework
- Orchestrator
- Multi-agent architecture

Keep sections for:
- Strategies module
- Configuration via .env
- Running trading sessions

- [ ] **Step 3: Commit README updates**

```bash
git add README.md
git commit -m "docs: update README for strategies-only architecture

Remove references to agent framework and orchestrator.
Document strategies module usage."
```

---

### Task 9: Final Verification & Summary

- [ ] **Step 1: List remaining files in src/**

```bash
find src/ -name "*.py" | sort
```

Expected structure:
```
src/__init__.py
src/config.py
src/models/__init__.py
src/models/market_data.py
src/models/orders.py
src/models/signals.py
src/state.py
src/strategies/__init__.py
src/strategies/bollinger_bands.py
src/strategies/contrarian.py
src/strategies/executor.py
src/strategies/factory.py
src/strategies/main.py
src/strategies/sma_crossover.py
src/strategies/strategy_base.py
src/strategies/tanh_strategy.py
src/tools/__init__.py
src/tools/ibkr_tools.py
```

- [ ] **Step 2: Verify tests pass one more time**

```bash
uv run pytest tests/ -v --tb=short
```

- [ ] **Step 3: Create cleanup summary**

Create `context/02-development/cleanup-summary.md`:
```markdown
# Cleanup Summary

## Date
2026-04-30

## Objective
Remove agent framework and unused code, preserving strategies functionality.

## Files Removed

### Entry Points
- src/main.py (orchestrator-based, unused by strategies)

### Agents (entire framework)
- src/agents/__init__.py
- src/agents/orchestrator.py
- src/agents/market_data_agent.py
- src/agents/analysis_agent.py
- src/agents/strategy_agent.py
- src/agents/risk_agent.py
- src/agents/execution_agent.py
- src/agents/monitor_agent.py
- src/agents/backtest_agent.py

### Unused Tools
- src/tools/analysis_tools.py
- src/tools/risk_tools.py

### Unused Models
- src/models/portfolio.py

### Unused Tests
- tests/agents/__init__.py
- tests/agents/test_market_data_agent.py
- tests/agents/test_analysis_agent.py
- tests/agents/test_strategy_agent.py
- tests/agents/test_risk_agent.py
- tests/agents/test_execution_agent.py
- tests/agents/test_monitor_agent.py
- tests/agents/test_backtest_agent.py
- tests/tools/test_analysis_tools.py
- tests/tools/test_risk_tools.py

## Files Preserved

### Core Strategy Module
- src/strategies/main.py (entry point)
- src/strategies/__init__.py
- src/strategies/strategy_base.py
- src/strategies/factory.py
- src/strategies/executor.py
- src/strategies/sma_crossover.py
- src/strategies/bollinger_bands.py
- src/strategies/contrarian.py
- src/strategies/tanh_strategy.py

### Configuration & State
- src/config.py
- src/state.py

### Models
- src/models/market_data.py
- src/models/signals.py
- src/models/orders.py

### Tools
- src/tools/ibkr_tools.py

### Tests
- tests/strategies/test_tanh_strategy.py
- tests/test_models_market_data.py
- tests/test_state.py
- tests/tools/test_ibkr_tools.py
- tests/conftest.py

## Verification
- All remaining tests pass
- Strategies entry point imports successfully
- Git history preserved on backup branch
```

- [ ] **Step 4: Final commit**

```bash
git add context/02-development/cleanup-summary.md
git commit -m "docs: add cleanup summary

Documents what was removed and what was preserved.
Backup branch: backup/pre-cleanup-agents-main"
```

---

## Self-Review Checklist

Before marking complete:

**1. Spec Coverage:**
- [ ] Agent framework removed
- [ ] Unused tools removed
- [ ] Unused models removed
- [ ] Unused tests removed
- [ ] Strategies functionality preserved
- [ ] Backup created

**2. Placeholder Scan:**
- [ ] No "TBD"/"TODO" markers
- [ ] Each step has exact commands
- [ ] Each step has expected output
- [ ] No vague "fix issues" steps without specifics

**3. Type/Import Consistency:**
- [ ] All imports in preserved files verified
- [ ] No references to removed modules
- [ ] Tests align with preserved code

---

## Execution Handoff

**Plan complete and saved to `context/02-development/cleanup-plan.md`.**

After execution, the codebase will contain only the strategies module and its dependencies, with all agent framework code removed.

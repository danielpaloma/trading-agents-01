# Feature: Strategy definition, setup and selection

Goal: Implement a python module capable to define a strategy, setup parameters and select the strategy that will be executed during the trading session.

## A. Strategy definition and parameter setup
1. Check this example which defines three strategies:

context\01-planning\FT002-strategies\strategies.py

2. Create config files to adjust the strategy parameters. One file per strategy.
3. Create a base class to define strategies and parameters, so that a user can include more strategies in future.

## B. Strategy execution

1. Read this file as reference for the strategy execution module.
2. The idea is to have a loose coupling between several strategies and the execution module.
3. The user can define the strategy in the .env, then define the parameters in the corresponding config file and the execution module can pick up this data and run a trading session using the defined strategy.

**Reference File**: 'context\references\algo-trading-course\trader_ibkr.py'

## General:
* Consider updating the .env.example (and .env) if needed.
* Include a README file in 'src/strategies' folder.
* This module must produce logs that are captured here: ./logs
* Use this file as reference, reuse some functions if needed: 'context\references\algo-trading-course\trader_ibkr.py'
* Keep the implementation concrete and focused on: strategy definition, parameter setup, loose coupling between strategies and execution.

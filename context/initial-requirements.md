# Trading Agents

## Purpose
Create a Team of Trading Agents Team to cover the whole workflow of a trading session:
 

## Tech stack
Openrouter to assign LLMs: https://openrouter.ai/docs/quickstart
Claude Agents SDK as agentic framework:
    * https://code.claude.com/docs/en/agent-sdk/overview
    * https://github.com/anthropics/claude-agent-sdk-python


* Main language is python.
* Use ib_async api to interact with Interactive Brokers' Trader Workstation (TWS) and IB Gateway
* ib_async github repo: https://github.com/ib-api-reloaded/ib_async
* ib_async api documentation: https://ib-api-reloaded.github.io/ib_async/api.html

* ALWAYS use uv as python package manager (DO NOT use `pip install`, use `uv add` instead)



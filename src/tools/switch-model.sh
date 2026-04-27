#!/bin/bash

################################################################################
# Claude Code + OpenRouter Switcher
################################################################################
#
# DESCRIPTION:
#   This script configures your current shell so that Claude Code (`claude`)
#   talks to OpenRouter, exactly as described in the official guide:
#   https://openrouter.ai/docs/guides/guides/claude-code-integration
#
# SETUP:
#   1. Ensure your OpenRouter API key is in .env file:
#      OPENROUTER_API_KEY="sk-or-your-key-here"
#   2. Make the script executable (if needed):
#      chmod +x src/tools/switch-model.sh
#
# USAGE:
#   source ./src/tools/switch-model.sh openrouter    # Configure env for Claude Code via OpenRouter
#   source ./src/tools/switch-model.sh default       # Clear OpenRouter-related env and revert
#   source ./src/tools/switch-model.sh status        # Show current configuration
#   ./src/tools/switch-model.sh help          # Display help information
#
################################################################################

OPENROUTER_MODEL_DEFAULT="minimax/minimax-m2.7" #check for models with tools support (https://openrouter.ai/models?fmt=cards&supported_parameters=tools)
OPENROUTER_BASE_URL="https://openrouter.ai/api"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_usage() {
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  openrouter [API_KEY] [MODEL]  Configure current shell to use OpenRouter"
    echo "                               (MODEL defaults to $OPENROUTER_MODEL_DEFAULT)"
    echo "  default                        Switch back to default Claude (no OpenRouter)"
    echo "  status                Show current model configuration"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  source $0 openrouter"
    echo "  source $0 openrouter sk-or-your-api-key moonshotai/kimi-k2.5"
    echo "  source $0 default"
    echo "  $0 status"
}

is_sourced() {
    # True if this script is sourced into the current shell (required for exports to persist)
    [ "${BASH_SOURCE[0]}" != "$0" ]
}

find_env_file() {
    # Look for .env in current directory or parent directories
    local current_dir="$(pwd)"
    while [ "$current_dir" != "/" ]; do
        if [ -f "$current_dir/.env" ]; then
            echo "$current_dir/.env"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    return 1
}

load_api_key_from_env() {
    local env_file=$(find_env_file)

    if [ -z "$env_file" ]; then
        return 1
    fi

    # Parse OPENROUTER_API_KEY from .env file (handles quotes and spaces)
    local api_key=$(grep "^OPENROUTER_API_KEY\s*=" "$env_file" | sed 's/.*=\s*["\x27]\?\([^"]*\)["\x27]\?$/\1/' | xargs)

    if [ -n "$api_key" ]; then
        echo "$api_key"
        return 0
    fi
    return 1
}

switch_to_openrouter() {
    local api_key="$1"
    local model="${2:-$OPENROUTER_MODEL_DEFAULT}"

    if ! is_sourced; then
        echo -e "${YELLOW}Error:${NC} You must run this with 'source' so exports persist in your current shell."
        echo "  source ./switch-model.sh openrouter [API_KEY] [MODEL]"
        return 1
    fi

    # Try to get API key from .env if not provided
    if [ -z "$api_key" ]; then
        api_key=$(load_api_key_from_env)
        if [ $? -eq 0 ]; then
            echo -e "${BLUE}Found OpenRouter API key in .env file${NC}"
        else
            read -sp "Enter your OpenRouter API key: " api_key
            echo ""
        fi
    fi

    if [ -z "$api_key" ]; then
        echo -e "${YELLOW}Error: API key is required (not found in .env and not provided)${NC}"
        return 1
    fi

    export OPENROUTER_API_KEY="$api_key"
    export ANTHROPIC_BASE_URL="$OPENROUTER_BASE_URL"
    export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
    export ANTHROPIC_API_KEY=""

    # Route Claude Code's default "Haiku/Sonnet/Opus" selections to a chosen OpenRouter model (e.g. Kimi K2.5)
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="$model"
    export ANTHROPIC_DEFAULT_SONNET_MODEL="$model"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="$model"

    echo -e "${GREEN}✓ Configured Claude Code to use OpenRouter${NC}"
    echo -e "${BLUE}Base URL:${NC} $OPENROUTER_BASE_URL"
    echo -e "${BLUE}Default model:${NC} $model"
    echo ""
    echo "You can now use Claude Code with OpenRouter:"
    echo "  claude"
}

switch_to_default() {
    if ! is_sourced; then
        echo -e "${YELLOW}Error:${NC} You must run this with 'source' so unsets apply to your current shell."
        echo "  source ./switch-model.sh default"
        return 1
    fi

    unset OPENROUTER_API_KEY
    unset ANTHROPIC_BASE_URL
    unset ANTHROPIC_API_KEY
    unset ANTHROPIC_AUTH_TOKEN
    unset ANTHROPIC_DEFAULT_HAIKU_MODEL
    unset ANTHROPIC_DEFAULT_SONNET_MODEL
    unset ANTHROPIC_DEFAULT_OPUS_MODEL

    echo -e "${GREEN}✓ Switched back to default Claude models${NC}"
    echo "Claude Code will now use your default Anthropic API configuration"
}

show_status() {
    echo "Current Claude Code / OpenRouter Configuration:"
    echo "----------------------------"

    if [ -z "$ANTHROPIC_BASE_URL" ]; then
        echo -e "${GREEN}Using default Claude configuration (no OpenRouter)${NC}"
    else
        echo -e "${BLUE}Using OpenRouter via Anthropic-compatible API skin${NC}"
        echo "  Base URL: $ANTHROPIC_BASE_URL"
        echo "  Haiku Model: ${ANTHROPIC_DEFAULT_HAIKU_MODEL:-not set}"
        echo "  Sonnet Model: ${ANTHROPIC_DEFAULT_SONNET_MODEL:-not set}"
        echo "  Opus Model: ${ANTHROPIC_DEFAULT_OPUS_MODEL:-not set}"
        if [ -n "$OPENROUTER_API_KEY" ]; then
            echo -e "  OpenRouter API Key: ${OPENROUTER_API_KEY:0:10}... (hidden)"
        fi
        if [ -n "$ANTHROPIC_AUTH_TOKEN" ]; then
            echo -e "  Anthropic Auth Token (via OpenRouter): ${ANTHROPIC_AUTH_TOKEN:0:10}... (hidden)"
        fi
        if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo "  ANTHROPIC_API_KEY: (explicitly empty, as required)"
        fi
    fi
}

# Main script logic
case "${1:-help}" in
    openrouter)
        switch_to_openrouter "$2" "$3"
        ;;
    default)
        switch_to_default
        ;;
    status)
        show_status
        ;;
    help)
        show_usage
        ;;
    *)
        echo -e "${YELLOW}Unknown option: $1${NC}"
        show_usage
        exit 1
        ;;
esac

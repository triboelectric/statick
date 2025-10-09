#!/usr/bin/env bash

# Function to display help information.
show_help() {
  echo "Statick Developer Commands:"
  echo "  dev format     - Format all Python code with black."
  echo "  dev help       - Show this help message."
  echo "  dev qa         - Run linting and static analysis tools."
  echo "  dev reset-venv - Remove and recreate the virtual environment."
  echo "  dev test       - Run unit tests and get code coverage."
}

# Match the `workspaceFolder` in the .devcontainer.json.
APP_HOME="/opt/statick"
export APP_HOME

# Function to execute commands
execute_command() {
    case $1 in
    format)
        cd $APP_HOME || exit
        black src/statick_tool/
        ;;
    help)
        show_help
        ;;
    qa)
        cd $APP_HOME || exit
        statick . -o /tmp/x --level self_check --log info
        ;;
    reset-venv)
        rm -rf /opt/venv
        uv venv /opt/venv
        # shellcheck disable=SC1091
        . /opt/venv/bin/activate
        cd $APP_HOME || exit
        # The [lint,test] range below is valid pip syntax
        # shellcheck disable=SC2102
        uv pip install -e .[docs,test]
        ;;
    test)
        cd $APP_HOME || exit
        tox -e py312
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        echo "Use 'dev --help' for a list of available commands."
        ;;
    esac
}

# Check for --help argument
if [ -z "$1" ] || [ "$1" == "--help" ]; then
    show_help
else
    execute_command "$1"
fi

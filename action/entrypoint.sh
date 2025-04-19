#!/usr/bin/env bash

mkdir -p /tmp/statick_output

STATICK_ARGS=""

if [ -n "$INPUT_PACKAGE_PATH" ]; then
  STATICK_ARGS+=" $INPUT_PACKAGE_PATH"
else
  echo "Package not supplied, but is required."
  exit 1
fi

if [ -n "$INPUT_CHECK" ]; then
  if [ "$INPUT_CHECK" = "true" ]; then
    STATICK_ARGS+=" --check"
  fi
fi

if [ -n "$INPUT_CONFIG" ]; then
  STATICK_ARGS+=" --config $INPUT_CONFIG"
fi

if [ -n "$INPUT_LEVEL" ]; then
  STATICK_ARGS+=" --level $INPUT_LEVEL"
fi

if [ -n "$INPUT_LOG_LEVEL" ]; then
  STATICK_ARGS+=" --log $INPUT_LOG_LEVEL"
fi

if [ -n "$INPUT_OUTPUT_PATH" ]; then
  STATICK_ARGS+=" --output-directory $INPUT_OUTPUT_PATH"
fi

if [ -n "$INPUT_PROFILE" ]; then
  STATICK_ARGS+=" --profile $INPUT_PROFILE"
fi

if [ -n "$INPUT_TIMINGS" ]; then
  if [ "$INPUT_TIMINGS" = "true" ]; then
    STATICK_ARGS+=" --timings"
  fi
fi

if [ -n "$INPUT_USER_PATHS" ]; then
  STATICK_ARGS+=" --user-paths $INPUT_USER_PATHS"
fi

# shellcheck disable=SC1091
. /opt/venv/bin/activate
# shellcheck disable=SC2086
statick $STATICK_ARGS

exit_code=$?

if [ $exit_code -ne 0 ]; then
  echo "Error(s) found by Statick, or Statick did not run successfully"
  exit $exit_code
fi

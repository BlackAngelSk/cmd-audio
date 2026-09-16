#!/bin/bash
# CMD-AUDIO start script
cd "$(dirname "$0")"
exec .venv/bin/cmd-audio "$@"

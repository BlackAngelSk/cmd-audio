#!/bin/bash
# CMD-AUDIO start script
#
# The browser live-controls panel is served by default so the controls are
# always reachable (the URL is printed when the render starts).
#   ./start.sh song.mp3               -> terminal + controls on :8080
#   ./start.sh song.mp3 --no-web      -> terminal only
#   ./start.sh song.mp3 --web-port N  -> controls on port N
cd "$(dirname "$0")"

has_flag() {
  for arg in "$@"; do
    case "$arg" in
      --web|--web=*|--no-web|--setup-ui|--no-setup-ui|--help|-h) return 0 ;;
    esac
  done
  return 1
}

if has_flag "$@"; then
  exec .venv/bin/cmd-audio "$@"
fi

exec .venv/bin/cmd-audio "$@" --web

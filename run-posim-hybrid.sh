#!/usr/bin/env bash
# Parallels GPU scene display; sonar sensors retain the software Ogre 2 renderer.
set -eo pipefail
workspace="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
profile="$workspace/.local/runtime/virgl-compat"
source "$HOME/.ros_ardusub_env/env"
source "$workspace/install/setup.bash"
if [[ ! -f "$profile/build/libgz-rendering-ogre.so" ]]; then
    printf 'Build the local renderer first: %s/extras/parallels/build.sh\n' "$workspace" >&2
    exit 1
fi
export QT_QPA_PLATFORM=xcb
export POSIM_PARALLELS_RUNTIME="$profile"
cd "$workspace"
exec ros2 launch "$workspace/extras/parallels/hybrid.launch.py" "$@"

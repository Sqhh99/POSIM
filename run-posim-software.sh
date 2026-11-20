#!/usr/bin/env bash
# Launch POSIM with software OpenGL on this virtual machine.
set -eo pipefail

scenario="${1:-underwater}"
case "$scenario" in
    underwater|surface) ;;
    -h|--help)
        printf '%s\n' \
            'Usage: ./run-posim-software.sh [underwater|surface] [launch arguments...]' \
            'Example: ./run-posim-software.sh underwater sonar:=true compute_backend:=cpu'
        exit 0
        ;;
    *)
        printf 'Unknown scenario: %s (use underwater or surface)\n' "$scenario" >&2
        exit 2
        ;;
esac
if (( $# > 0 )); then
    shift
fi

workspace="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/.ros_ardusub_env/env"
source "$workspace/install/setup.bash"

export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export QT_QPA_PLATFORM=xcb

cd "$workspace"
exec ros2 launch posim_demos "${scenario}_tutorial.launch.py" "$@"

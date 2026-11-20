#!/usr/bin/env bash
# Keep the colcon workspace and optional source overlays inside this project.
set -eo pipefail
project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$HOME/.ros_ardusub_env/env"
export CMAKE_BUILD_PARALLEL_LEVEL="${CMAKE_BUILD_PARALLEL_LEVEL:-1}"
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-1}"
export MAKEFLAGS="${MAKEFLAGS:--j1}"
sources=("$project")
overrides=()
if [[ -d "$project/.local/deps/ros_gz" ]]; then
    sources+=("$project/.local/deps/ros_gz")
    overrides=(--allow-overriding ros_gz ros_gz_bridge ros_gz_image
        ros_gz_interfaces ros_gz_sim ros_gz_sim_demos)
fi
cd "$project"
exec colcon --log-base "$project/log" build \
    --build-base "$project/build" --install-base "$project/install" \
    --merge-install --symlink-install --executor sequential \
    --base-paths "${sources[@]}" "${overrides[@]}" \
    --cmake-args -DCMAKE_BUILD_TYPE=Release "$@"

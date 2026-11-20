"""GPU scene display with software Ogre 2 sensors on Parallels."""
from pathlib import Path
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, EmitEvent, ExecuteProcess, IncludeLaunchDescription,
    OpaqueFunction, RegisterEventHandler, SetEnvironmentVariable, TimerAction,
)
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def setup(context):
    share = Path(get_package_share_directory("posim_demos"))
    base = Path(os.environ.get("POSIM_PARALLELS_RUNTIME",
        str(Path(__file__).resolve().parents[2] / ".local/runtime/virgl-compat")))
    sonar = LaunchConfiguration("sonar").perform(context) == "true"
    temporary = tempfile.TemporaryDirectory(prefix="posim-hybrid-")
    folder = Path(temporary.name)
    sys.path.insert(0, str(share / "launch"))
    from tutorial_models import underwater_world
    underwater_world(
        Path(get_package_share_directory("posim_worlds")) / "worlds/shallow_underwater.world",
        folder / "gui-world.sdf", sonar,
    )
    gui = ET.parse(folder / "gui-world.sdf").find("world/gui")
    for plugin in list(gui):
        if plugin.get("filename") == "posim_underwater_gui":
            gui.remove(plugin)
        engine = plugin.find("engine")
        if engine is not None:
            engine.text = "ogre"
    window = ET.Element("window")
    ET.SubElement(window, "width").text = "1200"
    ET.SubElement(window, "height").text = "1000"
    config = folder / "gui.config"
    config.write_text(ET.tostring(window, encoding="unicode") + "\n" + "\n".join(
        ET.tostring(plugin, encoding="unicode") for plugin in gui
    ))
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(share / "launch/underwater_tutorial.launch.py")),
        launch_arguments={
            "sonar": LaunchConfiguration("sonar"),
            "compute_backend": LaunchConfiguration("compute_backend"),
            "gui": "false", "rviz": LaunchConfiguration("rviz"),
        }.items(),
    )
    display = ExecuteProcess(
        name="posim_gpu_display",
        cmd=["env", "-u", "LIBGL_ALWAYS_SOFTWARE", "-u", "GALLIUM_DRIVER",
             str(Path(get_package_prefix("gz_sim_vendor")) /
                 "opt/gz_sim_vendor/libexec/gz/sim10/gz-sim-gui-client"),
             "--render-engine-gui", "ogre", "--gui-config", str(config)],
        additional_env={
            "GZ_RENDERING_PLUGIN_PATH": str(base / "build"),
            "GZ_SIM_SYSTEM_PLUGIN_PATH": str(base / "build") + ":" + os.environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH", ""),
            "QT_QPA_PLATFORM": "xcb",
        },
        output="screen",
    )
    actions = [
        RegisterEventHandler(OnShutdown(on_shutdown=[
            OpaqueFunction(function=lambda _context: temporary.cleanup()),
        ])),
        RegisterEventHandler(OnProcessExit(target_action=display, on_exit=[
            EmitEvent(event=Shutdown(reason="Gazebo display closed")),
        ])),
        SetEnvironmentVariable("LIBGL_ALWAYS_SOFTWARE", "1"),
        SetEnvironmentVariable("GALLIUM_DRIVER", "llvmpipe"),
        SetEnvironmentVariable("GZ_PARTITION", f"posim_hybrid_{os.getpid()}"),
        simulation,
        TimerAction(period=4.0, actions=[display]),
    ]
    if sonar:
        actions.extend([
            Node(package="posim_demos", executable="sonar_display.py",
                 remappings=[
                     ("sonar_image", "/model/bluerov2_heavy_multibeam_sonar/multibeam_sonar/sonar_image"),
                     ("sonar_rgb", "/tutorial/sonar_rgb"),
                 ], parameters=[{"use_sim_time": True}]),
            Node(package="ros_gz_bridge", executable="parameter_bridge",
                 arguments=["/tutorial/sonar@sensor_msgs/msg/Image]gz.msgs.Image"],
                 remappings=[("/tutorial/sonar", "/tutorial/sonar_rgb")]),
        ])
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("sonar", default_value="true", choices=["true", "false"]),
        DeclareLaunchArgument("compute_backend", default_value="cpu", choices=["cpu", "auto"]),
        DeclareLaunchArgument("rviz", default_value="false", choices=["true", "false"]),
        OpaqueFunction(function=setup),
    ])

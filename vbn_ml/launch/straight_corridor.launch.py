import launch
from launch_ros.actions import Node

def generate_launch_description():
    return launch.LaunchDescription([
        # Define arguments
        launch.actions.DeclareLaunchArgument(
            name='debug',
            default_value='false'
        ),
        launch.actions.DeclareLaunchArgument(
            name='gui',
            default_value='true'
        ),
        launch.actions.DeclareLaunchArgument(
            name='pause',
            default_value='false'
        ),
        launch.actions.DeclareLaunchArgument(
            name='world',
            default_value=launch.substitutions.FindPackageShare(package='vbn_ml').find('GazeboWorlds/straight_corridor.world')
        ),
        launch.actions.DeclareLaunchArgument(
            name='extra_gazebo_args',
            default_value='--verbose'
        ),
        launch.actions.DeclareLaunchArgument(
            name='front_laser',
            default_value='false'
        ),
        launch.actions.DeclareLaunchArgument(
            name='config',
            default_value=launch.substitutions.LaunchConfiguration('default_config')
        ),

        # Conditional argument setting
        launch.actions.SetLaunchConfiguration(
            name='default_config',
            value='front_laser',
            condition=launch.conditions.IfCondition(launch.substitutions.LaunchConfiguration('front_laser'))
        ),
        launch.actions.SetLaunchConfiguration(
            name='default_config',
            value='base',
            condition=launch.conditions.UnlessCondition(launch.substitutions.LaunchConfiguration('front_laser'))
        ),

        # Include Gazebo launch
        launch.actions.IncludeLaunchDescription(
            launch.launch_description_sources.PythonLaunchDescriptionSource(
                [launch.substitutions.FindPackageShare(package='gazebo_ros').find('launch'), '/empty_world.launch.py']
            ),
            launch_arguments={
                'world_name': launch.substitutions.LaunchConfiguration('world'),
                'debug': launch.substitutions.LaunchConfiguration('debug'),
                'gui': launch.substitutions.LaunchConfiguration('gui'),
                'paused': launch.substitutions.LaunchConfiguration('pause'),
                'use_sim_time': 'true',
                'extra_gazebo_args': launch.substitutions.LaunchConfiguration('extra_gazebo_args')
            }
        ),

        # Spawn Jackal node
        Node(
            package='vbn_ml',
            executable='spawn_jackal',
            name='spawn_jackal',
            arguments=[
                '10', '-1.5', '1.0', '-3.15',
                launch.substitutions.LaunchConfiguration('config')
            ]
        )
    ])

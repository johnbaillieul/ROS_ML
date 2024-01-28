# ROS_ML
Repo for experiments using git technology

Working code to run navigate with vision based on time to transit values.

To run the code

## To run the code

In ~/.bashrc
add the following but adjust the username

```
export GAZEBO_MODEL_PATH=${GAZEBO_MODEL_PATH}:/home/olagh/ros2_ws/src/ROS_ML/vbn_ml/models
export JACKAL_URDF_EXTRAS=/home/olagh/ros2_ws/src/ROS_ML/vbn_ml/urdf/realsense.urdf.xacro
```

Run in a terminal
```
mkdir -p ros2_ws/src
git clone --recursive https://github.com/johnbaillieul/ROS_ML
git clone https://github.com/IntelRealSense/realsense-ros
cd ..
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug

```

In separate terminals run 
```
ros2 launch vbn_ml gazebo.launch.py
ros2 run vbn_ml optical_flow 1
ros2 run vbn_ml tau_computation
ros2 run vbn_ml controller 

```


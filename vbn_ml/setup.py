from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'vbn_ml'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name,'launch'), glob('launch/*')),
        (os.path.join('share', package_name,'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name,'models'), glob('models/**/**/**/*')),
        (os.path.join('share', package_name,'GazeboWorlds'), glob('GazeboWorlds/*')),
        (os.path.join('share', package_name,'images_with_colored_bkg'), glob('images_with_colored_bkg/**/*')),    
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='olagh',
    maintainer_email='olaghattas@hotmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'optical_flow = vbn_ml.optical_flow:main',
            'tau_computation = vbn_ml.tau_computation:main',
            'controller = vbn_ml.controller:main',
            'change_env = vbn_ml.change_box_color_in_env:main',
        ],
    },
)

"""
This demo script demonstrates the various functionalities of each controller available within robosuite (list of
supported controllers are shown at the bottom of this docstring).

For a given controller, runs through each dimension and executes a perturbation "test_value" from its
neutral (stationary) value for a certain amount of time "steps_per_action", and then returns to all neutral values
for time "steps_per_rest" before proceeding with the next action dim.

    E.g.: Given that the expected action space of the Pos / Ori (EE_POS_ORI) controller (without a gripper) is
    (dx, dy, dz, droll, dpitch, dyaw), the testing sequence of actions over time will be:

        ***START OF DEMO***
        ( dx,  0,  0,  0,  0,  0, grip)     <-- Translation in x-direction      for 'steps_per_action' steps
        (  0,  0,  0,  0,  0,  0, grip)     <-- No movement (pause)             for 'steps_per_rest' steps
        (  0, dy,  0,  0,  0,  0, grip)     <-- Translation in y-direction      for 'steps_per_action' steps
        (  0,  0,  0,  0,  0,  0, grip)     <-- No movement (pause)             for 'steps_per_rest' steps
        (  0,  0, dz,  0,  0,  0, grip)     <-- Translation in z-direction      for 'steps_per_action' steps
        (  0,  0,  0,  0,  0,  0, grip)     <-- No movement (pause)             for 'steps_per_rest' steps
        (  0,  0,  0, dr,  0,  0, grip)     <-- Rotation in roll (x) axis       for 'steps_per_action' steps
        (  0,  0,  0,  0,  0,  0, grip)     <-- No movement (pause)             for 'steps_per_rest' steps
        (  0,  0,  0,  0, dp,  0, grip)     <-- Rotation in pitch (y) axis      for 'steps_per_action' steps
        (  0,  0,  0,  0,  0,  0, grip)     <-- No movement (pause)             for 'steps_per_rest' steps
        (  0,  0,  0,  0,  0, dy, grip)     <-- Rotation in yaw (z) axis        for 'steps_per_action' steps
        (  0,  0,  0,  0,  0,  0, grip)     <-- No movement (pause)             for 'steps_per_rest' steps
        ***END OF DEMO***

    Thus the EE_POS_ORI controller should be expected to sequentially move linearly in the x direction first,
        then the y direction, then the z direction, and then begin sequentially rotating about its x-axis,
        then y-axis, then z-axis.

Please reference the controller README in the robosuite/controllers directory for an overview of each controller.
Controllers are expected to behave in a generally controlled manner, according to their control space. The expected
sequential qualitative behavior during the test is described below for each controller:

* EE_POS_ORI: Gripper moves sequentially and linearly in x, y, z direction, then sequentially rotates in x-axis, y-axis,
            z-axis, relative to the global coordinate frame
* EE_POS: Gripper moves sequentially and linearly in x, y, z direction, relative to the global coordinate frame
* EE_IK: Gripper moves sequentially and linearly in x, y, z direction, then sequentially rotates in x-axis, y-axis,
            z-axis, relative to the local robot end effector frame
* JOINT_IMP: Robot Joints move sequentially in a controlled fashion
* JOINT_VEL: Robot Joints move sequentially in a controlled fashion
* JOINT_TOR: Unlike other controllers, joint torque controller is expected to act rather lethargic, as the
            "controller" is really just a wrapper for direct torque control of the mujoco actuators. Therefore, a
            "neutral" value of 0 torque will not guarantee a stable robot when it has non-zero velocity!

"""


import numpy as np
from robosuite.controllers import load_controller_config
import robosuite.utils.transform_utils as T
from robosuite.utils.input_utils import *


if __name__ == "__main__":

    # Create dict to hold options that will be passed to env creation call
    options = {}

    # print welcome info
    print("Welcome to Surreal Robotics Suite v{}!".format(suite.__version__))
    print(suite.__logo__)

    # Choose environment and add it to options
    options["env_name"] = choose_environment()

    # If a multi-arm environment has been chosen, choose configuration and appropriate robot(s)
    if "TwoArm" in options["env_name"]:
        # Choose env config and add it to options
        options["env_configuration"] = choose_multi_arm_config()

        # If chosen configuration was bimanual, the corresponding robot must be Baxter. Else, have user choose robots
        if options["env_configuration"] == 'bimanual':
            options["robots"] = 'Baxter'
        else:
            options["robots"] = []

            # Have user choose two robots
            print("A multiple single-arm configuration was chosen.\n")

            for i in range(2):
                print("Please choose Robot {}...\n".format(i))
                options["robots"].append(choose_robots(exclude_bimanual=True))

    # Else, we simply choose a single (single-armed) robot to instantiate in the environment
    else:
        options["robots"] = choose_robots(exclude_bimanual=True)

    # Choose controller
    controller_name = choose_controller()

    # Load the desired controller
    options["controller_configs"] = load_controller_config(default_controller=controller_name)

    # Define the pre-defined controller actions to use (action_dim, num_test_steps, test_value, neutral control values)
    controller_settings = {
        "EE_POS_ORI": [7, 6, 0.1, np.array([0, 0, 0, 0, 0, 0, 0], dtype=float)],
        "EE_POS": [4, 3, 0.1, np.array([0, 0, 0, 0], dtype=float)],
        "EE_IK": [8, 6, 0.01, np.array([0, 0, 0, 0, 0, 0, 1, 0], dtype=float)],
        "JOINT_IMP": [8, 7, 0.2, np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=float)],
        "JOINT_VEL": [8, 7, -0.05, np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=float)],
        "JOINT_TOR": [8, 7, 0.001, np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=float)]
    }

    # Define variables for each controller test
    action_dim = controller_settings[controller_name][0]
    num_test_steps = controller_settings[controller_name][1]
    test_value = controller_settings[controller_name][2]
    neutral = controller_settings[controller_name][3]

    # Define the number of timesteps to use per controller action as well as timesteps in between actions
    steps_per_action = 50
    steps_per_rest = 250

    # Help message to user
    print()
    print("Press \"H\" to show the viewer control panel.")

    # initialize the task
    env = suite.make(
        **options,
        has_renderer=True,
        ignore_done=True,
        use_camera_obs=False,
        horizon=(steps_per_action + steps_per_rest) * num_test_steps,
        control_freq=20,
    )
    env.reset()
    env.viewer.set_camera(camera_id=0)

    # To accommodate for multi-arm settings (e.g.: Baxter), we need to make sure to fill any extra action space
    # Get total number of arms being controlled
    n = 0
    for robot in env.robots:
        n += int(robot.action_dim / action_dim)

    # Keep track of done variable to know when to break loop
    count = 0
    # Loop through controller space
    while count < num_test_steps:
        action = neutral.copy()
        for i in range(steps_per_action):
            if controller_name == 'EE_IK' and count > 2:
                # Convert from euler angle to quat here since we're working with quats
                angle = np.zeros(3)
                angle[count - 3] = test_value
                action[3:7] = T.mat2quat(T.euler2mat(angle))
            else:
                action[count] = test_value
            total_action = np.tile(action, n)
            env.step(total_action)
            env.render()
        for i in range(steps_per_rest):
            total_action = np.tile(neutral, n)
            env.step(total_action)
            env.render()
        count += 1

    # Shut down this env before starting the next test
    env.close()

from robosuite.renderers.mujoco.mujoco_py_renderer import MujocoPyRenderer
from robosuite.renderers.base import Renderer

class MujocoRenderer(Renderer):
    def __init__(self,
                 sim,
                 render_camera="frontview",
                 render_collision_mesh=False,
                 render_visual_mesh=True):
        
        self.sim = sim        
        self.render_camera = render_camera
        self.render_collision_mesh = render_collision_mesh
        self.render_visual_mesh = render_visual_mesh
        
        self.initialize_renderer()       

    def reset(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None

        self.initialize_renderer()

    def initialize_renderer(self):
        self.viewer = MujocoPyRenderer(self.sim)
        self.viewer.viewer.vopt.geomgroup[0] = (1 if self.render_collision_mesh else 0)
        self.viewer.viewer.vopt.geomgroup[1] = (1 if self.render_visual_mesh else 0)

        # hiding the overlay speeds up rendering significantly
        self.viewer.viewer._hide_overlay = True

        # make sure mujoco-py doesn't block rendering frames
        # (see https://github.com/StanfordVL/robosuite/issues/39)
        self.viewer.viewer._render_every_frame = True

        # Set the camera angle for viewing
        if self.render_camera is not None:
            self.viewer.set_camera(camera_id=self.sim.model.camera_name2id(self.render_camera)) 

    def update(self):
        pass

    def set_camera(self, camera_id):
        self.viewer.set_camera(camera_id=camera_id)

    def update_with_state(self, state):
        self.sim.set_state(state)
        self.sim.forward()

    def render(self):
        self.viewer.render()

    def close(self):
        self.viewer.close()
        self.viewer = None

    def add_keypress_callback(self, key, fn):
        """
        Allows for custom callback functions for the viewer. Called on key down.
        Parameter 'any' will ensure that the callback is called on any key down,
        and block default mujoco viewer callbacks from executing, except for
        the ESC callback to close the viewer.

        Args:
            key (int): keycode
            fn (function handle): function callback to associate with the keypress
        """
        self.viewer.add_keypress_callback(key, fn)

    def add_keyup_callback(self, key, fn):
        """
        Allows for custom callback functions for the viewer. Called on key up.
        Parameter 'any' will ensure that the callback is called on any key up,
        and block default mujoco viewer callbacks from executing, except for 
        the ESC callback to close the viewer.

        Args:
            key (int): keycode
            fn (function handle): function callback to associate with the keypress
        """
        self.viewer.add_keyup_callback(key, fn)

    def add_keyrepeat_callback(self, key, fn):
        """
        Allows for custom callback functions for the viewer. Called on key repeat.
        Parameter 'any' will ensure that the callback is called on any key repeat,
        and block default mujoco viewer callbacks from executing, except for 
        the ESC callback to close the viewer.

        Args:
            key (int): keycode
            fn (function handle): function callback to associate with the keypress
        """
        self.viewer.add_keyrepeat_callback(key, fn)
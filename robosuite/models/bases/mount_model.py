"""
Defines the FixedBaseModel class (Fixed Base that is mounted to the robot)
"""

from robosuite.models.bases.robot_base_model import RobotBaseModel


class FixedBaseModel(RobotBaseModel):
    @property
    def naming_prefix(self) -> str:
        return "fixed_mount{}_".format(self.idn)

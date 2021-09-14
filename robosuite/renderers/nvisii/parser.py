import numpy as np
import xml.etree.ElementTree as ET
from collections import namedtuple

import nvisii
from robosuite.utils.mjcf_utils import string_to_array
from robosuite.renderers.nvisii.nvisii_utils import load_object
from robosuite.renderers.base_parser import BaseParser

Components = namedtuple('Components', ['obj', 'parent_body_name', 'geom_pos', 'geom_quat', 'dynamic'])

class Parser(BaseParser):
    def __init__(self, env):
        """
        Parse the mujoco xml and initialize NViSII renderer objects.
        Args:
            env (Mujoco env): Environment to parse
        """

        self.env = env
        self.xml_root = ET.fromstring(self.env.mjpy_model.get_xml())      
        self.parent_map = {c:p for p in self.xml_root.iter() for c in p}
        self.visual_objects = {}
        self.components = {}

    def parse_textures(self):
        """
        Parse and load all textures and store them
        """

        self.texture_attributes = {}
        self.texture_id_mapping = {}

        for texture in self.xml_root.iter('texture'):
            texture_type = texture.get('type')
            texture_name = texture.get('name')
            texture_file = texture.get('file')
            texture_rgb = texture.get('rgb1')

            if texture_file is not None:
                self.texture_attributes[texture_name] = texture.attrib
            else:
                color = np.array(string_to_array(texture_rgb))
                self.texture_id_mapping[texture_name] = (color, texture_type)

    def parse_materials(self):
        """
        Parse all materials and use texture mapping to initialize materials
        """

        self.material_texture_mapping = {}
        for material in self.xml_root.iter('material'):
            material_name = material.get('name')
            texture_name = material.get('texture')
            self.material_texture_mapping[material_name] = texture_name

    def parse_meshes(self):
        """
        Create mapping of meshes.
        """
        self.meshes = {}
        for mesh in self.xml_root.iter('mesh'):
            self.meshes[mesh.get('name')] = mesh.attrib

    def parse_geometries(self):
        """
        Iterate through each goemetry and load it in the NViSII renderer.
        """
        self.parse_meshes()

        repeated_names = {}

        block_rendering_objects = ['VisualBread_g0', 'VisualCan_g0', 'VisualCereal_g0', 'VisualMilk_g0']

        for geom in self.xml_root.iter('geom'):
            
            parent_body = self.parent_map.get(geom)
            parent_body_name = parent_body.get('name', 'worldbody')

            geom_name = geom.get('name')
            geom_type = geom.get('type')

            rgba_str = geom.get('rgba')
            geom_rgba = string_to_array(rgba_str) if rgba_str is not None else None

            if geom_name is None:
                if parent_body_name in repeated_names:
                    geom_name = parent_body_name + str(repeated_names[parent_body_name])
                    repeated_names[parent_body_name] += 1
                else:
                    geom_name = parent_body_name + '0'
                    repeated_names[parent_body_name] = 1

            if 'floor' in geom_name or 'wall' in geom_name or geom_name in block_rendering_objects:
                continue

            if (geom.get('group') != '1' and geom_type != 'plane') or ('collision' in geom_name):
                continue

            geom_quat = string_to_array(geom.get('quat', '1 0 0 0'))
            geom_quat = [geom_quat[0], geom_quat[1], geom_quat[2], geom_quat[3]]

            # handling special case of bins arena
            if 'bin' in parent_body_name:
                geom_pos = string_to_array(geom.get('pos', "0 0 0")) + string_to_array(parent_body.get('pos', '0 0 0'))
            else:
                geom_pos = string_to_array(geom.get('pos', "0 0 0"))

            if geom_type == 'mesh':
                geom_scale = string_to_array(self.meshes[geom.get('mesh')].get('scale', '1 1 1'))
            else:
                geom_scale = [1, 1, 1]
            geom_size = string_to_array(geom.get('size', "1 1 1"))

            geom_mat = geom.get('material')

            tags = ['bin']
            dynamic = True
            if self.tag_in_name(geom_name, tags):
                dynamic = False

            geom_tex_name = None
            geom_tex_file = None

            if geom_mat is not None:
                geom_tex_name = self.material_texture_mapping[geom_mat]

                if geom_tex_name in self.texture_attributes:
                    geom_tex_file = self.texture_attributes[geom_tex_name]['file']

            # load obj into nvisii
            obj = load_object(geom=geom,
                              geom_name=geom_name,
                              geom_type=geom_type,
                              geom_quat=geom_quat,
                              geom_pos=geom_pos,
                              geom_size=geom_size,
                              geom_scale=geom_scale,
                              geom_rgba=geom_rgba,
                              geom_tex_name=geom_tex_name,
                              geom_tex_file=geom_tex_file,
                              meshes=self.meshes)

            self.components[geom_name] = Components(obj=obj,
                                                    parent_body_name=parent_body_name,
                                                    geom_pos=geom_pos,
                                                    geom_quat=geom_quat,
                                                    dynamic=dynamic)

    def tag_in_name(self, name, tags):
        """
        Checks if one of the tags in body tags in the name

        Args:
            name (str): Name of geom element.

            tags (array): List of keywords to check from.
        """
        for tag in tags:
            if tag in name:
                return True
        return False

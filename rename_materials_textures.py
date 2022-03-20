# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# This script is designed to rename packed images, but will generally rename all textures connected to a material node. Proceed with caution.
# TODO: Add checks for existing files and image names. Currently it overwrites existing files... I think.

bl_info = {
    "name": "Rename Materials and Textures",
    "author": "nikolajmunk",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "File > External Data",
    "description": "Renames materials and/or their assigned textures based on object names.",
    "warning": "",
    "doc_url": "",
    "category": "Material",
}

import bpy
import os

# functions


def print_begin(source):
    print('----------------------------------------')
    print(bl_info['name'] + ': Performing operation \'' + source + '\'.')


def main(context, rename_materials=False, rename_textures=False):
    filenumber_length = 2
    name_appendices = {'Base Color': 'BaseColor'}

    def filenumber_string(number, length, leading_underscore=True):
        filenumber = ''
        if number >= 0:
            filenumber = ('_' if leading_underscore else '') + str(number).zfill(length)
        return filenumber

    def get_appendix(node, appendices, leading_underscore='TRUE'):
        for link in n.outputs[0].links:
            output_name = link.to_socket.name
            if output_name in appendices:
                return ('_' if leading_underscore else '') + appendices[output_name]
        return ''

    def build_name(body, prefix='', appendix='', filenumber=-1):
        return prefix + body + appendix + filenumber_string(filenumber, filenumber_length)

    def rename_image(image, name, prefix='', appendix='', filenumber=-1):
        old_name = image.name
        new_name = build_name(body=name, prefix=prefix, appendix=appendix, filenumber=filenumber)

        path = os.path.split(n.image.filepath)
        extension = os.path.splitext(path[1])[1]
        new_filename = new_name + extension
        new_path = os.path.join(path[0], new_filename)

        image.name = new_name
        image.filepath = new_path
        print("Renamed image", old_name, "to", new_name)
        print("Changed file path to", new_path)
        print('')

    def rename_material(material, name, prefix='', appendix='', filenumber=-1):
        old_name = material.name
        new_name = build_name(body=name, prefix=prefix, appendix=appendix, filenumber=filenumber)

        material.name = new_name
        print("Renamed material", old_name, "to", new_name)
        print('')

    renamed_materials = []
    renamed_images = []
    for obj in context.selected_objects:
        material_count = 0
        for s in obj.material_slots:
            if s.material and s.material.use_nodes:
                print('Material name:', s.material.name)
                print('')
                if rename_materials:
                    rename_material(material=s.material, name=obj.name, filenumber=material_count)
                    renamed_materials.append(s.material)
                    material_count += 1
                misc_images = []
                for n in s.material.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and rename_textures:
                        appendix = get_appendix(n, name_appendices)
                        if appendix == '':
                            misc_images.append(n.image)
                        else:
                            rename_image(image=n.image, name=s.material.name, appendix=appendix)
                        i = 0
                        for image in misc_images:
                            rename_image(image=image, name=s.material.name, filenumber=i)
                            i += 1
                        renamed_images.append(n.image)

    print('Finished! Renamed', len(renamed_materials), 'materials and', len(renamed_images), 'textures.')
    print('----------------------------------------')

# classes


class RenameMaterial(bpy.types.Operator):
    """Rename materials in selected objects based on object name"""
    bl_idname = "file.rename_material"
    bl_label = "Rename Material(s)"

    @classmethod
    def poll(cls, context):
        return context.selected_objects is not None

    def execute(self, context):
        print_begin(self.bl_label)
        main(context, rename_materials=True)
        return {'FINISHED'}


class RenameTexture(bpy.types.Operator):
    """Rename textures in selected objects' materials based on material name"""
    bl_idname = "file.rename_texture"
    bl_label = "Rename Textures"

    @classmethod
    def poll(cls, context):
        return context.selected_objects is not None

    def execute(self, context):
        print_begin(self.bl_label)
        main(context, rename_textures=True)
        return {'FINISHED'}


class RenameMaterialAndTexture(bpy.types.Operator):
    """Rename materials in selected objects based on object name, then rename materials' textures based on material name"""
    bl_idname = "file.rename_material_texture"
    bl_label = "Rename Both Material(s) and Texture(s)"

    @classmethod
    def poll(cls, context):
        return context.selected_objects is not None

    def execute(self, context):
        print_begin(self.bl_label)
        main(context, rename_materials=True, rename_textures=True)
        return {'FINISHED'}


class RenameMaterialTextureMenu(bpy.types.Menu):
    bl_label = "Renaming Target Menu"
    bl_idname = "FILE_MT_rename_material_texture_menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator(RenameMaterialAndTexture.bl_idname, text=RenameMaterialAndTexture.bl_label, icon='WORLD_DATA')
        layout.operator(RenameMaterial.bl_idname, text=RenameMaterial.bl_label, icon='MATERIAL')
        layout.operator(RenameTexture.bl_idname, text=RenameTexture.bl_label, icon='TEXTURE')


def menu_func_showmenu(self, _context):
    self.layout.separator()
    self.layout.menu(RenameMaterialTextureMenu.bl_idname, text="Rename Materials/Textures")


classes = (
    RenameMaterial,
    RenameTexture,
    RenameMaterialAndTexture,
    RenameMaterialTextureMenu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_external_data.append(menu_func_showmenu)


def unregister():
    bpy.types.TOPBAR_MT_file_external_data.remove(menu_func_showmenu)
    for cls in classes:
        bpy.utils.unregister_class(cls)

# test call
if __name__ == "__main__":
    register()

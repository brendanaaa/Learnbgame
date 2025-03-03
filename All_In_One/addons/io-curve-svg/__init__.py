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

# <pep8 compliant>

bl_info = {
    "name": "Scalable Vector Graphics (SVG) 1.1 format",
    "description": "Import SVG as curves",
    "author": "JM Soler, Sergey Sharybin, Madlaina Kalunder",
    "version": (2, 0),
    "blender": (2, 79, 0),
    "location": "File > Import > Scalable Vector Graphics (.svg)",
    "warning": "Add-on in development",
    "wiki_url": "https://github.com/Aadjou/io-curve-svg",
    "support": 'COMMUNITY',
    "category": "Learnbgame",
}


# To support reload properly, try to access a package var,
# if it's there, reload everything
if "bpy" in locals():
    import importlib
    if "import_svg" in locals():
        importlib.reload(import_svg)


import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper


class ImportSVG(bpy.types.Operator, ImportHelper):
    """Load a SVG file"""
    bl_idname = "import_curve.svg"
    bl_label = "Import SVG"
    bl_options = {'UNDO'}

    filename_ext = ".svg"
    filter_glob = StringProperty(default="*.svg", options={'HIDDEN'})

    def execute(self, context):
        from . import import_svg

        return import_svg.load(self, context,
            **self.as_keywords(ignore=("filter_glob",)))


def menu_func_import(self, context):
    self.layout.operator(ImportSVG.bl_idname,
        text="Scalable Vector Graphics (.svg)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)

# NOTES
# - blender version is hardcoded

if __name__ == "__main__":
    register()

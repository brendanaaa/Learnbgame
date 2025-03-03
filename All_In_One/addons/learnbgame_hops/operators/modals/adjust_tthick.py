import bpy
import gpu
from bgl import *
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ... utils.blender_ui import get_dpi, get_dpi_factor
from ... graphics.drawing2d import draw_text, set_drawing_dpi, draw_box
from ... preferences import Hops_text_color, Hops_text2_color, Hops_border_color, Hops_border2_color, get_preferences


class HOPS_OT_AdjustTthickOperator(bpy.types.Operator):
    bl_idname = "hops.adjust_tthick"
    bl_label = "Adjust Tthick"
    bl_description = """Interactively and non destructively adds SOLIDIFY modifier
Press H for help."""
    bl_options = {"REGISTER", "UNDO", "GRAB_CURSOR", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return getattr(context.active_object, "type", "") == "MESH"

    def invoke(self, context, event):
        self.modal_scale = get_preferences().Hops_modal_scale
        self.objects = [obj for obj in context.selected_objects if obj.type=="MESH"]
        self.solidify_mods = {}
        self.solidify = self.get_solidify_modifier()
        self.start_mouse_position = Vector((event.mouse_region_x, event.mouse_region_y))
        self.last_mouse_x = event.mouse_region_x

        for obj in self.solidify_mods:
            mod = self.solidify_mods[obj]
            self.solidify_mods[obj]["start_solidify_thickness"] = self.solidify_mods[obj]["solidify"].thickness
            self.solidify_mods[obj]["start_solidify_offset"] = self.solidify_mods[obj]["solidify"].offset

        args = (context, )
        self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_ui, args, "WINDOW", "POST_PIXEL")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def get_solidify_modifier(self):
        objects = self.objects
        for obj in objects:
            if obj not in self.solidify_mods:
                self.solidify_mods.update({obj: {"solidify": None, "start_solidify_thickness": 0, "start_solidify_offset": 0, "solidify_offset": 0, "thickness_offset": 0, "created_solidify_modifier": False}}) 
            mods = obj.modifiers
            if "Solidify" in mods:
                self.solidify_mods[obj]["solidify"] = obj.modifiers["Solidify"]
                solidify_modifier = obj.modifiers["Solidify"]
            else:# if did not get one this iteration, create it
                solidify_modifier = obj.modifiers.new("Solidify", "SOLIDIFY")
                self.solidify_mods[obj]["solidify"] = solidify_modifier
                self.solidify_mods[obj]["created_solidify_modifier"] = True
            if get_preferences().force_thick_reset_solidify_init or self.solidify_mods[obj]["created_solidify_modifier"]:
                solidify_modifier.thickness = 0
                solidify_modifier.use_even_offset = True
                solidify_modifier.use_quality_normals = True
                solidify_modifier.use_rim_only = False
                solidify_modifier.show_on_cage = True

    def modal(self, context, event):
        divisor = 10000 * self.modal_scale if event.shift else 10000000 if event.ctrl else 1000 * self.modal_scale
        divisor_profile = 500 * self.modal_scale if event.ctrl else 100000000000
        offset_x = event.mouse_region_x - self.last_mouse_x

        for obj in self.solidify_mods:
            self.solidify = self.solidify_mods[obj]["solidify"]
            self.solidify_mods[obj]["thickness_offset"] -= offset_x / divisor / get_dpi_factor()
            self.solidify.thickness = self.solidify_mods[obj]["start_solidify_thickness"] - self.solidify_mods[obj]["thickness_offset"]
            self.solidify_mods[obj]["solidify_offset"] -= offset_x / divisor_profile / get_dpi_factor()

            if event.type == 'ONE' and event.value == 'PRESS':
                self.solidify.offset = -1
                self.solidify_mods[obj]["solidify_offset"] = 0

            if event.type == 'TWO' and event.value == 'PRESS':
                self.solidify.offset = 0
                self.solidify_mods[obj]["solidify_offset"] = -1

            if event.type == 'THREE' and event.value == 'PRESS':
                self.solidify.offset = 1
                self.solidify_mods[obj]["solidify_offset"] = -2

            if event.ctrl:
                self.solidify.offset = self.solidify_mods[obj]["start_solidify_offset"] - self.solidify_mods[obj]["solidify_offset"]

            if event.type == 'R' and event.value == 'PRESS':
                self.solidify.use_rim_only = not self.solidify.use_rim_only

        if event.type == "H" and event.value == "PRESS":
            get_preferences().hops_modal_help = not get_preferences().hops_modal_help

        if event.type in ("ESC", "RIGHTMOUSE"):
            self.reset_object()
            return self.finish()

        if event.type in ("SPACE", "LEFTMOUSE"):
            return self.finish()

        self.last_mouse_x = event.mouse_region_x
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def reset_object(self):
        for obj in self.solidify_mods:
            self.solidify = self.solidify_mods[obj]["solidify"]
            self.solidify.thickness = self.solidify_mods[obj]["start_solidify_thickness"]
            self.solidify.offset = self.solidify_mods[obj]["start_solidify_offset"]
            if self.solidify_mods[obj]["created_solidify_modifier"]:
                obj.modifiers.remove(self.solidify)

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, "WINDOW")
        return {"FINISHED"}

    def draw_ui(self, context):
        x, y = self.start_mouse_position
        solidify = self.solidify

        set_drawing_dpi(get_dpi())
        factor = get_dpi_factor()

        color_text1 = Hops_text_color()
        color_text2 = Hops_text2_color()
        color_border = Hops_border_color()
        color_border2 = Hops_border2_color()
        gap = 3 * factor
        vertices = (
            (x - 1 * factor, y + 23 * factor), (x - 1 * factor, y + 4 * factor), (x + 72 * factor, y + 23 * factor), (x + 72 * factor, y + 4 * factor),
            (x + 72 * factor + gap, y + 23 * factor), (x + 72 * factor + gap, y + 4 * factor), (x + 154 * factor, y + 23 * factor), (x + 154 * factor, y + 4 * factor),
            (x + 154 * factor + gap, y + 23 * factor), (x + 154 * factor + gap, y + 4 * factor), (x + 245 * factor, y + 23 * factor), (x + 245 * factor, y + 4 * factor))

        indices = (
            (0, 1, 2), (1, 2, 3), (4, 5, 6), (5, 6, 7), (8, 9, 10), (9, 10, 11))

        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

        shader.bind()
        shader.uniform_float("color", (0.17, 0.17, 0.17, 1))
        glEnable(GL_BLEND)
        batch.draw(shader)
        glDisable(GL_BLEND)

        draw_text("{:.3f}".format(self.solidify.thickness),
                  x + 27 * factor, y + 9 * factor, size=12, color=(0.831, 0.831, 0.831, 1))

        draw_text("Rim: {}".format(self.solidify.use_rim_only),
                  x + 90 * factor, y + 9 * factor, size=12, color=(0.831, 0.831, 0.831, 1))

        draw_text("Offset: {:.2f}".format(self.solidify.offset),
                  x + 168 * factor, y + 9 * factor, size=12, color=(0.831, 0.831, 0.831, 1))

        self.draw_help(context, x, y, factor)

    def draw(self, context):
        x, y = self.start_mouse_position
        solidify = self.solidify

        set_drawing_dpi(get_dpi())
        factor = get_dpi_factor()
        color_text1 = Hops_text_color()
        color_text2 = Hops_text2_color()
        color_border = Hops_border_color()
        color_border2 = Hops_border2_color()

        # front
        draw_box(x - 14 * factor, y + 8 * factor, 82 * factor, 34 * factor, color=color_border2)
        # back
        draw_box(x + 208 * factor, y + 8 * factor, 2 * factor, 34 * factor, color=color_border2)
        # top
        draw_box(x + 68 * factor, y + 24 * factor, 140 * factor, 2 * factor, color=color_border2)
        # bot
        draw_box(x + 68 * factor, y - 8 * factor, 140 * factor, 2 * factor, color=color_border2)
        # middle
        # draw_box(x -14 * factor, y + 8 * factor, 224 * factor , 34* factor, color = color_border2)
        draw_box(x + 68 * factor, y + 8 * factor, 140 * factor, 30 * factor, color=color_border)

        if solidify.thickness < 0:
            draw_text("{:.3f}".format(solidify.thickness), x - 12 * factor, y, size=23, color=color_text1)
        else:
            draw_text("{:.3f}".format(solidify.thickness), x - 4 * factor, y, size=23, color=color_text1)

        draw_text("Rim    -   {}".format(solidify.use_rim_only),
                  x + 70 * factor, y + 9 * factor, size=12, color=color_text2)

        draw_text("Offset -  {:.3f}".format(solidify.offset),
                  x + 70 * factor, y - 4 * factor, size=12, color=color_text2)

        if get_preferences().hops_modal_help:
            self.draw_help(context, x, y, factor)

    def draw_help(self, context, x, y, factor):

        color_text1 = Hops_text_color()
        color_text2 = Hops_text2_color()
        color_border = Hops_border_color()
        color_border2 = Hops_border2_color()

        if get_preferences().hops_modal_help:
            draw_text(" R - on/off rim",
                      x + 45 * factor, y - 14 * factor, size=11, color=color_text2)

            draw_text(" Ctrl - change offset instead",
                      x + 45 * factor, y - 26 * factor, size=11, color=color_text2)

            draw_text(" 1 - set offset to -1 ",
                      x + 45 * factor, y - 38 * factor, size=11, color=color_text2)

            draw_text(" 2 - set offset to 0 ",
                      x + 45 * factor, y - 50 * factor, size=11, color=color_text2)

            draw_text(" 3 - set offset to 1 ",
                      x + 45 * factor, y - 62 * factor, size=11, color=color_text2)

        else:
            draw_text(" H - Show/Hide Help",
                      x + 45 * factor, y - 14 * factor, size=11, color=color_text2)
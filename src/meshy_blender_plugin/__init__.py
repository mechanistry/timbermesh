bl_info = {
    "name": "Meshy Model Exporter",
    "description": "Exporting models as Meshy file",
    "author": "Mechanistry",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "version": (1, 0, 0),
}

import bpy
import sys
from os.path import dirname

sys.path.append(dirname(__file__))
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, path_reference_mode
from meshy_blender_plugin import meshy_exporter
from meshy_blender_plugin import blender_utils


class ExportCollection(Operator, ExportHelper):
    bl_idname = "export_collection.meshy"
    bl_label = "Export Collection"
    bl_options = {'PRESET'}

    filename_ext = ".meshy"
    use_filter_folder = False
    check_extension = True
    path_mode: path_reference_mode

    filter_glob: bpy.props.StringProperty(
        default="*.meshy;",
        options={'HIDDEN'},
    )

    merge_meshes: bpy.props.BoolProperty(
        name="Merge meshes",
        description="Merge matching meshes together",
        default=True
    )

    single_animation: bpy.props.BoolProperty(
        name="Single animation",
        description="Use scene frame range as single animation",
        default=True
    )

    use_vertex_animations: bpy.props.BoolProperty(
        name="Use vertex animations",
        description="Use vertex (VAT) animations where possible",
        default=False
    )

    def execute(self, context):
        selected_collections = blender_utils.get_selected_collections(context)
        settings = meshy_exporter.ExportSettings(context,
                                                 self.merge_meshes,
                                                 self.single_animation,
                                                 self.use_vertex_animations)
        meshy_exporter.Exporter.export_collection(selected_collections[0], self.filepath, settings)
        return {'FINISHED'}


class ExportCollections(Operator, ExportHelper):
    bl_idname = "export_collections.meshy"
    bl_label = "Export Collections"
    bl_options = {'PRESET'}
    filename_ext = "."
    use_filter_folder = True

    filter_folder = bpy.props.BoolProperty(
        default=True,
        options={'HIDDEN'}
    )

    directory: bpy.props.StringProperty(
        name="Export Directory",
        description="Choose the directory to export to",
        subtype='DIR_PATH',
        options={'HIDDEN'},
    )

    merge_meshes: bpy.props.BoolProperty(
        name="Merge meshes",
        description="Merge matching meshes together",
        default=True
    )

    single_animation: bpy.props.BoolProperty(
        name="Single animation",
        description="Use scene frame range as single animation",
        default=True
    )

    use_vertex_animations: bpy.props.BoolProperty(
        name="Use vertex animations",
        description="Use vertex (VAT) animations where possible",
        default=False
    )

    append_model_to_name: bpy.props.BoolProperty(
        name="Append 'Model' to name",
        description="Append 'Model' to the name of the exported model file",
        default=True
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        settings = meshy_exporter.ExportSettings(context,
                                                 self.merge_meshes,
                                                 self.single_animation,
                                                 self.use_vertex_animations)

        selected_collections = blender_utils.get_selected_collections(context)
        for collection in selected_collections:
            path = self.directory + "/" + collection.name + ".meshy"
            if self.append_model_to_name:
                path = path.replace(".meshy", ".Model.meshy")
            meshy_exporter.Exporter.export_collection(collection, path, settings)
        return {'FINISHED'}


class ExportCollectionMenu(bpy.types.Operator):
    bl_idname = "export_collection_menu.meshy"
    bl_label = "Export Collection"

    def execute(self, context):
        bpy.ops.export_collection.meshy('INVOKE_DEFAULT')
        return {'FINISHED'}


class ExportCollectionsMenu(bpy.types.Operator):
    bl_idname = "export_collections_menu.meshy"
    bl_label = "Export Collections"

    def execute(self, context):
        bpy.ops.export_collections.meshy('INVOKE_DEFAULT')
        return {'FINISHED'}


def draw_menu(self, context):
    layout = self.layout
    layout.separator()
    selected_collections = blender_utils.get_selected_collections(context)
    if len(selected_collections) > 1:
        layout.operator(ExportCollectionsMenu.bl_idname, text="Batch Export (*.meshy)")
    else:
        layout.operator(ExportCollectionMenu.bl_idname, text="Export (*.meshy)")


def register():
    bpy.utils.register_class(ExportCollection)
    bpy.utils.register_class(ExportCollections)
    bpy.utils.register_class(ExportCollectionMenu)
    bpy.utils.register_class(ExportCollectionsMenu)
    bpy.types.OUTLINER_MT_collection.append(draw_menu)


def unregister():
    bpy.utils.unregister_class(ExportCollection)
    bpy.utils.unregister_class(ExportCollections)
    bpy.utils.unregister_class(ExportCollectionMenu)
    bpy.utils.unregister_class(ExportCollectionsMenu)
    bpy.types.OUTLINER_MT_collection.remove(draw_menu)


if __name__ == "__main__":
    register()

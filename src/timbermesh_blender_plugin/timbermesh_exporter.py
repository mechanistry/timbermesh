import time
import zlib
import model_pb2
import blender_utils
import exporter_utils
from hierarchy import Hierarchy
from node_builder import NodeBuilder
from animation_builder import AnimationBuilder


class ExportSettings:
    def __init__(self, context, merge_meshes, single_animation, use_vertex_animations) -> None:
        self.context = context
        self.merge_meshes = merge_meshes
        self.single_animation = single_animation
        self.use_vertex_animations = use_vertex_animations


class Exporter:

    @classmethod
    def export_collection(cls, collection, path, settings) -> None:
        start_time = time.time()

        settings.context.scene.frame_set(0)
        objects_to_export = exporter_utils.get_exportable_objects(collection.all_objects)
        root_hierarchy_node = Hierarchy.create(objects_to_export, collection.name, settings.merge_meshes)
        timbermesh_model = cls.__create_model(root_hierarchy_node, settings)

        with open(path, "wb") as file:
            serialized_model = timbermesh_model.SerializeToString()
            file.write(zlib.compress(serialized_model))

        end_time = time.time()
        print("Export finished in", '{0:.2f}'.format(end_time - start_time), "seconds")

    @classmethod
    def __create_model(cls, hierarchy_node, settings) -> model_pb2.Model:
        timbermesh_model = model_pb2.Model()
        nodes = NodeBuilder.create_nodes(hierarchy_node, settings.context, timbermesh_model)
        cls.__create_animation(nodes, settings)
        return timbermesh_model

    @classmethod
    def __create_animation(cls, nodes, settings):
        animations, current_frame = blender_utils.get_current_scene_animations(settings.context)
        try:
            AnimationBuilder.create_animations(nodes, settings)
        finally:
            blender_utils.restore_scene_animations(settings.context, animations, current_frame)

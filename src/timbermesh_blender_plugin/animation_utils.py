import exporter_utils
import blender_types


def can_use_vertex_animations(node) -> bool:
    return len(node.vertices) > 0


def can_use_node_animations(node) -> bool:
    source_object = node.hierarchy_node.source_object
    return exporter_utils.is_root(node.name) and \
        source_object.type != blender_types.ARMATURE and \
        (__is_object_animated(source_object) or source_object.parent_type == blender_types.BONE)


def is_object_animated_in_hierarchy(obj):
    object_to_check = obj
    while object_to_check is not None:
        if __is_object_animated(object_to_check):
            return True
        object_to_check = object_to_check.parent

    return False


def is_any_object_animated_in_hierarchy(node):
    for obj in node.hierarchy_node.object_matrix_stack:
        if is_object_animated_in_hierarchy(obj):
            return True

    return False


def __is_object_animated(obj):
    return obj is not None and obj.animation_data is not None and obj.animation_data.action is not None

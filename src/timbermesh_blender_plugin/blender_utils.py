import bmesh
import bpy
import mathutils
from . import blender_types
from typing import List, Any


def triangulate_mesh_ngons(mesh) -> None:
    triangulation_mesh = bmesh.new()
    triangulation_mesh.from_mesh(mesh)
    ngon_faces = [face for face in triangulation_mesh.faces if len(face.verts) > 4]
    bmesh.ops.triangulate(triangulation_mesh, faces=ngon_faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    triangulation_mesh.to_mesh(mesh)
    triangulation_mesh.free()
    mesh.update()


def create_mesh(obj, matrix) -> bpy.types.Mesh:
    mesh = bpy.data.meshes.new_from_object(obj)
    mesh.transform(matrix)
    mesh.calc_loop_triangles()

    if __mesh_has_ngons(mesh):
        triangulate_mesh_ngons(mesh)
        mesh.calc_loop_triangles()

    # Calculate tangents from the first UV (same way as FBX does).
    if mesh.uv_layers:
        mesh.calc_tangents(uvmap=mesh.uv_layers[0].name)

    return mesh


def remove_mesh(mesh) -> None:
    if bpy.app.version < (4, 0, 0):
        mesh.free_normals_split()
    mesh.free_tangents()
    mesh.clear_geometry()
    bpy.data.meshes.remove(mesh)


def get_scene_frame_range(scene) -> list[int | Any]:
    return [scene.frame_start, scene.frame_end + 1]


def get_selected_collections(context) -> List[bpy.types.Collection]:
    # context.selected_ids exists only in the UI (outliner) context, so fall back
    # to the active collection when the exporter runs from a background script.
    selected_ids = getattr(context, "selected_ids", None)
    if selected_ids is not None:
        collections = [ids for ids in selected_ids if ids.bl_rna.identifier == "Collection"]
        if len(collections) > 0:
            return collections

    active_collection = getattr(context.view_layer, "active_layer_collection", None)
    if active_collection is not None:
        return [active_collection.collection]

    return []


def get_number_of_parents(obj) -> int:
    number_of_parents = 0
    parent = obj.parent
    while parent is not None:
        number_of_parents += 1
        parent = parent.parent

    return number_of_parents


def get_local_matrix(obj) -> mathutils.Matrix:
    if obj.parent and obj.parent.type == blender_types.ARMATURE and obj.parent_type == blender_types.BONE:
        matrix_relative_to_armature = obj.parent.matrix_world.inverted() @ obj.matrix_world
        return matrix_relative_to_armature
    else:
        return obj.matrix_local


def get_used_materials(objects) -> List[str]:
    materials = []
    for obj in objects:
        if obj.type == blender_types.MESH:
            if len(obj.material_slots) > 0:
                for polygon in obj.data.polygons:
                    material_slot = obj.material_slots[polygon.material_index]
                    material = material_slot.material
                    if material.name not in materials:
                        materials.append(material.name)
            elif "" not in materials:
                materials.append("")

    return materials


def get_current_scene_animations(context) -> dict[Any, Any]:
    animations = {}
    for obj in context.selectable_objects:
        if obj.type == blender_types.ARMATURE:
            animations[obj.name] = get_object_action(obj)

    return animations


def restore_scene_animations(context, animations) -> None:
    for obj in context.selectable_objects:
        if obj.type == blender_types.ARMATURE and obj.name in animations:
            set_object_action(obj, animations[obj.name][0], animations[obj.name][1])


def get_object_action(obj) -> tuple[Any, Any]:
    # Since Blender 4.4 an action is evaluated through its slot, so both have to be
    # remembered to restore the animation state of an object.
    animation_data = obj.animation_data
    if animation_data is None:
        return None, None

    return animation_data.action, get_action_slot(animation_data)


def set_object_action(obj, action, action_slot=None) -> None:
    animation_data = obj.animation_data
    if animation_data is None:
        if action is None:
            return
        animation_data = obj.animation_data_create()

    animation_data.action = action
    if action is None:
        set_action_slot(animation_data, None)
    elif action_slot is not None:
        set_action_slot(animation_data, action_slot)
    else:
        select_action_slot(animation_data, obj)


def get_action_slot(animation_data) -> Any:
    action_slot = getattr(animation_data, "action_slot", None)
    return action_slot


def set_action_slot(animation_data, action_slot) -> None:
    if hasattr(animation_data, "action_slot"):
        animation_data.action_slot = action_slot


def select_action_slot(animation_data, obj) -> None:
    # Point the animation at a slot of the action that is assigned to this object.
    # Without it Blender keeps evaluating whatever slot was active before.
    if not hasattr(animation_data, "action_slot"):
        return

    suitable_slots = list(animation_data.action_suitable_slots)
    if len(suitable_slots) == 0:
        animation_data.action_slot = None
        return

    # A single action can hold the animation of several objects, each in its own
    # slot, so look for the slot created for this object before using the first one.
    for slot in suitable_slots:
        if slot.name_display == obj.name or slot.identifier in (obj.name, "OB" + obj.name):
            animation_data.action_slot = slot
            return

    animation_data.action_slot = suitable_slots[0]


def __mesh_has_ngons(mesh) -> bool:
    for poly in mesh.polygons:
        if len(poly.vertices) > 4:
            return True

    return False

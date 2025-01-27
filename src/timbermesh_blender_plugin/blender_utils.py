import bmesh
import bpy
import mathutils
import blender_types
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
    return [ids for ids in context.selected_ids if ids.bl_rna.identifier == "Collection"]


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


def get_current_scene_animations(context) -> tuple[dict[Any, Any], Any]:
    animations = {}
    for obj in context.selectable_objects:
        if obj.type == blender_types.ARMATURE:
            animations[obj.name] = obj.animation_data.action

    return animations, context.scene.frame_current


def restore_scene_animations(context, animations, current_frame) -> None:
    for obj in context.selectable_objects:
        if obj.type == blender_types.ARMATURE:
            obj.animation_data.action = animations[obj.name]

    context.scene.frame_set(current_frame)


def __mesh_has_ngons(mesh) -> bool:
    for poly in mesh.polygons:
        if len(poly.vertices) > 4:
            return True

    return False

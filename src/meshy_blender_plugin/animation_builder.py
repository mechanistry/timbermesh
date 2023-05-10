import bpy
import mathutils
import animation_utils
import blender_utils
import blender_types
import vertex_properties_utils


class AnimationBuilder:

    @classmethod
    def create_animations(cls, nodes, settings) -> None:
        if settings.single_animation:
            action = None
            try:
                action = bpy.data.actions.new("Default")
                action.frame_range = blender_utils.get_scene_frame_range(settings.context.scene)
                cls.__save_animation(action, nodes, settings)
            finally:
                if action is not None:
                    bpy.data.actions.remove(action)

        else:
            for action in bpy.data.actions:
                cls.__set_action_to_all_armatures(action, settings)
                cls.__save_animation(action, nodes, settings)

    @classmethod
    def __set_action_to_all_armatures(cls, action, settings) -> None:
        for obj in settings.context.selectable_objects:
            if obj.type == blender_types.ARMATURE:
                obj.animation_data.action = action

    @classmethod
    def __save_animation(cls, action, nodes, settings) -> None:
        context = settings.context
        frame_range = action.frame_range

        vertex_animations = {}
        node_animations = {}
        for node in nodes:
            if not animation_utils.is_any_object_animated_in_hierarchy(node):
                continue

            if settings.use_vertex_animations and animation_utils.can_use_vertex_animations(node):
                vertex_animation = node.meshy_node.vertexAnimations.add()
                vertex_animation.name = action.name
                vertex_animation.framerate = context.scene.render.fps
                vertex_animation.animatedVertexCount = node.animated_vertex_count
                vertex_animations[node] = vertex_animation
            elif animation_utils.can_use_node_animations(node):
                node_animation = node.meshy_node.nodeAnimations.add()
                node_animation.name = action.name
                node_animation.framerate = context.scene.render.fps
                node_animations[node] = node_animation

        if not vertex_animations and not node_animations:
            return

        print("Saving animation", action.name, "from frame", str(frame_range.x), "to", str(frame_range.y - 1))
        for frame_index in range(int(frame_range.x), int(frame_range.y), 1):
            context.scene.frame_set(frame_index)
            depsgraph = context.evaluated_depsgraph_get()

            for node, animation in vertex_animations.items():
                cls.__save_vertex_animation_frame(node, animation, depsgraph)
            for node, animation in node_animations.items():
                cls.__save_node_animation_frame(node, animation, depsgraph)

    @classmethod
    def __save_vertex_animation_frame(cls, node, vertex_animation, depsgraph) -> None:
        vertex_offsets = []
        vertex_rotations = []

        for obj in node.mesh_objects:
            cls.__save_vertex_animation_vertices(node, depsgraph, obj, vertex_offsets, vertex_rotations)

        vertex_animation_frame = vertex_animation.frames.add()

        vertex_offsets_properties = vertex_properties_utils.create_vector3(vertex_offsets, "offset")
        vertex_rotations_properties = vertex_properties_utils.create_vector4(vertex_rotations, "rotation")
        vertex_animation_frame.vertexProperties.append(vertex_offsets_properties)
        vertex_animation_frame.vertexProperties.append(vertex_rotations_properties)

    @classmethod
    def __save_vertex_animation_vertices(cls, node, depsgraph, obj, vertex_offsets, vertex_rotations) -> None:
        frame_mesh = None
        try:
            evaluated_object = obj.evaluated_get(depsgraph)
            frame_mesh = blender_utils.create_mesh(evaluated_object, obj.matrix_world)

            original_world_matrix_inverted = node.original_object_meshes[obj.name].world_matrix_inverted
            original_node_matrix = node.original_object_meshes[obj.name].node_matrix
            original_vertices = node.original_object_meshes[obj.name].vertices

            transformation_matrix = original_node_matrix @ original_world_matrix_inverted
            transformation_matrix_rotation = transformation_matrix.to_quaternion()
            vertex_rotation_matrix = mathutils.Matrix.Identity(3)

            vertex_counter = 0
            for original_vertex in original_vertices:
                if vertex_counter < node.animated_vertex_count:
                    vertex_counter += 1
                    loop_index = original_vertex.source_loop_index
                    loop = frame_mesh.loops[loop_index]
                    frame_vertex = frame_mesh.vertices[original_vertex.source_index]

                    position_in_node_space = transformation_matrix @ frame_vertex.co
                    vertex_offset = position_in_node_space - original_vertex.position

                    vertex_normal = transformation_matrix_rotation @ loop.normal
                    vertex_tangent = transformation_matrix_rotation @ loop.tangent
                    vertex_bitangent = vertex_normal.cross(vertex_tangent)

                    vertex_rotation_matrix.col[0] = vertex_normal
                    vertex_rotation_matrix.col[1] = vertex_tangent
                    vertex_rotation_matrix.col[2] = vertex_bitangent
                    vertex_rotation_quaternion = vertex_rotation_matrix.to_quaternion()

                    vertex_offsets.append(mathutils.Vector((-vertex_offset.x, vertex_offset.z, -vertex_offset.y)))
                    vertex_rotations.append(
                        mathutils.Vector((vertex_rotation_quaternion.x, -vertex_rotation_quaternion.z,
                                          vertex_rotation_quaternion.y, vertex_rotation_quaternion.w)))
        finally:
            if frame_mesh is not None:
                blender_utils.remove_mesh(frame_mesh)

    @classmethod
    def __save_node_animation_frame(cls, node, node_animation, depsgraph) -> None:
        node_animation_frame = node_animation.frames.add()
        source_object = node.hierarchy_node.source_object
        evaluated_object = source_object.evaluated_get(depsgraph)

        local_matrix = blender_utils.get_local_matrix(evaluated_object)
        object_position = local_matrix.to_translation()
        object_rotation = local_matrix.to_quaternion()
        object_scale = local_matrix.to_scale()

        node_animation_frame.position.x = -object_position.x
        node_animation_frame.position.y = object_position.z
        node_animation_frame.position.z = -object_position.y

        node_animation_frame.rotation.x = object_rotation.x
        node_animation_frame.rotation.y = -object_rotation.z
        node_animation_frame.rotation.z = object_rotation.y
        node_animation_frame.rotation.w = object_rotation.w

        node_animation_frame.scale.x = object_scale.x
        node_animation_frame.scale.y = object_scale.z
        node_animation_frame.scale.z = object_scale.y

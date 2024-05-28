import mathutils
import itertools
import animation_utils
import blender_utils
import blender_types
import vertex_properties_utils
import exporter_utils


class MeshVertex:
    def __init__(self, index, source_index, source_loop_index, position, normal, tangent, uv0, uv1, uv2, color):
        self.index = index
        self.source_index = source_index
        self.source_loop_index = source_loop_index
        self.position = position
        self.normal = normal
        self.tangent = tangent
        self.uv0 = uv0
        self.uv1 = uv1
        self.uv2 = uv2
        self.color = color

    def is_replaceable_by(self, other) -> bool:
        return self.source_index == other.source_index \
            and self.normal == other.normal \
            and self.tangent == other.tangent \
            and self.uv0 == other.uv0 \
            and self.uv1 == other.uv1 \
            and self.uv2 == other.uv2 \
            and self.color == other.color


class OriginalMesh:
    def __init__(self):
        self.node_matrix = []
        self.world_matrix_inverted = []
        self.vertices = []


class Mesh:
    def __init__(self):
        self.name = ""
        self.indices = []


class Node:
    def __init__(self):
        self.name = ""
        self.parent = None
        self.hierarchy_node = None
        self.mesh_objects = []
        self.timbermesh_node = None
        self.meshes = []
        self.vertices = []
        self.original_object_meshes = {}
        self.animated_vertex_count = 0
        self.has_colors = False
        self.has_uv0 = False
        self.has_uv1 = False
        self.has_uv2 = False


class NodeBuilder:

    @classmethod
    def create_nodes(cls, root_hierarchy_node, context, timbermesh_model) -> list:
        nodes = []
        cls.__create_node(context, root_hierarchy_node, nodes)
        cls.__save_nodes(nodes, timbermesh_model)
        return nodes

    @classmethod
    def __create_node(cls, context, hierarchy_node, created_nodes) -> Node:
        node = Node()
        node.name = hierarchy_node.name
        node.hierarchy_node = hierarchy_node
        created_nodes.append(node)

        cls.__create_node_mesh(context, node)

        for child_node in hierarchy_node.children:
            child_node = cls.__create_node(context, child_node, created_nodes)
            child_node.parent = node

        return node

    @classmethod
    def __create_node_mesh(cls, context, node) -> None:
        cls.__create_empty_meshes(node, node.hierarchy_node.object_matrix_stack.keys())
        objects_sorted_by_animation = sorted(node.hierarchy_node.object_matrix_stack,
                                             key=lambda x: not animation_utils.is_object_animated_in_hierarchy(x))

        for obj in objects_sorted_by_animation:
            if obj.type == blender_types.MESH and len(obj.data.vertices) > 0:
                depsgraph = context.evaluated_depsgraph_get()
                evaluated_object = obj.evaluated_get(depsgraph)
                object_matrix = node.hierarchy_node.get_object_matrix(obj)
                node.original_object_meshes[obj.name] = OriginalMesh()
                node.original_object_meshes[obj.name].node_matrix = object_matrix.copy()
                node.original_object_meshes[obj.name].world_matrix_inverted = obj.matrix_world.inverted().copy()
                node.mesh_objects.append(obj)
                cls.__update_node_vertices(node, evaluated_object, object_matrix)
                if animation_utils.is_object_animated_in_hierarchy(obj):
                    node.animated_vertex_count += len(node.original_object_meshes[obj.name].vertices)

    @classmethod
    def __create_empty_meshes(cls, node, objects) -> None:
        used_materials = blender_utils.get_used_materials(objects)
        for used_material in used_materials:
            mesh = Mesh()
            mesh.material = used_material
            node.meshes.append(mesh)

    @classmethod
    def __update_node_vertices(cls, node, obj, matrix) -> None:
        created_mesh = None
        try:
            created_mesh = blender_utils.create_mesh(obj, matrix)
            has_colors, has_uv0, has_uv1, has_uv2 = cls.__get_mesh_layers(created_mesh)
            node.has_colors = node.has_colors or has_colors
            node.has_uv0 = node.has_uv0 or has_uv0
            node.has_uv1 = node.has_uv1 or has_uv1
            node.has_uv2 = node.has_uv2 or has_uv2

            vertex_index = len(node.vertices)
            created_vertex_map = {}
            for vertex in created_mesh.vertices:
                created_vertex_map[vertex.index] = []

            sorted_triangles = sorted(created_mesh.loop_triangles, key=lambda x: x.material_index)
            for material_index, triangles in itertools.groupby(sorted_triangles, lambda x: x.material_index):
                triangle_list = list(triangles)

                if len(obj.material_slots) > 0:
                    material_name = obj.material_slots[material_index].material.name
                else:
                    material_name = ""
                mesh = next((m for m in node.meshes if m.material == material_name), None)

                for triangle in triangle_list:
                    for i in reversed(range(3)):
                        loop_index = triangle.loops[i]
                        original_vertex_index = triangle.vertices[i]
                        original_vertex = created_mesh.vertices[original_vertex_index]
                        position = original_vertex.co.copy()
                        normal = created_mesh.loops[loop_index].normal.copy()
                        tangent = created_mesh.loops[loop_index].tangent.copy()
                        bitangent_sign = created_mesh.loops[loop_index].bitangent_sign

                        if has_uv0:
                            uv0 = created_mesh.uv_layers[0].data[loop_index].uv.copy()
                        else:
                            uv0 = mathutils.Vector((0, 0))

                        if has_uv1:
                            uv1 = created_mesh.uv_layers[1].data[loop_index].uv.copy()
                        else:
                            uv1 = mathutils.Vector((0, 0))

                        if has_uv2:
                            uv2 = created_mesh.uv_layers[2].data[loop_index].uv.copy()
                        else:
                            uv2 = mathutils.Vector((0, 0))

                        if has_colors:
                            loop_color = created_mesh.vertex_colors[0].data[loop_index].color
                            color = [loop_color[0], loop_color[1], loop_color[2], loop_color[3]]
                        else:
                            color = [1, 1, 1, 1]

                        new_vertex = MeshVertex(vertex_index,
                                                original_vertex_index,
                                                loop_index,
                                                position,
                                                normal,
                                                [tangent.x, tangent.y, tangent.z, bitangent_sign],
                                                uv0,
                                                uv1,
                                                uv2,
                                                color)

                        existing_equal_vertex = next(
                            (v for v in created_vertex_map[original_vertex_index] if v.is_replaceable_by(new_vertex)),
                            None)
                        if existing_equal_vertex is None:
                            created_vertex_map[original_vertex_index].append(new_vertex)
                            node.vertices.append(new_vertex)
                            node.original_object_meshes[obj.name].vertices.append(new_vertex)
                            mesh.indices.append(vertex_index)
                            vertex_index += 1
                        else:
                            mesh.indices.append(existing_equal_vertex.index)
        finally:
            if created_mesh is not None:
                blender_utils.remove_mesh(created_mesh)

    @classmethod
    def __get_mesh_layers(cls, source_mesh) -> (bool, bool, bool, bool):
        has_colors = len(source_mesh.vertex_colors) > 0
        has_uv0 = len(source_mesh.uv_layers) > 0
        has_uv1 = len(source_mesh.uv_layers) > 1
        has_uv2 = len(source_mesh.uv_layers) > 2
        return has_colors, has_uv0, has_uv1, has_uv2

    @classmethod
    def __save_nodes(cls, nodes, timbermesh_model) -> None:
        for node in nodes:
            timbermesh_node = timbermesh_model.nodes.add()
            timbermesh_node.name = node.name
            timbermesh_node.parent = nodes.index(node.parent) if node.parent is not None else -1
            node.timbermesh_node = timbermesh_node

            source_object = node.hierarchy_node.source_object
            object_transform_matrix = mathutils.Matrix.Identity(4)
            if node.hierarchy_node.source_object is not None:
                object_transform_matrix = blender_utils.get_local_matrix(source_object)
            cls.__save_node_transform(timbermesh_node, object_transform_matrix)
            cls.__save_node_vertex_properties(timbermesh_node, node)
            cls.__save_node_meshes(timbermesh_node, node)

    @classmethod
    def __save_node_transform(cls, timbermesh_node, matrix) -> None:
        position = matrix.to_translation()
        rotation = matrix.to_quaternion()
        scale = matrix.to_scale()

        timbermesh_node.position.x = -position.x
        timbermesh_node.position.y = position.z
        timbermesh_node.position.z = -position.y

        timbermesh_node.rotation.x = rotation.x
        timbermesh_node.rotation.y = -rotation.z
        timbermesh_node.rotation.z = rotation.y
        timbermesh_node.rotation.w = rotation.w

        timbermesh_node.scale.x = scale.x
        timbermesh_node.scale.y = scale.z
        timbermesh_node.scale.z = scale.y

    @classmethod
    def __save_node_vertex_properties(cls, timbermesh_node, node) -> None:
        sorted_vertices = sorted(node.vertices, key=lambda v: v.index)
        positions = []
        normals = []
        tangents = []
        colors = []
        uv0 = []
        uv1 = []
        uv2 = []

        for vertex in sorted_vertices:
            positions.append(mathutils.Vector((-vertex.position.x, vertex.position.z, -vertex.position.y)))
            normals.append(mathutils.Vector((-vertex.normal.x, vertex.normal.z, -vertex.normal.y)))
            tangents.append(
                mathutils.Vector((-vertex.tangent[0], vertex.tangent[2], -vertex.tangent[1], -vertex.tangent[3])))

            if node.has_colors:
                colors.append(mathutils.Vector((vertex.color[0], vertex.color[1], vertex.color[2], vertex.color[3])))
            if node.has_uv0:
                uv0.append(mathutils.Vector((vertex.uv0.x, vertex.uv0.y)))
            if node.has_uv1:
                uv1.append(mathutils.Vector((vertex.uv1.x, vertex.uv1.y)))
            if node.has_uv2:
                uv2.append(mathutils.Vector((vertex.uv2.x, vertex.uv2.y)))

        timbermesh_node.vertexCount = len(sorted_vertices)
        timbermesh_node.vertexProperties.append(vertex_properties_utils.create_vector3(positions, "position"))
        timbermesh_node.vertexProperties.append(vertex_properties_utils.create_vector3(normals, "normal"))
        timbermesh_node.vertexProperties.append(vertex_properties_utils.create_vector4(tangents, "tangent"))

        if node.has_colors:
            timbermesh_node.vertexProperties.append(vertex_properties_utils.create_vector4(colors, "color"))
        if node.has_uv0:
            timbermesh_node.vertexProperties.append(vertex_properties_utils.create_vector2(uv0, "uv0"))
        if node.has_uv1:
            timbermesh_node.vertexProperties.append(vertex_properties_utils.create_vector2(uv1, "uv1"))
        if node.has_uv2:
            timbermesh_node.vertexProperties.append(vertex_properties_utils.create_vector2(uv2, "uv2"))

    @classmethod
    def __save_node_meshes(cls, timbermesh_node, node) -> None:
        for mesh in node.meshes:
            timbermesh_mesh = timbermesh_node.meshes.add()
            timbermesh_mesh.material = mesh.material
            for index in mesh.indices:
                timbermesh_mesh.indices.append(index)

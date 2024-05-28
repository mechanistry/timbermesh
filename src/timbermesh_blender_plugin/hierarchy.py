import exporter_utils
import blender_utils
import mathutils


class HierarchyNode:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.children = []
        self.source_object = None
        self.object_matrix_stack = {}

    def get_object_matrix(self, obj) -> mathutils.Matrix:
        matrix = mathutils.Matrix.Identity(4)
        object_stack = self.object_matrix_stack[obj]
        for stack_object in object_stack:
            matrix = matrix.copy() @ blender_utils.get_local_matrix(stack_object)
        return matrix


class HierarchyBuildingContext:
    def __init__(self, allowed_objects):
        self.allowed_objects = allowed_objects.copy()
        self.visited_objects = []
        self.created_nodes = []


class Hierarchy:

    @classmethod
    def create(cls, objects, name, merge_objects) -> HierarchyNode:
        matrix_stack = []
        context = HierarchyBuildingContext(objects)
        root_node = HierarchyNode(name, None)

        cls.__create_hierarchy_tree(objects, context, matrix_stack, root_node, merge_objects)
        cls.__remove_empty_nodes(context)

        return root_node

    @classmethod
    def __create_hierarchy_tree(cls, objects, context, matrix_stack, root_node, merge_objects) -> None:
        for obj in objects:
            cls.__visit_object(obj, context, matrix_stack, root_node, root_node, merge_objects)

    @classmethod
    def __remove_empty_nodes(cls, context) -> None:
        for node in context.created_nodes:
            if node.parent is not None and not node.children and not node.object_matrix_stack:
                node.parent.children.remove(node)

    @classmethod
    def __visit_object(cls, obj, context, matrix_stack, node, parent_node, merge_objects) -> None:
        if obj.name not in context.visited_objects and obj in context.allowed_objects:
            context.visited_objects.append(obj.name)
            # If object merging is disabled or object is a "root" object - we need to create a new node.
            # Otherwise we can use the same node to store object (e.g. to join meshes together).
            if exporter_utils.is_root(obj.name) or not merge_objects:
                matrix_stack = []
                cls.__visit_root_object(obj, context, matrix_stack, parent_node, merge_objects)
            else:
                matrix_stack = list(matrix_stack)
                matrix_stack.append(obj)
                cls.__visit_same_level_object(obj, context, matrix_stack, parent_node, node, False, merge_objects)

    @classmethod
    def __visit_root_object(cls, obj, context, object_stack, parent_node, merge_objects) -> None:
        node = cls.__create_node(obj, context, parent_node)
        cls.__visit_same_level_object(obj, context, object_stack, node, node, True, merge_objects)

    @classmethod
    def __visit_same_level_object(cls, obj, context, matrix_stack, parent_node, node, is_root, merge_objects) -> None:
        node.object_matrix_stack[obj] = matrix_stack.copy()
        if len(obj.children) > 0:
            if not is_root:
                parent_node = cls.__create_node(obj, context, parent_node)

            for child in obj.children:
                cls.__visit_object(child, context, matrix_stack, node, parent_node, merge_objects)

    @classmethod
    def __create_node(cls, obj, context, parent_node) -> HierarchyNode:
        node = HierarchyNode(obj.name, parent_node)
        node.source_object = obj
        parent_node.children.append(node)
        context.created_nodes.append(node)
        return node

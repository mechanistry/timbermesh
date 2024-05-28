import blender_utils
import blender_types


def get_exportable_objects(objects) -> list:
    objects_to_export = list(objects)
    for obj in objects:
        if obj.parent and obj.parent not in objects_to_export:
            objects_to_export.append(obj.parent)

    objects_to_export = [obj for obj in objects_to_export if
                         obj.type in [blender_types.MESH, blender_types.EMPTY]]
    return sorted(objects_to_export, key=lambda o: blender_utils.get_number_of_parents(o))


def is_root(name) -> bool:
    return name.startswith("#")

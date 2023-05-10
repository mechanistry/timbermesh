import struct
import model_pb2


def pack_vector2f_array(source_array, target_bytearray) -> None:
    for item in source_array:
        target_bytearray += bytearray(struct.pack('<f', item.x))
        target_bytearray += bytearray(struct.pack('<f', item.y))


def pack_vector3f_array(source_array, target_bytearray) -> None:
    for item in source_array:
        target_bytearray += bytearray(struct.pack('<f', item.x))
        target_bytearray += bytearray(struct.pack('<f', item.y))
        target_bytearray += bytearray(struct.pack('<f', item.z))


def pack_vector4f_array(source_array, target_bytearray) -> None:
    for item in source_array:
        target_bytearray += bytearray(struct.pack('<f', item.x))
        target_bytearray += bytearray(struct.pack('<f', item.y))
        target_bytearray += bytearray(struct.pack('<f', item.z))
        target_bytearray += bytearray(struct.pack('<f', item.w))


def create_vector2(source_array, name) -> model_pb2.VertexProperty:
    target_bytearray = bytearray()
    pack_vector2f_array(source_array, target_bytearray)
    return create(target_bytearray, name, model_pb2.ScalarType.SCALAR_TYPE_FLOAT, 2)


def create_vector3(source_array, name) -> model_pb2.VertexProperty:
    target_bytearray = bytearray()
    pack_vector3f_array(source_array, target_bytearray)
    return create(target_bytearray, name, model_pb2.ScalarType.SCALAR_TYPE_FLOAT, 3)


def create_vector4(source_array, name) -> model_pb2.VertexProperty:
    target_bytearray = bytearray()
    pack_vector4f_array(source_array, target_bytearray)
    return create(target_bytearray, name, model_pb2.ScalarType.SCALAR_TYPE_FLOAT, 4)


def create(target_bytearray, name, scalar_type, scalar_type_dimension) -> model_pb2.VertexProperty:
    container = model_pb2.VertexProperty()
    container.name = name
    container.scalarType = scalar_type
    container.scalarTypeDimension = scalar_type_dimension
    container.data = bytes(target_bytearray)
    return container

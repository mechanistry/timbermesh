### Rename note
Meshy has been renamed into Timbermesh, along with the change of the file format to ".timbermesh". Timberborn will use the new format starting with version 0.6.0.0 (also known as Update 6), although the ".meshy" extension will continue to be supported for some time. If you want to make a mod for an older version of the game, use release 1.0.0.

# Timbermesh
Timbermesh is an open-source 3D file format that allows for storage of geometry (mesh) information usable in various 3D software. It was created with the primary goal of simplifying animation pipeline and improving performance in the Unity game engine. It allows to take advantage of VAT (Vertex Animation Texture) animations that can replace existing animation implementations, increasing rendering performance and simplifying model creation process. Due to its open nature (based on Google Protocol Buffers) and serialization structure, Timbermesh allows for an easy integration not only with Unity, but also other 3D engines, design software and various tools. During **Timberborn** game development Timbermesh proved to be an effective and performant solution - more about that can be found [here](https://github.com/mechanistry/timbermesh/wiki/How-we-use-Timbermesh-in-Timberborn).

### Details

Overview of the Timbermesh file format can be found here:\
[https://github.com/mechanistry/timbermesh/wiki/Timbermesh-overview](https://github.com/mechanistry/timbermesh/wiki/Timbermesh-overview)

### Plugins

There's a Blender plugin that allows to export models to Timbermesh format. \
Latest release can be found here: [https://github.com/mechanistry/timbermesh/releases](https://github.com/mechanistry/timbermesh/releases) \
Plugin manual is available here: [https://github.com/mechanistry/timbermesh/wiki/Timbermesh-Blender-Plugin-manual](https://github.com/mechanistry/timbermesh/wiki/Timbermesh-Blender-Plugin-manual)

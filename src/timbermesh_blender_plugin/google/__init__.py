# Makes the vendored protobuf a private sub-package of this plugin, so it is
# imported as <add-on>.google.protobuf instead of as the top level "google"
# package. Upstream ships "google" as a namespace package; declaring it here
# keeps the dependency inside the plug-in's own namespace, which is what the
# Blender extension policy requires (no extra sys.path entries, no top level
# modules of its own).

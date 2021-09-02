import sendwave.pants_node.package as package
import sendwave.pants_node.target as target


def rules():
    return [
        *package.rules(),
        *target.rules(),
    ]


def target_types():
    return [target.NodeLibrary, target.NodePackage]

import logging
from dataclasses import dataclass
from pathlib import PurePath

from pants.core.goals.package import BuiltPackage, BuiltPackageArtifact
from pants.core.util_rules.external_tool import (DownloadedExternalTool,
                                                 ExternalToolRequest)
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.engine.environment import Environment, EnvironmentRequest
from pants.engine.fs import (AddPrefix, Digest, FileContent, MergeDigests,
                             PathGlobs, RemovePrefix, Snapshot)
from pants.engine.platform import Platform
from pants.engine.process import (BinaryPathRequest, BinaryPaths, Process,
                                  ProcessResult)
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.target import (Target, TransitiveTargets,
                                 TransitiveTargetsRequest)
from pants.engine.unions import UnionMembership, UnionRule
from .target import NodeLibrary, NodeLibrarySources, NodeProjectFieldSet

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PackageFileRequest:
    package_root: str


@rule()
async def get_npm_package_files(request: PackageFileRequest) -> Digest:
    project_root = PurePath(request.package_root)
    package_json_path = project_root.joinpath("package.json")
    package_lock = project_root.joinpath("package-lock.json")
    yarn_lock = project_root.joinpath("yarn.lock")
    npm_shrinkwrap = project_root.joinpath("npm-shrinkwrap.json")

    rooted_configs = await Get(
        Digest,
        PathGlobs(
            [
                str(package_json_path),
                str(package_lock),
                str(yarn_lock),
                str(npm_shrinkwrap),
            ]
        ),
    )
    unrooted_configs = await Get(Digest, RemovePrefix(rooted_configs, project_root))
    return unrooted_configs


@dataclass(frozen=True)
class NodeSourceFilesRequest:
    package_address: str


@rule()
async def get_node_package_file_sources(
    request: NodeSourceFilesRequest,
) -> StrippedSourceFiles:
    transitive_targets = await Get(
        TransitiveTargets, TransitiveTargetsRequest([request.package_address])
    )
    all_sources = [
        t.get(NodeLibrarySources)
        for t in transitive_targets.closure
        if t.has_field(NodeLibrarySources)
    ]
    source_files = await Get(StrippedSourceFiles, SourceFilesRequest(all_sources))
    return source_files


@rule()
async def get_node_package_digest(field_set: NodeProjectFieldSet) -> Digest:
    artifact_paths = field_set.artifact_paths.value
    package_files, source_files, nvm_bin = await MultiGet(
        Get(Snapshot, PackageFileRequest(field_set.address.spec_path)),
        Get(StrippedSourceFiles, NodeSourceFilesRequest(field_set.address)),
        Get(Environment, EnvironmentRequest(["NVM_BIN"])),
    )

    build_context = await Get(
        Snapshot, MergeDigests([source_files.snapshot.digest, package_files.digest])
    )
    search_path = []
    if nvm_bin:
        search_path.append(nvm_bin.get("NVM_BIN"))
    search_path.extend(["/bin", "/usr/bin", "/usr/local/bin"])
    npm_paths = await Get(
        BinaryPaths,
        BinaryPathRequest(
            binary_name="npm",
            search_path=search_path,
        ),
    )
    if not npm_paths.first_path:
        raise ValueError("Could not find npm in path: {} cannot create package"
                         .format(":".join(search_path)))

    npm_path = npm_paths.first_path.path
    npm_install_result = await Get(
        ProcessResult,
        Process(
            argv=[npm_paths.first_path.path, "install"],
            output_directories=["./node_modules"],
            output_files=["npm-shrinkwrap.json", "./package-lock.json", "yarn.lock"],
            input_digest=build_context.digest,
            env={"PATH": ":".join(search_path)},
            description="installing node project dependencies",
        ),
    )

    logger.debug(npm_install_result.stdout)
    build_context = await Get(
        Snapshot, MergeDigests([build_context.digest, npm_install_result.output_digest])
    )
    proc = await Get(
        ProcessResult,
        Process(
            description="Running npm run-script pants:build",
            argv=[npm_paths.first_path.path, "run-script", "pants:build"],
            input_digest=build_context.digest,
            output_directories=artifact_paths,
            env={"PATH": ":".join(search_path)},
        ),
    )
    logger.debug(proc.stdout)
    return proc.output_digest


@rule()
async def node_project_package(
    field_set: NodeProjectFieldSet,
) -> BuiltPackage:
    """"""
    package = await Get(Digest, NodeProjectFieldSet, field_set)
    output = await Get(Snapshot, AddPrefix(package, field_set.address.spec_path))
    return BuiltPackage(
        digest=output.digest,
        artifacts=tuple(BuiltPackageArtifact(f) for f in output.files),
    )


def rules():
    """Return the pants rules for this module."""
    return [
        UnionRule(NodeProjectFieldSet, NodeProjectFieldSet),
        *collect_rules(),

    ]

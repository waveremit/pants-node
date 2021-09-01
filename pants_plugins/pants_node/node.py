from pants.core.util_rules.external_tool import (DownloadedExternalTool,
                                                 ExternalTool)
from pants.engine.platform import Platform


class Node(ExternalTool):
    options_scope = "node"
    help = "Execution environment for non-browser javascript"

    default_version = "latest-fermium"
    default_known_versions = [
        "latest-fermium|darwin|2e40ab625b45b9bdfcb963ddd4d65d87ddf1dd37a86b6f8b075cf3d77fe9dc09|31959580",
        "latest-fermium|linux|bee6d7fb5dbdd2931e688b33defd449afdfd9cd6e716975864406cda18daca66|34005093",
    ]

    lts_version_to_version_number = {
        "latest-fermium": "v14.17.5",
    }

    def plat_str(self, plat: Platform) -> str:
        return "linux-arm64" if plat == Platform.linux else "darwin-x64"

    def generate_url(self, plat: Platform) -> str:
        version_number = self.lts_version_to_version_number[self.version]
        return f"https://nodejs.org/dist/{self.version}/node-{version_number}-{self.plat_str(plat)}.tar.gz"

    def generate_exe(self, plat: Platform) -> str:
        version_number = self.lts_version_to_version_number[self.version]
        x = f"./shellcheck-{self.version}/shellcheck"
        return f"./node-{version_number}-{self.plat_str(plat)}/bin/"

    def generate_npm_exe(self, plat: Platform) -> str:
        version_number = self.lts_version_to_version_number[self.version]
        return f"./node-{version_number}-{self.plat_str(plat)}/bin/node"

    def get_path(self, plat: Platform):
        version_number = self.lts_version_to_version_number[self.version]
        return f"./node-{version_number}-{self.plat_str(plat)}/bin/"


@dataclass(frozen=True)
class WebpackRequest:
    tool_request: ExternalToolRequest


@dataclass(frozen=True)
class WebpackResult:
    node: DownloadedExternalTool
    digest: Digest


@rule
async def install_node_and_webpack(webpack_request: WebpackRequest) -> WebpackResult:
    node = await Get(
        DownloadedExternalTool, ExternalToolRequest, webpack_request.tool_request
    )
    process_path = webpack_request.node.exe + "node"
    npm_path = node.exe + "../lib/node_modules/npm/bin/npm-cli.js"
    logger.info(process_path)
    logger.info(npm_path)
    process_result = await Get(
        ProcessResult,
        Process(
            argv=[node.exe + "/node", npm_path, "install", "webpack", "--save"],
            input_digest=node.digest,
            output_directories=["node_modules"],
            description="installing webpack",
        ),
    )
    logger.info(process_result.stdout)
    return WebpackResult(node, process_result.output_digest)

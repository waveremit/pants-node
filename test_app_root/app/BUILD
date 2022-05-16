node_library(name='app_root', dependencies=['test_app_root/app/src:src'])

node_package(
    name="app_root_bundle",
    dependencies=[":app_root"],
    artifact_paths=["public/bundle"],
    app_root="test_app_root/app",
    output_path="output",
)

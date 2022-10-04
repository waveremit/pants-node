node_library(name="test_webpack", dependencies=["//test_webpack/src:src"])

node_package(
    name="test_bundle",
    dependencies=[":test_webpack"],
    artifact_paths=["public/bundle"],
)

docker(
    name="docker_with_weback_bundle",
    base_image="python:3.9.1-slim-buster",
    command=[
        "/bin/bash",
    ],
    dependencies=[
        "test_webpack:test_bundle",
    ],
)

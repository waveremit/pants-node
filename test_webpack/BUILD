
node_library(name='test_webpack', dependencies=['test_webpack/src:src'])

node_package(
    name = 'test_bundle',
    dependencies=[":test_webpack"],
    artifact_paths=["public/bundle"]
)

docker_image(
    name="docker_with_webpack_bundle",
    instructions=[
        "FROM python:3.9.1-slim-buster",
        "COPY public /public",
        "CMD /bin/bash",
    ],
    dependencies=[":test_bundle",]
)

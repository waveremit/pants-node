
node_library(name='test_webpack', dependencies=['test_webpack/src:src'])

node_package(
    name = 'test_bundle',
    dependencies=[":test_webpack"],
    output_paths=["./public/bundle"]
)

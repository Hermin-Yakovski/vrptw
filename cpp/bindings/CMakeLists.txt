find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_greedy_cpp py_greedy.cpp)
target_link_libraries(_greedy_cpp PRIVATE greedy_kernel)
target_include_directories(_greedy_cpp PRIVATE ${CMAKE_SOURCE_DIR}/kernel)

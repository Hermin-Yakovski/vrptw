add_executable(test_greedy_cpp test_greedy.cpp)
target_link_libraries(test_greedy_cpp PRIVATE greedy_kernel)
target_include_directories(test_greedy_cpp PRIVATE ${CMAKE_SOURCE_DIR}/kernel)
set_target_properties(test_greedy_cpp PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

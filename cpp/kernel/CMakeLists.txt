add_library(greedy_kernel STATIC greedy.cpp)
target_include_directories(greedy_kernel PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
set_target_properties(greedy_kernel PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

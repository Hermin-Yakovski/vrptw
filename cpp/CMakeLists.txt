cmake_minimum_required(VERSION 3.20)
project(greedy_vrptw LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

add_subdirectory(kernel)
add_subdirectory(bindings)

option(BUILD_TESTING "Build C++ tests" OFF)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()

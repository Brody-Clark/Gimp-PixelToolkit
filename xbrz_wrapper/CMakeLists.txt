cmake_minimum_required(VERSION 3.15)
project(xbrz_wrapper)

set(CMAKE_CXX_STANDARD 17)

add_library(xbrz SHARED
    Scale.cpp
    xbrz.cpp
)

target_include_directories(xbrz PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# Use dllexport when building the DLL
target_compile_definitions(xbrz PRIVATE BUILDING_DLL)

# Rename the output
set_target_properties(xbrz PROPERTIES
    OUTPUT_NAME "xbrz"
)

# On Windows, export all symbols if needed (optional)
if (WIN32)
    set_target_properties(xbrz PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)
endif()

# Set output directory for all configurations to build/
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

foreach(OUTPUTCONFIG Debug Release RelWithDebInfo MinSizeRel)
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG_UPPER)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UPPER} ${CMAKE_BINARY_DIR})
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UPPER} ${CMAKE_BINARY_DIR})
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UPPER} ${CMAKE_BINARY_DIR})
endforeach()
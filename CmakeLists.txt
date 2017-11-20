cmake_minimum_required(VERSION 3.2)

project(Clothsim)

set ( MAYA_PLUGIN_NAME "Mass-spring cloth" )

if(WIN32)
    if(MSVC)
        # To enable /MP, parralel build on MSVC
        option(WIN32_USE_MP "Set to OFF to diable /MP." ON)
        MARK_AS_ADVANCED(WIN32_USE_MP)
        if(WIN32_USE_MP)
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP")
        endif(WIN32_USE_MP)

        # Other MSVC compilation flags
        add_definitions(-D_SCL_SECURE_NO_WARNINGS)
        add_definitions(-D_CRT_SECURE_NO_DEPRECATE)
		add_definitions(-D NOMINMAX) # prevent windef.h min/max macros from interfering with stl's
		add_definitions(-D REQUIRE_IOSTREAM)
		add_definitions(-D _BOOL)
		set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc")

    endif(MSVC)
else()
add_definitions(-D REQUIRE_IOSTREAM)
add_definitions(-D _BOOL)
add_definitions(-D LINUX)
endif()

# Maya version and architecture (default values)
set(MAYA_VERSION 2015 CACHE STRING "Maya Version")
set(MAYA_ARCH x64 CACHE STRING "HW Architecture")

if(WIN32)
    set( MAYA_USER_DIR $ENV{USERPROFILE}/Documents/maya CACHE PATH "Maya user home directory" )
    set( MAYA_ROOT $ENV{PROGRAMFILES}/Autodesk/Maya${MAYA_VERSION} CACHE PATH "Maya installation directory" )
    set( MAYA_SDK_DEFINITIONS "_AFXDLL;_MBCS;NT_PLUGIN;REQUIRE_IOSTREAM" )
    set( MAYA_HEADERS_DIR ${MAYA_ROOT}/include )
    set( MAYA_LIBRARY_DIR ${MAYA_ROOT}/lib )
else()
    set( MAYA_HEADERS_DIR "/usr/autodesk/maya/include" CACHE PATH "Maya Include Dir" )
    set( MAYA_LIBRARY_DIR "/usr/autodesk/maya/lib" CACHE PATH "Maya Library Dir" )
endif()

set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/build)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/build)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/build)

# add base to include directories
include_directories (${MAYA_HEADERS_DIR})
link_directories (${MAYA_LIBRARY_DIR})

set ( MAYA_DEFINITIONS "_AFXDLL,_MBCS,NT_PLUGIN,REQUIRE_IOSTREAM" )

if(WIN32)
set( MAYASDK_LIBRARIES "Foundation.lib" "OpenMaya.lib" "OpenMayaUI.lib" "OpenMayaAnim.lib" "OpenMayaFX.lib" "OpenMayaRender.lib" )
else()
set( MAYASDK_LIBRARIES "Foundation" "OpenMaya" "OpenMayaUI" "OpenMayaAnim" "OpenMayaFX" "OpenMayaRender" )
endif()

#specify app sources
file(GLOB_RECURSE SOURCE_FILES src/*.c src/*.cc src/*.cpp src/*.h src/*.hh src/*.inl src/*.hpp src/*.glsl src/*.ui)

add_library( ${MAYA_PLUGIN_NAME} SHARED ${SOURCE_FILES} )
target_link_libraries( ${MAYA_PLUGIN_NAME} ${MAYASDK_LIBRARIES})

set_target_properties( ${MAYA_PLUGIN_NAME} PROPERTIES COMPILE_DEFINITIONS ${MAYA_DEFINITIONS} )
set_target_properties( ${MAYA_PLUGIN_NAME} PROPERTIES OUTPUT_NAME ${MAYA_PLUGIN_NAME} )

if(WIN32)
set_target_properties( ${MAYA_PLUGIN_NAME} PROPERTIES SUFFIX ".mll" )
else()
set_target_properties( ${MAYA_PLUGIN_NAME} PROPERTIES SUFFIX ".so" )
endif()

set_target_properties( ${MAYA_PLUGIN_NAME} PROPERTIES CLEAN_DIRECT_OUTPUT 1 )
if(WIN32)
set_target_properties( ${MAYA_PLUGIN_NAME} PROPERTIES LINK_FLAGS "/export:initializePlugin /export:uninitializePlugin" )
endif()
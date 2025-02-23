if (NOT DEBUG)
  string(APPEND CFLAGS " -O2")
endif()
set(CONFIG_ARGS "--host=cray")
if (MODEL STREQUAL gptl)
  string(APPEND CPPDEFS " -DHAVE_PAPI")
endif()
if (NOT DEBUG)
  string(APPEND FFLAGS " -O2")
endif()
string(APPEND SLIBS " -L$ENV{NETCDF_DIR} -lnetcdff -Wl,--as-needed,-L$ENV{NETCDF_DIR}/lib -lnetcdff -lnetcdf")

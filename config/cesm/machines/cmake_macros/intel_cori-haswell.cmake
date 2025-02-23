set(CONFIG_ARGS "--host=cray")
string(APPEND CFLAGS " -xCORE-AVX2")
string(APPEND FFLAGS " -xCORE-AVX2")
string(APPEND SLIBS " -L$(NETCDF_DIR) -lnetcdff -Wl,--as-needed,-L$(NETCDF_DIR)/lib -lnetcdff -lnetcdf")
if (MODEL STREQUAL gptl)
  string(APPEND CPPDEFS " -DHAVE_SLASHPROC")
endif()
string(APPEND LDFLAGS " -mkl")
set(HAS_F2008_CONTIGUOUS "FALSE")

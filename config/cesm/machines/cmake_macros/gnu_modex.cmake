string(APPEND SLIBS " -L$ENV{HDF5_HOME}/lib -lhdf5_fortran -lhdf5 -lhdf5_hl -lhdf5hl_fortran")
string(APPEND SLIBS " -L$ENV{NETCDF_PATH}/lib/ -lnetcdff -lnetcdf -lcurl -lblas -llapack")
if (MODEL STREQUAL gptl)
  string(APPEND CPPDEFS " -DHAVE_VPRINTF -DHAVE_GETTIMEOFDAY -DHAVE_BACKTRACE")
endif()

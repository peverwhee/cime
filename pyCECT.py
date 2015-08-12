#! /usr/bin/env python

import sys,getopt,os
import numpy as np
import Nio
import time
import pyEnsLib
import json
import random
from datetime import datetime
from asaptools.partition import EqualStride, Duplicate
import asaptools.simplecomm as simplecomm 

#This routine compares the results of several (default=3) new CAM tests
#against the accepted ensemble (generated by pyEC).


def main(argv):


    # Get command line stuff and store in a dictionary
    s='verbose sumfile= indir= timeslice= nPC= sigMul= minPCFail= minRunFail= numRunFile= printVarTest popens jsonfile= mpi_enable nbin= minrange= maxrange= outfile= casejson= npick= pepsi_gm'
    optkeys = s.split()
    try:
        opts, args = getopt.getopt(argv,"h",optkeys)
    except getopt.GetoptError:
        pyEnsLib.CECT_usage()
        sys.exit(2)
  
    
    # Set the default value for options
    opts_dict = {}
    opts_dict['timeslice'] = 1
    opts_dict['nPC'] = 50
    opts_dict['sigMul'] = 2
    opts_dict['verbose'] = False
    opts_dict['minPCFail'] = 3
    opts_dict['minRunFail'] = 2
    opts_dict['numRunFile'] = 3
    opts_dict['printVarTest'] = False
    opts_dict['popens'] = False
    opts_dict['jsonfile'] = ''
    opts_dict['mpi_enable'] = False
    opts_dict['nbin'] = 40
    opts_dict['minrange'] = 0.0
    opts_dict['maxrange'] = 4.0
    opts_dict['outfile'] = 'testcase.result'
    opts_dict['casejson'] = ''
    opts_dict['npick'] = 10
    opts_dict['pepsi_gm'] = False
    # Call utility library getopt_parseconfig to parse the option keys
    # and save to the dictionary
    caller = 'CECT'
    gmonly = False
    opts_dict = pyEnsLib.getopt_parseconfig(opts,optkeys,caller,opts_dict)
    popens = opts_dict['popens']

    # Print out timestamp, input ensemble file and new run directory
    dt=datetime.now()
    verbose = opts_dict['verbose']
    print '--------pyCECT--------'
    print ' '
    print dt.strftime("%A, %d. %B %Y %I:%M%p")
    print ' '
    print 'Ensemble summary file = '+opts_dict['sumfile']
    print ' '
    print 'Cam output directory = '+opts_dict['indir']    
    print ' '
    print ' '

    # Create a mpi simplecomm object
    if opts_dict['mpi_enable']:
        me=simplecomm.create_comm()
    else:
        me=simplecomm.create_comm(not opts_dict['mpi_enable'])
  
    ifiles=[]
    if opts_dict['casejson']:
       with open(opts_dict['casejson']) as fin:
            result=json.load(fin)
            in_files_first=result['not_pick_files']
            in_files_temp=random.sample(in_files_first,opts_dict['npick'])
            
    else: 
       # Open all input files
       in_files_temp=os.listdir(opts_dict['indir'])
    in_files=sorted(in_files_temp)
    print 'testcase files:'
    print '\n'.join(in_files)

    if popens:
        #Partition the input file list 
        in_files_list=me.partition(in_files,func=EqualStride(),involved=True)

    else:
        in_files_list=pyEnsLib.Random_pickup(in_files,opts_dict)
    for frun_file in in_files_list:
         if (os.path.isfile(opts_dict['indir'] +'/'+ frun_file)):
             ifiles.append(Nio.open_file(opts_dict['indir']+'/'+frun_file,"r"))
         else:
             print "COULD NOT LOCATE FILE " +opts_dict['indir']+frun_file+" EXISTING"
             sys.exit()
    
    if popens:
        
        # Read in the included var list
        Var2d,Var3d=pyEnsLib.read_jsonlist(opts_dict['jsonfile'],'ESP')
        Zscore3d,Zscore2d=pyEnsLib.compare_raw_score(opts_dict,ifiles,me.get_rank(),Var3d,Var2d)  
        print Zscore3d.shape,Zscore2d.shape
        zmall = np.concatenate((Zscore3d,Zscore2d),axis=0)
        np.set_printoptions(threshold=np.nan)
        if opts_dict['mpi_enable']:
            zmall = pyEnsLib.gather_npArray_pop(zmall,me,(me.get_size(),len(Var3d)+len(Var2d),len(ifiles),opts_dict['nbin'])) 
            if me.get_rank()==0:
                fout = open(opts_dict['outfile'],"w")
		for i in range(me.get_size()):
		    for j in zmall[i]:
                        np.savetxt(fout,j,fmt='%-7.2e')
    else:
	# Read all variables from the ensemble summary file
	ens_var_name,ens_avg,ens_stddev,ens_rmsz,ens_gm,num_3d,mu_gm,sigma_gm,loadings_gm,sigma_scores_gm=pyEnsLib.read_ensemble_summary(opts_dict['sumfile']) 

	if len(ens_rmsz) == 0:
	    gmonly = True
	# Add ensemble rmsz and global mean to the dictionary "variables"
	variables={}
	if not gmonly:
	    for k,v in ens_rmsz.iteritems():
		pyEnsLib.addvariables(variables,k,'zscoreRange',v)

	for k,v in ens_gm.iteritems():
	    pyEnsLib.addvariables(variables,k,'gmRange',v)

	# Get 3d variable name list and 2d variable name list seperately
	var_name3d=[]
	var_name2d=[]
	for vcount,v in enumerate(ens_var_name):
	  if vcount < num_3d:
	    var_name3d.append(v)
	  else:
	    var_name2d.append(v)

	# Get ncol and nlev value
	npts3d,npts2d,is_SE=pyEnsLib.get_ncol_nlev(ifiles[0])
     
	# Compare the new run and the ensemble summary file to get rmsz score
	results={}
	countzscore=np.zeros(len(ifiles),dtype=np.int32)
	countgm=np.zeros(len(ifiles),dtype=np.int32)
	if not gmonly:
	    for fcount,fid in enumerate(ifiles): 
		otimeSeries = fid.variables 
		for var_name in ens_var_name: 
		    orig=otimeSeries[var_name]
		    Zscore,has_zscore=pyEnsLib.calculate_raw_score(var_name,orig[opts_dict['timeslice']],npts3d,npts2d,ens_avg,ens_stddev,is_SE,opts_dict,0,0,0) 
		    if has_zscore:
			# Add the new run rmsz zscore to the dictionary "results"
			pyEnsLib.addresults(results,'zscore',Zscore,var_name,'f'+str(fcount))


	    # Evaluate the new run rmsz score if is in the range of the ensemble summary rmsz zscore range
	    for fcount,fid in enumerate(ifiles):
		countzscore[fcount]=pyEnsLib.evaluatestatus('zscore','zscoreRange',variables,'ens',results,'f'+str(fcount))

	# Calculate the new run global mean
	mean3d,mean2d=pyEnsLib.generate_global_mean_for_summary(ifiles,var_name3d,var_name2d,opts_dict['timeslice'],is_SE,opts_dict['popens'],opts_dict['pepsi_gm'],verbose)
	means=np.concatenate((mean3d,mean2d),axis=0)

	# Add the new run global mean to the dictionary "results"
	for i in range(means.shape[1]):
	    for j in range(means.shape[0]):
		pyEnsLib.addresults(results,'means',means[j][i],ens_var_name[j],'f'+str(i))

	# Evaluate the new run global mean if it is in the range of the ensemble summary global mean range
	for fcount,fid in enumerate(ifiles):
	    countgm[fcount]=pyEnsLib.evaluatestatus('means','gmRange',variables,'gm',results,'f'+str(fcount))
      
	# Calculate the PCA scores of the new run
	new_scores=pyEnsLib.standardized(means,mu_gm,sigma_gm,loadings_gm)
	pyEnsLib.comparePCAscores(ifiles,new_scores,sigma_scores_gm,opts_dict)

	# Print out 
	if opts_dict['printVarTest']:
	    print '*********************************************** '
	    print 'Variable-based testing (for reference only - not used to determine pass/fail)'
	    print '*********************************************** '
	    for fcount,fid in enumerate(ifiles):
		print ' '
		print 'Run '+str(fcount+1)+":"
		print ' '
		if not gmonly:
		    print '***'+str(countzscore[fcount])," of "+str(len(ens_var_name))+' variables are outside of ensemble RMSZ distribution***'
		    pyEnsLib.printsummary(results,'ens','zscore','zscoreRange',(fcount),variables,'RMSZ')
		    print ' '
		print '***'+str(countgm[fcount])," of "+str(len(ens_var_name))+' variables are outside of ensemble global mean distribution***'
		pyEnsLib.printsummary(results,'gm','means','gmRange',fcount,variables,'global mean')
		print ' '
		print '----------------------------------------------------------------------------'

if __name__ == "__main__":
    main(sys.argv[1:])
    print ' '
    print "Testing complete."

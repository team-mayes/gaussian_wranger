gaussian_wrangler
==============================
[//]: # (Badges)
[![Travis Build Status](https://travis-ci.org/REPLACE_WITH_OWNER_ACCOUNT/gaussian_wrangler.png)](https://travis-ci.org/REPLACE_WITH_OWNER_ACCOUNT/gaussian_wrangler)
[![AppVeyor Build status](https://ci.appveyor.com/api/projects/status/REPLACE_WITH_APPVEYOR_LINK/branch/master?svg=true)](https://ci.appveyor.com/project/REPLACE_WITH_OWNER_ACCOUNT/gaussian_wrangler/branch/master)
[![codecov](https://codecov.io/gh/REPLACE_WITH_OWNER_ACCOUNT/gaussian_wrangler/branch/master/graph/badge.svg)](https://codecov.io/gh/REPLACE_WITH_OWNER_ACCOUNT/gaussian_wrangler/branch/master)

A suite of scripts that have been helpful primarily with work flows involving Gaussian.

To install, obtain the tarball (from https://www.dropbox.com/sh/spiu46a0mrgtean/AADfeFWQsJNUpD2UkYNe6gCoa?dl=0)
or by creating it from the project using `python setup.py sdist`). Then install it on your machine, e.g.:

`pip install --upgrade gaussian_wrangler-0.0.0.tar.gz --user`
    
You will also need to install common_wrangler. You can copy the tarball from 
https://www.dropbox.com/sh/spiu46a0mrgtean/AADfeFWQsJNUpD2UkYNe6gCoa?dl=0 or download the project 
and built it yourself (available at https://github.com/team-mayes/common_wrangler). You can use a similar command to install it:

`pip install --upgrade gaussian_wrangler-0.0.0.tar.gz --user`

**check_gauss**: There are two main functions:
1) Checks for normal termination of Gaussian output files in a specified directory, and moves them to a new location.
You can specify the directory where to look, where to move them two, and the extension name of the output files.
2) Checks for convergence of Gaussian output files: either only the final convergence ('-z' option) or for each step 
('-s' option)/

**gauss_fragment**: Given either a Gaussian input or output file, and a list of pairs of atoms, it will produce files 
to run a counterpoise correction calculation and optimize each fragment. Currently, the script assumes 
the initial molecule (or molecules; see below) is neutral with singlet multiplicity. If you would like to use the script 
for other cases, please contact the developer.
 
By default, the script will assume that the pair of atoms are (close enough to be) bonded, are not both part of a ring, 
and there is one molecule in the file. Then, the fragments will be radicals (with determined by the type of bond being 
broken). 

If the `two_molecules` option is used, the script will assume that there are two molecules, and the pair of atoms 
provided includes
one atom from each of the two molecules. 

**gausscom2pdb**: As you might expect, this script takes the atoms and coordinates from a Gaussian input file and 
creates a PDB from them. If a template PDB file is provided, it will replace the coordinates in that PDB with those
from the Gaussian input file. Otherwise, it will created a generic one. .py

**run_gauss**: This script prepares inputs and runs Gaussian jobs, or (with '-s' and '-l' options) prepares and submits
slurm jobs to run Gaussian. It can be used to run (and/or submit) a series of Gaussian jobs.

The script includes functions to determine inputs to Gaussian based on the specifications of the machine running the 
job. For example, if the '{default_route}' parameter is included in the 'job_run_tpl', the script will 
determine a MaxDisk and Cachesize based on the running systems's specifications: specifically, 90% of free diskspace 
and Gaussian's cache size algorithm of ('cache size' * 1024)/num_procs. The calculations assume the whole node will be 
used for the Gaussian job.  These calculations are used to create a Default.Route file for Gaussian to read. This file 
will be created in the current directory, or in a directory specified with the 'scratch_dir' parameter in the 
configuration file.

The program will also determine an appropriate amount of memory to allocate and max number of cores to use (also 
assuming the whole node is used for the Gaussian job) if a '{mem}' and/or '{proc_list}' parameter is included in the 
'job_run_tpl' and not specified in the configuration file.


### Copyright

Copyright (c) 2019, Heather B Mayes


#### Acknowledgements
 
Project based on the 
[Computational Chemistry Python Cookiecutter](https://github.com/choderalab/cookiecutter-python-comp-chem)

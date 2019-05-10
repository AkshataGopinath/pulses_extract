import os
import argparse

import numpy as np


def out(SCRIPT_DIR, FITS_FILE, ncores, nsub=64, lodm=461.0, numdms=200, dmstep=1.0, fname='jobs.txt'):
    script = os.path.join(SCRIPT_DIR, 'prepsubband_call.py')
    dm_core = int(np.ceil(numdms / float(ncores)))
    with open(fname, 'w') as f:
        for n in range(ncores):
            lodm += dm_core
            line = "mkdir {}; cd {}; python {} -nsub {} -noscales -nooffsets -noweights -nobary -lodm {} -numdms {} -dmstep {} -o timeseries_TOPO -zerodm {}; cd ..; mv {}/* .; rm -r {}\n".format(
                n, n, script, nsub, lodm, dm_core, dmstep, FITS_FILE, n, n)
            f.write(line)
            
            
def parser():
  # Command-line options
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  description="The program writes out a file to prepsubband in parallel.")
  parser.add_argument('SCRIPT_DIR', help="Script directory.")
  parser.add_argument('FITS_FILE', help="Name of the fits file.")
  parser.add_argument('ncores', help="Number of cores.", type=int)
  parser.add_argument('-nsub', help="The number of sub-bands to use.", type=int, default=64)
  parser.add_argument('-lodm', help="The lowest dispersion measure to de-disperse (cm^-3 pc).", type=float, default=461.0)
  parser.add_argument('-numdms', help="The number of DMs to de-disperse.", type=int, default=200)
  parser.add_argument('-dmstep', help="The stepsize in dispersion measure to use (cm^-3 pc).", type=float, default=1.0)
  parser.add_argument('-fname', help="Name of the output text file.", default='jobs.txt')
  return parser.parse_args()
  
  
if __name__ == '__main__':
  args = parser()
  out(args.SCRIPT_DIR, args.FITS_FILE, args.ncores, nsub=args.nsub, lodm=args.lodm, numdms=args.numdms, dmstep=args.dmstep, fname=args.fname)




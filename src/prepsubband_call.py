import subprocess
import argparse
import astropy.io.fits as pyfits

def parser():
  # Command-line options
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  description="The program calls prepsubband.")
  parser.add_argument('fits', help="Input data file name.")
  parser.add_argument('-o', help="Root of the output file names.")
  parser.add_argument('-zerodm', help="Subtract the mean of all channels from each sample.", action='store_true')
  parser.add_argument('-dmstep', help="The stepsize in dispersion measure to use (cm^-3 pc).", type=float)
  parser.add_argument('-numout', help="Directory to store the output.", type=int)
  parser.add_argument('-numdms', help="The number of DMs to de-disperse.", type=int)
  parser.add_argument('-lodm', help="The lowest dispersion measure to de-disperse (cm^-3 pc).", type=float)
  parser.add_argument('-nobary', help="Do not barycenter the data.", action='store_true')
  parser.add_argument('-noweights', help="Do not apply PSRFITS weights.", action='store_true')
  parser.add_argument('-nooffsets', help="Do not apply PSRFITS offsets.", action='store_true')
  parser.add_argument('-noscales', help="Do not apply PSRFITS scales.", action='store_true')
  parser.add_argument('-nsub', help="The number of sub-bands to use.", type=int)
  
  return parser.parse_args()
  

def prepsubband(args):
  argument_list = ['prepsubband',]
  
  if args.o: 
    argument_list.append('-o')
    argument_list.append(args.o)
  if args.zerodm: argument_list.append('-zerodm')
  if args.dmstep: 
    argument_list.append('-dmstep')
    argument_list.append(str(args.dmstep))
  if args.numout: numout = args.numout
  else: 
    with pyfits.open(args.fits,memmap=True) as fits:
      header = fits['SUBINT'].header
      numout = header['NSBLK'] * header['NAXIS2']
  if numout % 2: numout += 1
  argument_list.append('-numout')
  argument_list.append(str(numout))
  if args.numdms: 
    argument_list.append('-numdms')
    argument_list.append(str(args.numdms))
  if args.lodm: 
    argument_list.append('-lodm')
    argument_list.append(str(args.lodm))
  if args.nsub: 
    argument_list.append('-nsub')
    argument_list.append(str(args.nsub))
  if args.nobary: argument_list.append('-nobary')
  if args.noweights: argument_list.append('-noweights')
  if args.nooffsets: argument_list.append('-nooffsets')
  if args.noscales: argument_list.append('-noscales')
  argument_list.append(args.fits)
  
  subprocess.call(argument_list)
  return

if __name__ == '__main__':
  args = parser()
  prepsubband(args)
  
  
  

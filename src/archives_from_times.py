import argparse
import os
from glob import glob

import astropy.io.fits as pyfits

from extract_psrfits_subints import extract_subints_from_observation
from create_psrchives import dspsr





def parser():
    # Command-line options
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                    description="The program extracts chunks of data from fits file into psarchives around a specified time list.")
    parser.add_argument('obsID', help="ID of the observation to process.")
    parser.add_argument('time_list', help="List of times to extract, either in seconds from beginning of observation or MJD.", nargs='+', type=float)
    parser.add_argument('-output_folder', help="Path of the folder to store the bursts.", default='.')
    parser.add_argument('-time_window', help="Time window to extract around the pulse, in sec.", default=0.04194304, type=float)
    parser.add_argument('-raw_path', help="Path to raw data", default="/psr_archive/hessels/hessels/AO-FRB/raw_data")
    return parser.parse_args()
 


def main():
  args = parser()
  raw_path = args.raw_path 
  if max(args.time_list) < 36000:
    print "Seconds from the start of observation inserted."
    t_sec = args.time_list
    t_mjd, mjd = sec2mjd(t_sec, args.obsID)
    print "Equivalent MJDs: {}".format([mjd + t / 24. / 3600. for t in t_mjd])
  else:
    print "MJD values inserted."
    t_sec, mjd = mjd2sec(args.time_list, args.obsID)
    t_mjd = [(t - mjd)*24.*3600. for t in args.time_list]
    print "Equivalent seconds from the start of observation: {}".format(t_sec)
    
  #Output directory
  out_dir = args.output_folder
  if not os.path.exists(out_dir):
    os.makedirs(out_dir)
  
  for i in range(len(args.time_list)):
    if not os.path.exists(os.path.join(out_dir,'%.2f'%t_sec[i])):
      os.makedirs(os.path.join(out_dir,'%.2f'%t_sec[i]))
    extract_archive(t_sec[i], t_mjd[i], args.obsID, out_dir=out_dir, width=args.time_window)
  
  return


  
def sec2mjd(t_sec, obsID):
  obs_start, mjd = start_of_obs(obsID)
  return [t + obs_start for t in t_sec], mjd

def mjd2sec(t_mjd, obsID):
  obs_start, mjd = start_of_obs(obsID)
  return [(t - mjd) * 24. * 3600. - obs_start for t in t_mjd], mjd
  
def start_of_obs(obsID,RAW_DIR=raw_path):
  raw_files = os.path.join(RAW_DIR, obsID)
  raw_fits_files = glob(raw_files+'*')
  file_starts = []
  for obs in raw_fits_files:
    with pyfits.open(obs,memmap=True) as fits:
      header = fits['SUBINT'].header + fits['PRIMARY'].header
      file_starts.append(header['STT_SMJD'] + header['STT_OFFS'] + header['NSUBOFFS'] * header['NSBLK'] * header['TBIN'])
  mjd = header['STT_IMJD']
  return min(file_starts), mjd
  
  
  
def extract_archive(t_sec, t_mjd, obsID, out_dir='.', width=0.04194304,RAW_DIR=raw_path):
  out_dir = os.path.abspath(out_dir)
  #Create fits file
  fits_file = os.path.join(out_dir,'%.2f'%t_sec,'%s_%.2f.fits'%(obsID,t_sec))
  if not os.path.isfile(fits_file):
    raw_files = os.path.join(RAW_DIR, obsID)
    extract_subints_from_observation(raw_files, out_dir, [t_sec,], -2, 8, pulseID='%.2f'%t_sec)
  
  #Create psrchive
  dspsr(fits_file, SMJD=t_mjd, width=width)
  
  return



if __name__ == '__main__':
  main()

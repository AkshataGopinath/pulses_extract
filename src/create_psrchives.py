import subprocess
from glob import glob
import os
import argparse
import shutil
import StringIO

import psrchive
import astropy.io.fits as pyfits
import numpy as np
import pandas as pd
from presto import psr_utils

from auto_waterfaller import psrchive_plots


ephemeris = '''PSRJ J0531+33
RAJ 05:31:58.561
DECJ 33:08:52.56
PEPOCH 55388.0
P0 {}
EPHVER 2
DM {}'''


def parser():
    # Command-line options
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                    description="The program create a sinlge-pulse psrchive file.")
    parser.add_argument('db_name', help="Name of the HDF5 database containing single pulses.", default='.')
    parser.add_argument('-fits_file', help="Name of fits file.", default='*')
    parser.add_argument('-obsPATH', help="Path of the observation output folder.", default='.')
    #parser.add_argument('-par_file', help="Name of the parameter file for the puls.", default='')
    parser.add_argument('-profile_bins', help="Number of bins within the profile.", default=4096, type=int)
    return parser.parse_args()

def read_fits(fits_file):
  with pyfits.open(fits_file) as fits:
    header = fits['SUBINT'].header + fits['Primary'].header
    #MJD seconds of the beginning of the fits file
    mjds_chop = header['STT_SMJD'] + header['STT_OFFS'] + header['NSUBOFFS'] * header['NSBLK'] * header['TBIN']
    #Time resolution of the fits file
    time_resolution = header['TBIN']
    freq_c = header['OBSFREQ']
    bandwidth = abs(header['OBSBW'])
    
  return {'time_resolution': time_resolution, 'freq_c': freq_c, 'bandwidth': bandwidth}

  
def dspsr(fits_file, puls=None, par_file=False, profile_bins=4096, parallel=False, DM=560.5, Downfact=False, SMJD=False, width=0.04194304):
  #Read puls
  if isinstance(puls, pd.Series):
    DM = puls.DM
    SMJD = puls.SMJD
    Downfact = puls.Downfact
  else:
    if not SMJD:
      print "Either a valid pulse pandas instance or seconds from beginning of day (SMJD) required. Exiting"
      return 1
  
  if SMJD > 86400: SMJD = SMJD - 86400  #Deal with observations taken over midnight
  
  #Read par_file
  if not par_file:
    obs_id = os.path.splitext(os.path.basename(fits_file))[0]
    par_file = '/dev/shm/{}_ephemeris'.format(obs_id)
    with open(par_file, 'w') as f:
      f.write(ephemeris.format(width, DM))
    
  archive_name = os.path.splitext(fits_file)[0]
  puls_folder = os.path.split(archive_name)[0]
  if not os.path.isfile(archive_name + '.ar'):
    readfile = read_fits(fits_file)
    period = width #readfile['time_resolution'] * profile_bins

    #Delay between maximum and central frequencies
    DM_delay = psr_utils.delay_from_DM(DM, readfile['freq_c']) - psr_utils.delay_from_DM(DM, readfile['freq_c'] + readfile['bandwidth'] / 2. )
    n_puls = int(DM_delay / period)

    temp_folder = os.path.join('/dev/shm', os.path.basename(archive_name))
        
    def archive_creation(phase_start=0):
      if os.path.exists(temp_folder): shutil.rmtree(temp_folder)
      os.makedirs(temp_folder)
      
      #Fold the fits file to create single-pulse archives
      if phase_start: start = period / 2.
      else: start = 0
      
      with open(os.devnull, 'w') as FNULL:
        _ = subprocess.call(['dspsr', '-S', str(start), '-K', '-b', str(profile_bins), '-s', '-E', par_file, fits_file], cwd=temp_folder, stdout=FNULL)
        
      #Lists of archive names and starting times (s)
      archive_list = np.array(glob(os.path.join(temp_folder,'pulse_*.ar')))
      archive_time_list = np.array([psrchive.Archive_load(ar).start_time().get_secs() + psrchive.Archive_load(ar).start_time().get_fracsec() for ar in archive_list])
      idx_sorted = np.argsort(archive_list)
      archive_list = archive_list[idx_sorted]
      archive_time_list = archive_time_list[idx_sorted]
    
      #Find archive where dispersed pulse would start
      start_dispersed_puls = SMJD - archive_time_list
      idx_puls = np.where( (start_dispersed_puls > 0) & (start_dispersed_puls < period))[0][0]
    
      #Check that puls is centered
      phase = start_dispersed_puls[idx_puls] / period - start / period
      
      idx_puls += n_puls
      if phase_start > 0.75: idx_puls += 1
      
      return phase, archive_list[idx_puls]
    
    phase, archive = archive_creation()
    
    if abs(phase - 0.5) > 0.25: phase, archive = archive_creation(phase_start=phase)
   
    shutil.copyfile(os.path.join(temp_folder,archive), archive_name + '.ar')
    shutil.rmtree(temp_folder)
    if os.path.isfile('/dev/shm/{}_ephemeris'.format(obs_id)): os.remove('/dev/shm/{}_ephemeris'.format(obs_id))
    
  #Clean the archive
  if not os.path.isfile(archive_name + '.ar.paz'):
    subprocess.call(['paz', '-e', 'ar.paz', '-r', archive_name + '.ar'], cwd=puls_folder)
  
  #Create downsampled archive at the closest factor scrunched in polarisation
  if Downfact:
    downfact = int(Downfact)
    while profile_bins % downfact != 0:
      downfact -= 1
    
    if not os.path.isfile(archive_name + '.ar.paz.pb'+str(downfact)):  
      subprocess.call(['pam', '-e', 'paz.pb'+str(downfact), '-p', '-b', str(downfact), archive_name + '.ar.paz'], cwd=puls_folder)  
      #Plot the archive
      psrchive_plots(os.path.join(puls_folder, archive_name + '.ar.paz.pb'+str(downfact)))
    
    #Create compressed archive
    if not os.path.isfile(archive_name + '.ar.paz.Fpb'+str(downfact)):
      subprocess.call(['pam', '-e', 'Fpb'+str(downfact), '-F',  archive_name + '.ar.paz.pb'+str(downfact)], cwd=puls_folder)  

  return

  
if __name__ == '__main__':
  args = parser()
  
  pulses = pd.read_hdf(args.db_name,'pulses')
  pulses = pulses[(pulses.Pulse == 0) | (pulses.Pulse == 1)]
  
  #if args.par_file: par_file = args.par_file
  #else: par_file = ephemeris

  fits_path = os.path.join(args.obsPATH, '{}', args.fits_file)
    
  for idx_p, puls in pulses.iterrows():
    print "  Pulse n. {} processing".format(idx_p)
    fits_file = fits_path.format(idx_p) 
    try: 
      if '*' in fits_file: fits_file = glob(fits_file)[0]
    except IndexError: 
      print "PSRCHIVE for pulse {} cannot be created.".format(idx_p)
      with open(os.path.join(args.obsPATH, 'ERRORS.txt'), 'w') as error_file:
        error_file.write("PSRCHIVE for pulse {} cannot be created.".format(idx_p))      
      continue
    dspsr(fits_file, puls=puls, profile_bins=args.profile_bins)
    
    #if args.par_file: os.remove(par_file)


import subprocess
from glob import glob
import os
import argparse
import multiprocessing as mp
import shutil

import psrchive
import pyfits
import numpy as np
import pandas as pd
from presto import psr_utils

from auto_waterfaller import psrchive_plots


def parser():
    # Command-line options
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                    description="The program create a sinlge-pulse psrchive file.")
    parser.add_argument('db_name', help="Name of the HDF5 database containing single pulses.", default='.')
    parser.add_argument('-fits_file', help="Name of fits file.", default='*')
    parser.add_argument('-obsPATH', help="Path of the observation output folder.", default='.')
    parser.add_argument('-par_file', help="Name of the parameter file for the puls.", default='*.par')
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

  
def dspsr(puls, par_file, fits_file, profile_bins=4096, parallel=False):
  archive_name = os.path.splitext(fits_file)[0]
  puls_folder = os.path.split(archive_name)[0]
  if not os.path.isfile(archive_name + '.ar'):
    readfile = read_fits(fits_file)
    period = readfile['time_resolution'] * profile_bins

    #Delay between maximum and central frequencies
    DM_delay = psr_utils.delay_from_DM(puls.DM, readfile['freq_c']) - psr_utils.delay_from_DM(puls.DM, readfile['freq_c'] + readfile['bandwidth'] / 2. )
    n_puls = int(DM_delay / period)

    temp_folder = os.path.join('/dev/shm', os.path.basename(archive_name))
        
    def archive_creation(phase_start=0):
      if os.path.exists(temp_folder): shutil.rmtree(temp_folder)
      os.makedirs(temp_folder)
      
      #Fold the fits file to create single-pulse archives
      if phase_start: start = period / 2.
      else: start = 0
      _ = subprocess.call(['dspsr', '-S', str(start), '-D', str(puls.DM), '-K', '-b', str(profile_bins), '-s', '-E', par_file, fits_file], cwd=temp_folder)
    
      #Lists of archive names and starting times (s)
      archive_list = np.array(glob(os.path.join(temp_folder,'pulse_*.ar')))
      archive_time_list = np.array([psrchive.Archive_load(ar).start_time().get_secs() + psrchive.Archive_load(ar).start_time().get_fracsec() for ar in archive_list])
      idx_sorted = np.argsort(archive_list)
      archive_list = archive_list[idx_sorted]
      archive_time_list = archive_time_list[idx_sorted]
    
      #Find archive where dispersed pulse would start
      start_dispersed_puls = puls.SMJD - archive_time_list
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
    
  #Clean the archive
  if not os.path.isfile(archive_name + '.ar.paz'):
    subprocess.call(['paz', '-e', 'ar.paz', '-r', archive_name + '.ar'], cwd=puls_folder)
  
  #Create downsampled archive at the closest factor scrunched in polarisation
  downfact = int(puls.Downfact)
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
  pulses = pulses[pulses.Pulse <= 1]
  
  if '*' in args.par_file: par_file = glob(args.par_file)[0]
  else: par_file = args.par_file

  fits_path = os.path.join(args.obsPATH, '{}', args.fits_file)
    
  for idx_p, puls in pulses.iterrows():
    fits_file = fits_path.format(idx_p) 
    if '*' in fits_file: fits_file = glob(fits_file)[0]
    dspsr(puls, par_file, fits_file, profile_bins=args.profile_bins)



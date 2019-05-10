import argparse
import glob
import os
import sys

import matplotlib
matplotlib.use('Agg')
import pandas as pd
pd.options.mode.chained_assignment = None
import numpy as np
from scipy import special
from astropy.io import fits as pyfits

import C_Funct
import auto_waterfaller
from extract_psrfits_subints import extract_subints_from_observation
from obs_parameters import parameters


def parser():
  # Command-line options
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                  description="The program groupes events from single_pulse_search.py in pulses.")
  parser.add_argument('-db_name', help="Filename of the HDF5 database.", default='SinglePulses.hdf5')
  parser.add_argument('-fits', help="Filename of .fits file.", default='*.fits')
  parser.add_argument('-idL', help="Basename of .singlepulse files.", default='*')
  parser.add_argument('-folder', help="Path of the folder containig the .singlepulse files.", default='.')
  parser.add_argument('-store_events', help="Store events in a HDF5 database.", action='store_true')
  parser.add_argument('-events_dt', help="Duration in sec within two events are related to the same pulse.", default=20e-3,
                      type=float)
  parser.add_argument('-events_dDM', help="Number of DM steps within two events are related to the same pulse.", 
                      default=5, type=float)
  parser.add_argument('-DM_step', help="Value of the DM step between timeseries.", 
                      default=1., type=float)
  parser.add_argument('-events_database', help="Load events from the database.", action='store_true')
  parser.add_argument('-pulses_database', help="Load pulses from the database.", action='store_true')
  parser.add_argument('-parameters_id', help="Parameters to search the observation defined in obs_parameters.", default='Default')
  parser.add_argument('-store_dir', help="Path of the folder to store the output.", default='.')
  parser.add_argument('-plot_pulses', help="Save plots of detected pulses.", action='store_true')
  parser.add_argument('-extract_raw', help="Extract raw data specified in this path around detected pulses.", default='')
  parser.add_argument('-pulses_checked', help="Path of a text file containig a list of pulse identifiers to label as RFI.", default='')
  parser.add_argument('-plot_statistics', help="Produce plots with statistics of the pulses.", action='store_true')
  parser.add_argument('-beam_num', help="Number ID of the beam.", type=int, default=None)
  parser.add_argument('-group_num', help="Number ID of the group of beams (i.e. subband).", type=int, default=None)
  parser.add_argument('-beam_comparison', help="Path of databases to merge and compare.", default=None)
  parser.add_argument('-no_RFI', help="Do not select RFI instances.", action='store_false')
  return parser.parse_args()
  
  

def main(args):
  if args.beam_comparison is not None: 
    beam_comparison(hdf5_in=args.beam_comparison, hdf5_out=args.db_name)
    exit()
  if args.pulses_database: 
    try: pulses = pd.read_hdf(os.path.join(args.store_dir,args.db_name),'pulses')
    except (KeyError, IOError):
      print "Database does not contain pulses!"
      return
  else: 
    header = fits_header(args.fits)
    pulses = pulses_database(args, header)
    print pulses
    store = pd.HDFStore(os.path.join(args.store_dir,args.db_name), 'a')
    store.append('pulses',pulses)
    #store.append('pulses_bu',pulses) #Create a back up table in the database
    store.close()
    pulses = pulses[pulses.Pulse == -1]
    obs_id = os.path.splitext(args.db_name)[0]
    pulses.sort_index().to_csv(os.path.join(args.store_dir,'{}_pulses.txt'.format(obs_id)), sep='\t', columns=['Pulse',], header=['Rank',], index_label='#PulseID')

  pulses = pulses[pulses.Pulse < 4]
  if args.pulses_checked: 
    pulses_checked(pulses, args.pulses_checked)
    store = pd.HDFStore(os.path.join(args.store_dir,args.db_name), 'r+')
    store.remove('pulses')
    store.append('pulses',pulses)
    store.close()

    obs_id = os.path.splitext(args.db_name)[0]
    pulses[(pulses.Pulse == 0) | (pulses.Pulse == 1) | (pulses.Pulse == 3)].sort_index().to_csv(os.path.join(args.store_dir,'{}_realPulses_info.txt'.format(obs_id)), sep='\t', \
      columns=['Sigma','DM','Time','Sample','IMJD','SMJD','Downfact','Duration','top_Freq','N_events','dDM','Pulse'], \
      header= ['SNR',  'DM','Time','Sample','IMJD','SMJD','Downfact','Duration','top_Freq','N_events','dDM','Rank'], index_label='#PulseID')
    
  if args.plot_pulses: 
    if pulses.shape[0] > 0:
      database_path = os.path.join(args.store_dir,args.db_name)
      params = parameters[args.parameters_id]
      if (args.parameters_id == "FRB130628_Alfa_s0") or (args.parameters_id == "FRB130628_Alfa_s1"):
        auto_waterfaller.main(args.fits, database_path, np.array(pulses.Time), np.array(pulses.DM), np.array(pulses.IMJD), np.array(pulses.SMJD), np.array(pulses.Sigma), \
                                             duration=np.array(pulses.Duration), top_freq=pulses.top_Freq.iloc[0], \
                                             FRB_name=params['FRB_name'], directory=args.store_dir, \
                                             pulse_id=np.array(pulses.index), beam=np.array(pulses.Beam), group=np.array(pulses.Group))
      else:  
        auto_waterfaller.main(args.fits, database_path, np.array(pulses.Time), np.array(pulses.DM), np.array(pulses.IMJD), np.array(pulses.SMJD), np.array(pulses.Sigma), \
                                             duration=np.array(pulses.Duration), top_freq=pulses.top_Freq.iloc[0], \
                                             FRB_name=params['FRB_name'], directory=args.store_dir, pulse_id=np.array(pulses.index))
  
  if args.extract_raw: 
    real_pulses = pulses[(pulses.Pulse == 0) | (pulses.Pulse == 1) | (pulses.Pulse == 3)]
    extract_subints_from_observation(args.extract_raw, args.store_dir, np.array(real_pulses.Time), -2, 8, pulseID=np.array(real_pulses.index).astype(str))
  
  if args.plot_statistics: 
    if args.pulses_checked: ranked = True
    else: ranked = False
    obs_id = os.path.splitext(args.db_name)[0]
    if pulses.shape[0] > 0:
      auto_waterfaller.plot_statistics(np.array(pulses.DM), np.array(pulses.Time), np.array(pulses.Sigma), np.array(pulses.Duration), np.array(pulses.Pulse), \
        folder=args.store_dir, observation=obs_id, ranked=ranked)

  return


def events_database(args, header):
  #Create events database
  params = parameters[args.parameters_id]
  sp_files = glob.glob(os.path.join(args.folder,'{}*.singlepulse'.format(args.idL)))
  events = pd.concat(pd.read_csv(f, delim_whitespace=True, dtype=np.float64) for f in sp_files if os.stat(f).st_size > 0)
  print "Loaded {} events.".format(events.shape[0])
  events.reset_index(drop=True, inplace=True)
  events.columns = ['DM','Sigma','Time','Sample','Downfact','a','b']
  events = events.ix[:,['DM','Sigma','Time','Sample','Downfact']]
  events.index.name = 'idx'
  events['Pulse'] = 0
  events.Pulse = events.Pulse.astype(np.int32)

  #Correct Downfact value including downsample of prepsubband
  try:
    dv = params['down_values']
    df = events.Downfact * 0
    df[events.DM < min(dv)] = 1
    for i in sorted(dv):
      df[events.DM >= i] = dv[i]
    events.Downfact *= df
  except KeyError: pass
  
  events.Downfact = events.Downfact.astype(np.int16)
  events.Sample = events.Sample.astype(np.int32)
  events.sort_values(['DM','Time'],inplace=True)

  #Remove last 10s of data
  obs_length = header['NSBLK'] * header['NAXIS2'] * header['TBIN']
  events = events[events.Time < obs_length-10.]

  C_Funct.Get_Group(events.DM.values, events.Sigma.values, events.Time.values, events.Pulse.values, 
                    args.events_dDM, args.events_dt, args.DM_step)

  #events = events[events.Pulse >= 0]

  if args.store_events:
    store = pd.HDFStore(os.path.join(args.store_dir,args.db_name), 'w')
    store.append('events',events,data_columns=['Pulse','SAP','BEAM','DM','Time'])
    store.close()
    
  return events
  
  
def pulses_database(args, header, events=None):
  #Create pulses database
  if args.events_database: events = pd.read_hdf(os.path.join(args.store_dir,args.db_name),'events')
  elif not isinstance(events, pd.DataFrame): events = events_database(args, header)
  events = events[events.Pulse >= 0]
  gb = events.groupby('Pulse',sort=False)
  pulses = events.loc[gb.Sigma.idxmax()]
  print "Detected {} pulses.".format(pulses.shape[0])
  pulses.index = pulses.Pulse
  pulses.index.name = None
  pulses = pulses.loc[:,['DM','Sigma','Time','Sample','Downfact']]
  pulses.index.name = 'idx'
  pulses['IMJD'] = header['STT_IMJD']
  pulses['SMJD'] = header['STT_SMJD'] + header['STT_OFFS'] + header['NSUBOFFS'] * header['NSBLK'] * header['TBIN'] + pulses.Time
  pulses.ix[pulses.SMJD > 86400, 'IMJD'] += 1  #Deal with observations taken over midnight
  
  if args.beam_num is not None: pulses['Beam'] = args.beam_num
  if args.group_num is not None: pulses['Group'] = args.group_num
  pulses['Duration'] = pulses.Downfact * header['TBIN']
  pulses['top_Freq'] = header['OBSFREQ'] + abs(header['OBSBW']) / 2.
  pulses['Pulse'] = -1 
  pulses.Pulse = pulses.Pulse.astype(np.int8)
  pulses['dDM'] = (gb.DM.max() - gb.DM.min()) / 2.
  pulses.dDM=pulses.dDM.astype(np.float32)
  pulses['dTime'] = (gb.Time.max() - gb.Time.min()) / 2.
  pulses.dTime=pulses.dTime.astype(np.float32)
  pulses['N_events'] = gb.DM.count()
  pulses.N_events = pulses.N_events.astype(np.int16)
  pulses['Obs_ID'] = os.path.splitext(args.db_name)[0]

  params = parameters[args.parameters_id]
  pulses = pulses[pulses.N_events > 5]
  #print "%d grouped events"%(pulses.shape[0])

  n_pulses = pulses.shape[0] #zeroth order pulses
  print "Selected {} pulses.".format(n_pulses)
  
  if n_pulses > 0 and args.no_RFI:
    RFIexcision(events, pulses, params, args) #1st order
    #set search parameter space
    pulses.Pulse[pulses.Sigma <= params['SNR_peak_min']] = 9
    pulses.Pulse[pulses.Downfact >= params['Downfact_max']] = 9
    pulses.Pulse[pulses.DM <= params['DM_search_low']] = 9
    pulses.Pulse[pulses.DM >= params['DM_search_high']] = 9
    print "{} pulses classified as astrophysical".format(pulses[pulses.Pulse == -1].shape[0])
  #print pulses.Pulse
  pulses.sort_values(['Pulse','Sigma'], ascending=False, inplace=True) 
  return pulses #2nd (final) order

def RFIexcision(events, pulses, params, args):
  RFI_code = 9
  events = events[events.Pulse.isin(pulses.index)]
  events.sort_values(by='DM',inplace=True)
  gb = events.groupby('Pulse')
  pulses.sort_index(inplace=True)
    
  #Remove flat SNR pulses. Minimum ratio to have weakest pulses with SNR = 8
  pulses.Pulse[pulses.Sigma / gb.Sigma.min() <= params['SNR_peak_min'] / params['SNR_min']] = RFI_code
  
  #Remove flat duration pulses. Minimum ratio to have weakest pulses with SNR = 8 (from Eq.6.21 of Pulsar Handbook)
  pulses.Pulse[gb.Downfact.max() / pulses.Downfact < (params['SNR_peak_min'] / params['SNR_min'])**2] = RFI_code
  
  #Remove pulses peaking near the DM edges
  DM_frac = (params['DM_high'] - params['DM_low']) * 0.2  #Remove 5% of DM range from each edge
  pulses.Pulse[(pulses.DM < params['DM_low']+DM_frac) | (pulses.DM > params['DM_high']-DM_frac)] = RFI_code
  
  #Remove pulses intersecting half the maximum SNR different than 2 or 4 times
  def crosses(sig):
    diff = sig - (sig.max() + sig.min()) / 2.
    count = np.count_nonzero(np.diff(np.sign(diff)))
    return (count != 2) & (count != 4) & (count != 6) & (count != 8)
  pulses.Pulse[gb.apply(lambda x: crosses(x.Sigma))] = RFI_code
  
  """
  #Remove weaker pulses within a temporal window [good for multi-beam]
  def simultaneous(p):                            
    puls = pulses.Pulse[np.abs(pulses.Time-p.Time) < 0.02]
    if puls.shape[0] == 1: return False
    elif p.name == puls.index[0]: return False
    else: return True
  pulses.Pulse[pulses.apply(lambda x: simultaneous(x), axis=1)] = RFI_code
  """
  
  #Remove many pulses concentrated in time
  def RFI_bursts(p):
    puls = pulses.Pulse[np.abs(pulses.Time-p.Time) < 1.]
    if puls.shape[0] <= 10: return False
    elif p.name == puls.index[0]: return False
    else: return True
  pulses.Pulse[pulses.apply(lambda x: RFI_bursts(x), axis=1)] = RFI_code
  
  return


def fits_header(filename):
  with pyfits.open(filename,memmap=True) as fits:
    header = fits['SUBINT'].header + fits['PRIMARY'].header
  return header


def pulses_checked(pulses, filename):
  RFI_list = np.genfromtxt(filename, dtype=int).T

  #print "Folowing pulses will be marked as RFI: ", RFI_list[0,RFI_list[1]==0]
  #sys.stdout.write("Proceed? [y/n]")
  #choice = raw_input().lower()
  #if not (choice == 'y') | (choice == 'yes'): 
    #print "Aborting..."
    #return
  
  pulses.Pulse.loc[RFI_list[0]] = RFI_list[1]
  return


def beam_comparison(hdf5_in='*.hdf5', hdf5_out='SinglePulses.hdf5'):
  #Merge the databases
  pulses = pd.DataFrame()
  events = pd.DataFrame()
  db_list = glob.glob(hdf5_in)
  for f in db_list:
    try: p = pd.read_hdf(f, 'pulses')
    except (KeyError, IOError): continue
    e = pd.read_hdf(f, 'events')
    #e = e[e.Pulse.isin(p.index)]

    try:
      group_order = 10**np.ceil(np.log10(p.Group.max()))
      group = p.Group.unique()
      if len(group) == 1: group = group[0]
      else: raise ValueError('More than one group found in a single database!')
      p.index *= group_order
      p.index += group
      e.Pulse *= group_order
      e.Pulse += group
    except AttributeError: pass
    try:
      beam_order = 10**np.ceil(np.log10(p.Beam.max()))
      beam = p.Beam.unique()
      if len(beam) == 1: beam = beam[0]
      else: raise ValueError('More than one beam found in a single database!')
      p.index *= beam_order
      p.index += beam
      e.Pulse *= beam_order
      e.Pulse += beam
    except AttributeError:
      print "No candidates found in any beam/subband pair"
      sys.exit()

    pulses = pd.concat([pulses, p])
    events = pd.concat([events, e])

  if pulses.shape[0] == 0:
    print "No pulse detected!"
    return

  #Compare the beams
  conditions_A = '(Time > @tmin) & (Time < @tmax)'
  if 'Group' in pulses.columns: conditions_B = '(SAP == @sap) & (BEAM != @beam) & (DM > @DMmin) & (DM < @DMmax) & (Sigma >= @SNRmin)'
  else: conditions_B = '(BEAM != @beam) & (DM > @DMmin) & (DM < @DMmax) & (Sigma >= @SNRmin)'
    
  def comparison(puls):
    if puls.Pulse >= 2: return False
    if 'Group' in puls.columns: sap = int(puls.Group)
    beam = int(puls.Beam)
    tmin = float(puls.Time - 2. * puls.Duration)
    tmax = float(puls.Time + 2. * puls.Duration)
    DMmin = float(puls.DM - .5)
    DMmax = float(puls.DM + .5)
    SNRmin = puls.Sigma / 2.
    if events.query(conditions_A).query(conditions_B).groupby('BEAM').count().shape[0] > 4: return True
    else: return False
  
  pulses.Pulse[pulses.apply(lambda x: comparison(x), axis=1)] = 8
  
  pulses.to_hdf(hdf5_out, 'pulses')
  events.to_hdf(hdf5_out, 'events')
  return


if __name__ == '__main__':
  args = parser()
  main(args)


import os
import argparse

import matplotlib.pyplot as plt
import numpy as np
import psrchive
import scipy.misc

def parser():
    # Command-line options
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                    description="Plot dynamic spectrum from single archives with 1 polarisation and 1 subintegration.")
    parser.add_argument('archive_name', help="Name of the psrchive file to plot.")
    parser.add_argument('-show', help="Show the plot.", action='store_false')
    parser.add_argument('-save_fig', help="Save the plot.", action='store_true')
    parser.add_argument('-zap', help="Plot to manually zap bins out.", action='store_true')
    return parser.parse_args()

def main():
  args = parser()
  DS, extent = load_DS(args.archive_name)
  if args.zap: extent = None
  zap(args.archive_name, DS)
  plot_DS(DS, args.archive_name, extent=extent, show=args.show, save=args.save_fig)
  
def plot_DS(DS, archive_name, extent=None, show=True, save=False):
  fig = plt.figure()
  
  #Dynamic spectrum
  ax1 = plt.subplot2grid((5,5), (1,0), rowspan=4, colspan=4)
  if extent:
    smooth_DS = scipy.misc.imresize(DS, 0.25, interp='cubic').astype(np.float)
    smooth_DS -= np.median(smooth_DS)
    smooth_DS /= smooth_DS.max()
    cmap = 'RdGy_r'
  else: 
    smooth_DS = DS
    cmap = 'Greys'
  ax1.imshow(smooth_DS, cmap=cmap, origin='upper', aspect='auto', interpolation='nearest', extent=extent)
  if extent:
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Frequency (MHz)")
  else:
    ax1.set_xlabel("Time (bins)")
    ax1.set_ylabel("Frequency (bins)")
    extent = [0, smooth_DS.shape[1]-1, smooth_DS.shape[0]-1, 0]
  
  #Pulse profile
  ax2 = plt.subplot2grid((5,5), (0,0), colspan=4, sharex=ax1)
  prof = np.mean(smooth_DS, axis=0)
  x = np.linspace(extent[0], extent[1], prof.size)
  ax2.plot(x, prof, 'k-')
  ax2.tick_params(axis='y', which='both', left='off', right='off', labelleft='off')
  ax2.tick_params(axis='x', labelbottom='off')
  ax2.set_xlim(extent[0:2])
  
  #Baseline
  ax3 = plt.subplot2grid((5,5), (1,4), rowspan=4, sharey=ax1)
  bl = np.mean(smooth_DS, axis=1)
  y = np.linspace(extent[3], extent[2], bl.size)
  ax3.plot(bl, y, 'k-')
  ax3.tick_params(axis='x', which='both', top='off', bottom='off', labelbottom='off')
  ax3.tick_params(axis='y', labelleft='off')
  ax3.set_ylim(extent[2:4])
  
  #General plot settings
  fig.tight_layout()
  fig.subplots_adjust(hspace=0, wspace=0)
  title = os.path.split(os.path.basename(archive_name))[0]
  plt.title(title)
  
  if show: plt.show()
  if save: fig.savefig(title)
  return 

def load_DS(archive_name):
  load_archive = psrchive.Archive_load(archive_name)
  load_archive.remove_baseline()
  DS = load_archive.get_data().squeeze()
  
  freq = load_archive.get_centre_frequency()
  bw = abs(load_archive.get_bandwidth())
  duration = load_archive.integration_length() * 1000
  
  return DS, [0., duration, freq-bw/2, freq+bw/2]
    
def zap(archive_name, DS):
  zap_list = load_zap_list(archive_name)
  
  med = np.median(DS)
  for chan in zap_list:
    DS[chan[0], chan[1]:chan[2]] = med
  DS -= med
  DS /= DS.max()
  return
  
def load_zap_list(archive_name):
  '''
  List of bins to zap in the archive.
  Single list per archive where first column is the frequency channel, second column is the starting time and third column is the ending time.
  None value in time mean all values.
  '''
  
  if os.path.basename(archive_name) == 'puppi_57649_C0531+33_0106_413.Tp':
    zap_list = [\
[99,  2700, 3700],
[103, 1700, 2700],
[275, None, None],
[276, None, None],
[323, None, None],
[324, None, None],
[334, None, None]
]
    
  elif os.path.basename(archive_name) == 'puppi_57644_C0531+33_0021_2461.Tp':
    zap_list = [\
[0, None, None],
[286, None, None],
[310, None, None],
[311, None, None],
[320,765, 1500],
[321, 0, 1500],
[332, None, None],
[341, None, None],
[342, None, None],
[353, None, None],
[323, None, None],
[324, None, None],
[343, None, None],
[344, None, None],
[287, None, None],
[510, None, None]
]

  elif os.path.basename(archive_name) == 'puppi_57638_C0531+33_1218_280.Tp':
    zap_list = [\
[102, 3750, None],
[170, None, None],
[180, None, None],
[275, None, None],
[276, None, None],
[286, None, None],
[310, 3750, None],
[311, 3750, None],
[320, 700, 1000],
[332, None, None],
[334, None, None],
[335, None, None],
[341, None, None],
[342, None, None],
[353, None, None],
[410, 2500, None]
]

  
  elif os.path.basename(archive_name) == 'puppi_57648_C0531+33_0048_821.Tp':
    zap_list = [\
[0  , None, None],
[1  , None, None],
[2  , None, None],
[3  , None, None],
[4  , None, None],
[5  , None, None],
[6  , None, None],
[7  , None, None],
[8  , None, None],
[9  , None, None],
[10 , None, None],
[11 , None, None],
[12 , None, None],
[13 , None, None],
[14 , None, None],
[15 , None, None],
[16 , None, None],
[17 , None, None],
[18 , None, None],
[19 , None, None],
[20 , None, None],
[27 , None, None],
[28 , None, None],
[29 , None, None],
[102, None, 2000],
[168, None, None],
[169, None, None],
[170, None, None],
[171, None, None],
[172, None, None],
[180, None, None],
[168, None, None],
[168, None, None],
[275, None, None],
[276, None, None],
[286, None, None],
[287, None, None],
[323, None, None],
[324, None, None],
[332, None, None],
[334, None, None],
[341, None, None],
[342, None, None]
]
  
  elif os.path.basename(archive_name) == 'puppi_.Tp':
    zap_list = [\
[100, None, 1000],
[275, None, None],
[276, None, None],
[310, None, None],
[311, None, None],
[320, None, None],
[321, None, None],
[334, None, None],
[335, None, None],
[343, None, 3000],
[344, None, 3000],
[353, None, None]
]
  
  elif os.path.basename(archive_name) == 'puppi_.Tp':
    zap_list = [\
[],
[]
]    
  else:
    print "Archive not known. It will not be zapped. Select bins to zap out if you wish."
    zap_list = []
    
  return zap_list 


if __name__ == '__main__':
  main()

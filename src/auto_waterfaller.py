"""
auto_waterfaller.py

Kelly Gourdji - Sept. 2016

"""
from waterfaller import waterfall, plot_waterfall
from matplotlib import pyplot as plt
from matplotlib import cm
import matplotlib.cm
import numpy as np
import sys
import optparse
import copy
import psr_utils
import rfifind
import psrfits
import spectra
import os
import pandas as pd
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib import ticker
from math import ceil
import subprocess
from PIL import Image
from glob import glob

def plotter(data, start, plot_duration, t, DM, IMJD, SMJD, duration, top_freq, sigma, 
			directory, FRB_name, observation, zero_dm_data, zero_dm_start, pulse_id, pulse_events, zoom=True, idx='', downsamp=True):
	
	fig = plt.figure(figsize=(8,5))
	ax1 = plt.subplot2grid((3,3), (1,1), rowspan=2, colspan=3)
	ax2 = plt.subplot2grid((3,3), (1,0), rowspan=3) #row = right, col = left, row = left, col=right
	ax3 = plt.subplot2grid((3,3), (0,1), colspan=3)
	ax4 = plt.subplot2grid((3,3), (0,0))

	fontsize = 11
	ax2.axis([0,7,0,11])
	ax2.annotate('Pulse ID: %i'%pulse_id, xy=(0,9),fontsize=fontsize)
	ax2.annotate('DM: %d'%DM, xy=(0,7.5), fontsize=fontsize)
	ax2.annotate('MJD: %.8f'%(IMJD+SMJD), xy=(0,6), fontsize=fontsize)
	ax2.annotate('Time (s): %0.3f'%t, xy=(0,4.5), fontsize=fontsize)
	ax2.annotate('Duration (ms): %0.2f'%(duration*1000.), xy=(0,3), fontsize=fontsize)
	ax2.annotate('Top frequency: %0.2f'%top_freq, xy=(0,1.5), fontsize=fontsize)
	ax2.annotate('Sigma: %0.2f'%sigma, xy=(0,0), fontsize=fontsize)
	
	zerodm_timeseries(ax3, plot_duration, zero_dm_data, zero_dm_start)
	plot_waterfall(data, start, plot_duration, 
	               integrate_ts=True, integrate_spec=False, show_cb=False, 
	               cmap_str="gist_yarg", sweep_dms=[], sweep_posns=[],
	               ax_im=ax1, ax_ts=ax3, ax_spec=None, interactive=False)
	
	dm_snr(pulse_events, ax=ax4)
	ax3.axvline(t, c='r')
	ax3.legend(loc=1, fontsize=8, frameon=False)
	ax2.axis('off')
	ax1.set_xlabel('Time (s)')
	fig.tight_layout(w_pad = 2, h_pad = 0.0)
	plt.subplots_adjust(hspace=0.3)#, bottom=0.05)
	if zoom and downsamp:
		title = (' [close up with downsamp = %d]'%downsamp)
		name = '_zoomed_downsamped'
		#ax1.locator_params(axis='x', tight=True, nbins=4)
		#ax1.xaxis.set_minor_locator(minorLocator)
		#ax1.tick_params(axis='x',which='minor',bottom='on', top='on')
		ax1.ticklabel_format(style='sci', axis='x', scilimits=(0,0), useOffset=True)
	elif zoom:
		title = (' [close up]')
		name = '_zoomed'
		#ax1.locator_params(axis='x', tight=True, nbins=4)
		#ax1.xaxis.set_minor_locator(minorLocator)
		#ax1.tick_params(axis='x',which='minor',bottom='on', top='on')
		ax1.ticklabel_format(style='sci', axis='x', scilimits=(0,0), useOffset=True)
	else:
		title = name = ''
	plt.suptitle('%s %.8f %s\n %s'%(FRB_name, IMJD + SMJD, title, observation), y=1.05)
	if not os.path.isdir('%s/%s'%(directory, pulse_id)): os.makedirs('%s/%s'%(directory, pulse_id))
	plt.savefig('%s/%s/%s_%s%s.png'%(directory, pulse_id, observation, pulse_id, name),\
									   bbox_inches='tight', pad_inches=0.2, dpi=300)
	fig.clf()
	plt.close('all')


def zerodm_timeseries(ax, plot_duration, data, zero_dm_start):
		nbinlim = np.int(plot_duration/data.dt)
		Data = np.array(data.data[..., :nbinlim])
		Dedisp_ts = Data.sum(axis=0)
		times = (np.arange(data.numspectra)*data.dt + zero_dm_start)[..., :nbinlim]
		ax.plot(times, Dedisp_ts, c="0.6", zorder=2, label='zero-dm filtering')
		ax.set_xlim([times.min(),times.max()])

def histogram(data, ax, title='', xlabel='', color='', bins=None, stacked=False, logy=False, logx=False, ranked=False):
	"""
	Creates a histogram of a given burst property. 

	Inputs:

		name: burst property being plotted

	"""
	if not bins:
		if ranked:
			length = sum(len(x) for x in data)
			bins = int(2 * np.sqrt(length))
			ax.hist(data, bins=bins, color=color, histtype='step', lw=2, stacked=stacked, log=logy)

		else:
			length = len(data)
			bins = int(2 * np.sqrt(length))
			ax.hist(data, bins=bins, color='g', histtype='step', lw=2, stacked=stacked, log=logy)



	#logarithmic xaxis scale:
	#MIN = ceil(np.amin(data[0])/1) #round up to nearest integer value
	#MAX = ceil(np.amax(data[0])/1)
	#ax.hist(data, bins=(10.0 ** np.linspace(np.log10(MIN), np.log10(MAX), bins)), color=color, histtype='step', lw=2, stacked=stacked, log=logy)
	#ax.hist(data, bins=bins, color=color, histtype='step', lw=2, stacked=stacked, log=log)
	#ax.set_xscale('log')
	#ax.set_xlim([MIN,MAX])
	#if not logx:
		#n, bin_edges, patches = ax.hist(data, bins=bins, color=color, histtype='step', lw=2, stacked=stacked, log=logy)
		#ax.set_xscale('linear')
		#ax.set_xlim([np.amin(bin_edges), np.amax(bin_edges)])
	#try: 
	#ax.hist(data, bins=bins, color=color, histtype='step', lw=2, stacked=stacked, log=logy)
	#except ValueError: 
	#	pass
	#	print 'did not plot histogram'
	ax.set_xlabel(xlabel, fontsize=8)
	ax.set_ylabel('Counts', fontsize=8)
	t = ax.set_title(title, fontsize=8)
	t.set_y(1.09)
	ax.tick_params(axis='x', labelsize=8)
	ax.tick_params(axis='y', labelsize=8)

def toa_plotter(time, SN, duration, Rank, observation, ax=None):
	"""
	Plots a bar at each candidate time. Bar width corresponds to pulse duration, while its
	height corresponds to the signal to noise ratio of the burst.

	Inputs:

		time: numpy array of arrival times
		SN: numpy array of signal-to-noise ratios
		duration: numpy array of burst durations

	Optional Input:
		Rank: numpy array of pulse rankings for color-mapping. Default is no coloring.
		observation: observation name (str). Default is none.


	"""
	rank_colors = cm.colors.LinearSegmentedColormap.from_list('rank_colors', [(0,'green'), (0.5,'#D4AC0D'), (1,'red')]) 
	norm=cm.colors.Normalize(vmin=0, vmax=2)
	ranks=norm(Rank)
	ax.bar(time, SN, duration, color=rank_colors(ranks), edgecolor=rank_colors(ranks))
	ax.set_xlabel('Time (s)',fontsize=8)
	ax.set_ylabel('S/N', fontsize=8)
	ax.set_title('%s\n\nTimes of Arrival v. Signal to Noise Ratio'%observation, fontsize=8)
	ax.tick_params(axis='x', labelsize=8)
	ax.tick_params(axis='y', labelsize=8)

def scatter(xdata, ydata, ax, Rank, title='', xlabel='', ylabel=''):
	rank_colors = cm.colors.LinearSegmentedColormap.from_list('rank_colors', [(0,'green'), (0.5,'#D4AC0D'), (1,'red')]) 
	norm=cm.colors.Normalize(vmin=0, vmax=2)
	ranks=norm(Rank)
	ax.scatter(xdata, ydata, c=rank_colors(ranks), marker='.', edgecolors=rank_colors(ranks))
	ax.set_xlabel(xlabel, fontsize=8)
	ax.set_ylabel(ylabel, fontsize=8)
	t = ax.set_title(title, fontsize=8)
	t.set_y(1.09)
	ax.tick_params(axis='x', labelsize=8)
	ax.tick_params(axis='y', labelsize=8)

def plot_statistics(dm, time, SNR, duration, Rank, folder='.', observation='', ranked=False):
	#fig = plt.figure(figsize=(8,6))
	ax1 = plt.subplot2grid((3,3), (1,0))
	ax2 = plt.subplot2grid((3,3), (1,1))
	ax3 = plt.subplot2grid((3,3), (1,2))
	ax4 = plt.subplot2grid((3,3), (0,0), colspan=3)
	ax5 = plt.subplot2grid((3,3), (2,0))
	ax6 = plt.subplot2grid((3,3), (2,1))
	ax7 = plt.subplot2grid((3,3), (2,2))

	colors = ['green', '#D4AC0D', 'red']
	toa_plotter(time, SNR, duration, Rank, observation, ax=ax4)

	if ranked:
		DMs = [dm[Rank==0], dm[Rank==1], dm[Rank>=2]]
		histogram(DMs, ax = ax1, title='Distribution of Dispersion Measures',\
		                                            xlabel=(r'DM (pc cm$^{-3}$)'), color=colors, ranked=True)

		SNRs = [SNR[Rank==0], SNR[Rank==1], SNR[Rank>=2]]
		histogram(SNRs, ax= ax2, title='Distribution of Signal to Noise Ratios',\
		                                            xlabel='S/N', color=colors, logy=True, ranked=True)

		durations = [duration[Rank==0]*1000., duration[Rank==1]*1000., duration[Rank>=2]*1000.]
		histogram(durations, ax=ax3, title='Distribution of Burst Durations',\
		                                            xlabel='Duration (ms)', color=colors, ranked=True)
	else:
		histogram(dm, ax = ax1, title='Distribution of Dispersion Measures',\
		                                            xlabel=(r'DM (pc cm$^{-3}$)'))

		histogram(SNR, ax= ax2, title='Distribution of Signal to Noise Ratios',\
		                                            xlabel='S/N', logy=True)

		histogram(duration*1000., ax=ax3, title='Distribution of Burst Durations',\
		                                            xlabel='Duration (ms)')

	scatter(dm, SNR, ax5, title='Dispersion Measure v. Signal to Noise Ratio',\
									 xlabel=(r'DM (pc cm$^{-3}$)'), ylabel='SNR', Rank=Rank)
	scatter(duration*1000., SNR, ax6, title='Pulse Duration v. Signal to Noise Ratio',\
									 xlabel='Duration (ms)', ylabel='SNR', Rank=Rank)
	scatter(duration*1000., dm, ax7, title='Pulse Duration v. Dispersion Measure',\
									 xlabel='Duration (ms)', ylabel=(r'DM (pc cm$^{-3}$)'), Rank=Rank)
	ax5.locator_params(axis='x',nbins=8)
	ax7.locator_params(axis='y', nbins=8)
	plt.tight_layout(w_pad = 0.3, h_pad = 0.1)
	if ranked:
		rank = '_ranked'
		red_artist = plt.Line2D((0,1),(0,0), color='red')
		green_artist = plt.Line2D((0,1),(0,0), color='green')
		yellow_artist = plt.Line2D((0,1),(0,0), color='#D4AC0D')
		ax4.legend([green_artist, yellow_artist, red_artist],['Rank 0: likely real','Rank 1: maybe real','Rank 2: likely RFI'], loc=3, bbox_to_anchor=(0, 1), ncol=1,fontsize=8, frameon=False)

	else:
		rank = ''
	plt.savefig('%s/statistical_plots_%s%s.png'%(folder,observation,rank), bbox_inches='tight')

def master_statistics(dm, SNR, duration, figtitle, figname):
	Rank = np.zeros(len(dm))
	#fig = plt.figure(figsize=(8,6))
	ax1 = plt.subplot2grid((2,3), (0,0)) #row,col,row,col
	ax2 = plt.subplot2grid((2,3), (0,1))
	ax3 = plt.subplot2grid((2,3), (0,2))
	ax4 = plt.subplot2grid((2,3), (1,0))
	ax5 = plt.subplot2grid((2,3), (1,1))
	ax6 = plt.subplot2grid((2,3), (1,2))	

	histogram(dm, ax = ax1, title='Distribution of Dispersion Measures',\
		                                            xlabel=(r'DM (pc cm$^{-3}$)'))

	histogram(SNR, ax= ax2, title='Distribution of Signal to Noise Ratios',\
		                                            xlabel='S/N', logy=True)

	histogram(duration*1000., ax=ax3, title='Distribution of Burst Durations',\
		                                            xlabel='Duration (ms)')

	scatter(dm, SNR, ax4, title='Dispersion Measure v. Signal to Noise Ratio',\
									 xlabel=(r'DM (pc cm$^{-3}$)'), ylabel='SNR', Rank=Rank)
	scatter(duration*1000., SNR, ax5, title='Pulse Duration v. Signal to Noise Ratio',\
									 xlabel='Duration (ms)', ylabel='SNR', Rank=Rank)
	scatter(duration*1000., dm, ax6, title='Pulse Duration v. Dispersion Measure',\
									 xlabel='Duration (ms)', ylabel=(r'DM (pc cm$^{-3}$)'), Rank=Rank)
	ax4.locator_params(axis='x',nbins=8)
	ax6.locator_params(axis='y', nbins=8)
	plt.tight_layout(w_pad = 0.3, h_pad = 0.1)
	plt.suptitle(figtitle, y=1.04)
	plt.savefig(figname, bbox_inches='tight')

def psrchive_plots(archive_name): #assuming: (full name of the archive with path)
		folder, ar_name = os.path.split(archive_name)
		plot_name = ar_name.split('.')[0]
		#subprocess.call(['pav','-GTpd','-g',"%s_DS.ps /CPS"%plot_name, archive_name], cwd=folder)
		subprocess.call(['psrplot','-p','freq+','-c','psd=0','-c','above:l=','-c','above:c=%s'%plot_name,'-D', "%s.ps /CPS"%plot_name, ar_name], cwd=folder)
		subprocess.call(['convert', '%s.ps'%plot_name,'-border','10x10','-fill','white','-opaque','none','-rotate','90','%s.png'%plot_name], cwd=folder)
		subprocess.call(['pav','-SFT','-g',"%s_stokes.ps /CPS"%plot_name, '%s.ar'%plot_name], cwd=folder)
		subprocess.call(['convert', '%s_stokes.ps'%plot_name,'-border','10x10','-fill','white','-opaque','none','-rotate','90','%s_stokes.png'%plot_name], cwd=folder)
		
		stokes = Image.open(folder + '/' + '%s_stokes.png'%plot_name)
		DS = Image.open(folder + '/' + '%s.png'%plot_name)
		width_stokes, height_stokes = stokes.size
		width_DS, height_DS = DS.size
		width = width_stokes + width_DS
		height = max(height_stokes,height_DS)
		diagnostic = Image.new('RGB', (width, height), 'white')
		diagnostic.paste(im=stokes, box=(0,0))
		diagnostic.paste(im=DS, box=(width_stokes,(height_stokes-height_DS)))
		diagnostic.save(folder + '/' +'%s_diagnostic.png'%plot_name)

		os.remove('%s.ps'%os.path.join(folder,plot_name))
		os.remove('%s.png'%os.path.join(folder,plot_name))
		os.remove('%s_stokes.ps'%os.path.join(folder,plot_name))
		os.remove('%s_stokes.png'%os.path.join(folder,plot_name))
		#os.remove('%s_DS.ps'%os.path.join(folder,plot_name))
		#produce pulse profile	
		#subprocess.call(['pav','-DFpTd','-g',"%s_profile.ps /CPS"%plot_name,archive_name], cwd=folder)
		#subprocess.call(['convert', '%s_profile.ps'%plot_name,'-border','10x10','-fill','white','-opaque','none','-rotate','90','%s_profile.png'%plot_name], cwd=folder)
		#os.remove('%s_profile.ps'%os.path.join(folder,plot_name))
		#psrplot -p freq+ -c psd=0 archive.ar

def main(fits, database, time, DM, IMJD, SMJD, sigma, duration=0.01, pulse_id=4279, top_freq=0., directory='.',\
		  FRB_name='FRB121102', downsamp=1., beam=0, group=0, plot_standard=True, plot_zoom=True, plot_wide=False):

  if isinstance(time, float) or isinstance(time, int): time = np.array([time])
  num_elements = time.size
  if isinstance(DM, float) or isinstance(DM, int): DM = np.zeros(num_elements) + DM
  if isinstance(sigma, float) or isinstance(sigma, int): sigma = np.zeros(num_elements) + sigma
  if isinstance(duration, float) or isinstance(duration, int): duration = np.zeros(num_elements) + duration
  if isinstance(pulse_id, float) or isinstance(pulse_id, int): pulse_id = np.zeros(num_elements) + pulse_id
  if isinstance(downsamp, float) or isinstance(downsamp, int): downsamp = np.zeros(num_elements) + downsamp
  if isinstance(IMJD, float) or isinstance(IMJD, int): IMJD = np.zeros(num_elements) + IMJD
  if isinstance(SMJD, float) or isinstance(SMJD, int): SMJD = np.zeros(num_elements) + SMJD

  if not FRB_name.startswith('FRB130628'):
		rawdata = psrfits.PsrfitsFile(fits)
		observation = os.path.basename(fits)
		observation = observation[:observation.find('_subs_')]	

	events = pd.read_hdf(database, 'events')

	#Fractional day
	SMJD = SMJD / 86400.

	for i, t in enumerate(time):
		if FRB_name.startswith('FRB130628'):
			fits = glob("%s/*b%ds%d*.fits"%(fits,beam[i],group[i]))[0]
			rawdata = psrfits.PsrfitsFile(fits)
			observation = os.path.basename(fits)
			observation = os.path.splitext(observation)[0]
		pulse_events = events[events.Pulse == pulse_id[i]]

                #zero-DM filering version
		start_time = t - 0.05
		plot_duration = 0.1
                if plot_standard:
			zero_dm_data, nbinsextra, nbins, zero_dm_start = waterfall(rawdata, start_time, plot_duration, DM[i],\
				nbins=None, nsub=None, subdm = DM, zerodm=True, downsamp=1,\
				scaleindep=False, width_bins=1, mask=False, maskfn=None,\
				bandpass_corr=False, ref_freq=None)
			#non-zero-DM filtering version
			data, nbinsextra, nbins, start = waterfall(rawdata, start_time, plot_duration, DM[i],\
				nbins=None, nsub=None, subdm = DM, zerodm=False, downsamp=1,\
				scaleindep=False, width_bins=1, mask=False, maskfn=None,\
				bandpass_corr=False, ref_freq=None)
			plotter(data, start, plot_duration, t, DM[i], IMJD[i], SMJD[i], duration[i], top_freq,\
				sigma[i], directory, FRB_name, observation, zero_dm_data, zero_dm_start, pulse_events=pulse_events, zoom=False, idx=i, pulse_id=pulse_id[i], downsamp=False)

	        #Zoomed version
 		start_time = t - 0.01
		plot_duration = 0.03
		if plot_zoom:
			zero_dm_data, nbinsextra, nbins, zero_dm_start = waterfall(rawdata, start_time, plot_duration, DM[i],\
				nbins=None, nsub=None, subdm = DM, zerodm=True, downsamp=1,\
				scaleindep=False, width_bins=1, mask=False, maskfn=None,\
				bandpass_corr=False, ref_freq=None)
			data, nbinsextra, nbins, start = waterfall(rawdata, start_time, plot_duration, DM[i],\
				nbins=None, nsub=None, subdm = DM, zerodm=False, downsamp=1,\
				scaleindep=False, width_bins=1, mask=False, maskfn=None,\
				bandpass_corr=False, ref_freq=None)
			plotter(data, start, plot_duration, t, DM[i], IMJD[i], SMJD[i], duration[i], top_freq,\
				sigma[i], directory, FRB_name, observation, zero_dm_data, zero_dm_start, pulse_events=pulse_events, zoom=True, idx=i, pulse_id=pulse_id[i], downsamp=False)               

	        #Wide version
                start_time = t - 0.5
                plot_duration = 1.
                if plot_wide:
                        zero_dm_data, nbinsextra, nbins, zero_dm_start = waterfall(rawdata, start_time, plot_duration, DM[i],\
                                nbins=None, nsub=None, subdm = DM, zerodm=True, downsamp=1,\
                                scaleindep=False, width_bins=1, mask=False, maskfn=None,\
                                bandpass_corr=False, ref_freq=None)
                        #non-zero-DM filtering version
                        data, nbinsextra, nbins, start = waterfall(rawdata, start_time, plot_duration, DM[i],\
                                nbins=None, nsub=None, subdm = DM, zerodm=False, downsamp=1,\
                                scaleindep=False, width_bins=1, mask=False, maskfn=None,\
                                bandpass_corr=False, ref_freq=None)

                        plotter(data, start, plot_duration, t, DM[i], IMJD[i], SMJD[i], duration[i], top_freq,\
                                sigma[i], directory, FRB_name, observation, zero_dm_data, zero_dm_start, pulse_events=pulse_events, zoom=False, idx=i, pulse_id=pulse_id[i], downsamp=False)
	

def dm_snr(pulse_events, ax=None):
	plt.scatter(pulse_events.DM, pulse_events.Sigma, marker='o', s=10, facecolors='none', edgecolors ='k')
	ax.set_xlabel(r'DM (pc cm$^{-3}$)', fontsize=10)
	ax.set_ylabel('S/N', fontsize=10)
	ax.tick_params(axis='x', labelsize=10)
	ax.tick_params(axis='y', labelsize=10)
	ax.locator_params(axis='x',nbins=3)
	ax.locator_params(axis='y',nbins=5)

if __name__ == '__main__':
	#DM, sigma, time, downfact = np.loadtxt(sys.argv[2], usecols=(0,1,2,4), unpack=True) #argv[2] = .singlepulse
	#downsamp = np.zeros(len(downfact)) + 1. #just a place holder so my code runs upon testing.	
	#main(sys.argv[1],time, DM, sigma, downsamp = downsamp) #arg1 = fitsfile
	#singlepulse_file = 'puppi_57614_C0531+33_0803_subs_0001_TOPO_DM561.00.singlepulse'
	#DM, sigma, time, downfact = np.loadtxt(singlepulse_file, usecols=(0,1,2,4), unpack=True)
	#time = time[17:18]
	#sigma = sigma[17:18]
	#downfact = downfact[17:18]
	#DM = DM[17:18]
	#database = 'puppi_57614_C0531+33_0803.hdf5'
	#downsamp = np.zeros(len(downfact)) + 1.
	#main('puppi_57614_C0531+33_0803_subs_0001.fits', database, time, DM, sigma, downsamp = downsamp)

	#database = '/psr_temp/hessels/AO-FRB/P3054/FRB_pipeline/output/puppi_57614_C0531+33_0803/pulses/puppi_57614_C0531+33_0803.hdf5'#'/psr_temp/hessels/AO-FRB/P3054/FRB_pipeline/TEST/SinglePulses.hdf5'#'/psr_temp/hessels/AO-FRB/P3054/FRB_pipeline/output/puppi_57614_C0531+33_0803/OLD/SinglePulses.hdf5'
	#database = '/psr_archive/hessels/hessels/AO-FRB/pipeline_products/20170112_pulses_archive.hdf5'
	database = '/data/FRB121102/pipeline_products/FRB121102_statistics/Pulses_ALL.hdf5'
	pulses = pd.read_hdf(database,'pulses')
	pulses = pulses[pulses.Pulse == 0]
	dm = np.array(pulses.DM)
	SNR = np.array(pulses.Sigma)
	time = np.array(pulses.Time)
	duration = np.array(pulses.Duration)
	figtitle = "FRB121102"
	figname = "FRB121102_statistics.png"
	master_statistics(dm, SNR, duration, figtitle, figname)





#Kelly Gourdji 2016/17
import os
import sys
import Image
from PIL import ImageTk
import pandas as pd
import numpy as np
import h5py
import Tkinter
import argparse
import glob

def select_cands(filename, Master=False, DM_min=None, DM_max=None, Sigma_min=None,duration_max=None, sort=None):
	cands = pd.read_hdf(filename, 'pulses') #Haven't fully implemented these capabilities yet
	if DM_min:
		cands = cands[cands.DM > DM_min]
	if DM_max:
		cands = cands[cands.DM < DM_max]
	if Sigma_min:
		cands = cands[cands.Sigma > Sigma_min]
	if duration_max:
		cands = cands[cands.Duration < duration_max]
	cands = cands[cands.Pulse == -1]
	new_filename = os.path.splitext(filename)[0] + '_pulses_unranked.txt'
	if Master:
		new_filename = os.path.splitext(filename)[0] + '.txt'
		return cands.to_csv(new_filename, sep='\t', cols=['Pulse',], header=['Rank',], index_label='#PulseID')
	
	if sort:
		cands.sort(sort, ascending=False, inplace=True)
		return cands.to_csv(new_filename, sep='\t', cols=['Pulse',], header=['Rank',], index_label='#PulseID')
	else:
		#default sorting (by pulse ID)
		return cands.sort_index().to_csv(new_filename, sep='\t', columns=['Pulse',], header=['Rank',], index_label='#PulseID')

def next_image(event):
	print("Hit the enter key to view the next figure.")
	event.widget.quit() # this will cause mainloop to unblock.

def next_image_quiet(event): #without prompt (view_only_mode)
	event.widget.quit()

#def previous_image(event, current_file):
#	event.widget.quit()
#	global new_file_pos
#	new_file_pos = current_file - 1
	#print new_file_pos

def masterlist_viewer(txtfile, path_to_pulses, view_only_mode=False, multicomponents=False, multibursts=False, start=None):
	with open(txtfile, 'r') as tf:
		pulse_IDs = np.array([]).reshape(0,1)
		components = np.array([]).reshape(0,1)
		multi_bursts = np.array([]).reshape(0,1)
		comments = np.array([]).reshape(0,1)
		paths = np.array([]).reshape(0,1)
		next(tf)
		if view_only_mode:
			next(tf) #skip over lines to be used for header
		for row in tf:
			cols = np.array(row.split())
			ID = cols[0]
			path_to_cand = glob.glob('*/pulses/%s'%ID)[0] #relative to path_to_pulses
			cols = np.array([ID,'','','',path_to_cand])
			pulse_IDs = np.vstack([pulse_IDs, int(cols[0])])
			components = np.vstack([components, cols[1]])
			multi_bursts = np.vstack([multi_bursts, cols[2]])
			comments = np.vstack([comments, str(cols[3])])
			paths = np.vstack([paths, cols[4]])
		comments = comments.astype(object)
		cands = np.loadtxt(txtfile, usecols=(0,), dtype='int')
		if view_only_mode:
			comps = np.loadtxt(txtfile, usecols=(1,), dtype='int')
			bursts = np.loadtxt(txtfile, usecols=(2,), dtype='int')
			comments = np.genfromtxt(txtfile, usecols=(6,), delimiter="\t", skip_header=2, dtype=None)
			comps = np.where(comps>0)[0]
			bursts = np.where(bursts >0)[0]
			if multicomponents and not multibursts:
				cands = cands[comps]
				paths = paths[comps]
				comments = comments[comps]
			if multibursts and not multicomponents:
				cands = cands[bursts]
				paths = paths[bursts]
				comments = comments[bursts]
			if multibursts and multicomponents:
				bursts_comps = np.append(comps, bursts)
				cands = cands[bursts_comps]
				paths = paths[bursts_comps]
				comments = comments[bursts_comps]

			root = Tkinter.Tk()
			root.bind('<Return>', next_image_quiet)
			#root.bind('<space>', next_image_quiet)
			#root.bind('<Left>', lambda event: previous_image(event, current_file))
			for i, cand in enumerate(cands):
				print 'Viewing pulse %d: '%cand + comments[i]
				path_to_cand = paths[i][0]
				abs_path = path_to_pulses + path_to_cand
				#current_file = 0
				#global new_file_pos
				#new_file_pos = 1000 #arbitrary large number
				for file in os.listdir(abs_path): #turn what follows into a function since im repeating to go to previous image.
					if not file.endswith('zoomed.png') and not file.endswith('downsamped.png') and file.endswith('.png') :
						#current_file += 1
						img = Image.open(os.path.join(abs_path, file))
						img = img.resize((800, 500), Image.ANTIALIAS)
						root.geometry('%dx%d' % (img.size[0],img.size[1]))
						tkpi = ImageTk.PhotoImage(img)
						label_image = Tkinter.Label(root, image=tkpi)
						label_image.place(x=0,y=0,width=img.size[0],height=img.size[1])
						root.title(file)			
						root.mainloop()
						#print new_file_pos
						#print current_file
						#if new_file_pos < current_file:
							#break #breaks out of nearest for loop. this isnt useful.
							#instead of using for loop, try using os.walk and search through list of returned files satisfying the above if conditions.

							

					else:
						pass
		else:
			annotated_file = txtfile.split('.')[0]
			unfinished = annotated_file + '_annotated_unfinished.txt'
			continued = annotated_file + '_annotated_continued.txt'
			annotated_file = annotated_file + '_annotated.txt'
			if start:
				start_idx = np.where(cands==start)[0][0]
			else:
				start_idx = 0
			for i, cand in enumerate(cands):
				if i >= start_idx:
					path_to_cand = paths[i][0]
					abs_path = path_to_pulses + path_to_cand
					root = Tkinter.Tk()
					root.bind('<Return>', next_image)
					for file in os.listdir(abs_path):
						if not file.endswith('zoomed.png') and not file.endswith('downsamped.png') and file.endswith('.png') :
							img = Image.open(os.path.join(abs_path, file))
							img = img.resize((800, 500), Image.ANTIALIAS)
							root.geometry('%dx%d' % (img.size[0],img.size[1]))
							tkpi = ImageTk.PhotoImage(img)
							label_image = Tkinter.Label(root, image=tkpi)
							label_image.place(x=0,y=0,width=img.size[0],height=img.size[1])
							root.title(file)				
							root.mainloop()
						else:
							pass

					print "NOW EDITING PULSE %d"%cand
					root.destroy()
					input = raw_input("How many additional components are there?:")
					while input.isdigit() == False:
						input = raw_input("Oops. Please enter an integer:")
					components[i] = input
					input = raw_input("How many additional bursts are there?:")
					while input.isdigit() == False:
						input = raw_input("Oops. Please enter an integer:")
					multi_bursts[i] = input
					comment = raw_input("comments:") #or '\t'
					comments[i] = comment
					pulse_IDs=pulse_IDs.flatten()
					pulse_IDs = pulse_IDs.astype(int)
					components = components.flatten()
					multi_bursts = multi_bursts.flatten()
					comments = comments.flatten()
					if cand == cands[-1] and not start: 
						np.savetxt(annotated_file, np.column_stack([pulse_IDs, components, multi_bursts, comments]),\
				 					delimiter='\t\t', header='PulseID\tAdditional\tAdditional\tComment\n\t\tcomponents\tbursts',fmt="%s")
						os.remove(unfinished)
						
					elif start: #This is a safety, in case classification is interrupted, you don't lose progress and can start classifying at last index and then merge files manually when done.
						np.savetxt(continued, np.column_stack([pulse_IDs, components, multi_bursts, comments]),\
				 					delimiter='\t\t', header='PulseID\tAdditional\tAdditional\tComment\n\t\tcomponents\tbursts',fmt="%s")

					else:
						np.savetxt(unfinished, np.column_stack([pulse_IDs, components, multi_bursts, comments]),\
				 					delimiter='\t\t', header='PulseID\tAdditional\tAdditional\tComment\n\t\tcomponents\tbursts',fmt="%s")
				else:
					pass
			#
def viewer(txtfile, path_to_pulses, obs, view_only_mode=False,ranks_to_view=None):
	#put txtfile columns into numpy arrays:
	with open(txtfile, 'r') as tf:
		pulse_IDs = np.array([]).reshape(0,1)
		ranks = np.array([]).reshape(0,1)
		next(tf)
		for row in tf:
			cols = np.array(row.split())
			pulse_IDs = np.vstack([pulse_IDs, int(cols[0])])
			ranks = np.vstack([ranks, cols[1]])

	cands = np.loadtxt(txtfile, usecols=(0,), dtype='int')
	if view_only_mode:
		root = Tkinter.Tk()
		root.bind('<Return>', next_image_quiet)
		for i, cand in enumerate(cands):
			cand_rank = ranks[i]
			cand_rank = cand_rank.astype(int)
			if cand_rank in ranks_to_view:
				path = path_to_pulses + str(cand)
				for file in os.listdir(path):
					if file.endswith('.png'):
						img = Image.open(os.path.join(path, file))
						img = img.resize((800, 500), Image.ANTIALIAS)
						root.geometry('%dx%d' % (img.size[0],img.size[1]))
						tkpi = ImageTk.PhotoImage(img)
						label_image = Tkinter.Label(root, image=tkpi)
						label_image.place(x=0,y=0,width=img.size[0],height=img.size[1])
						root.title(file)				
						root.mainloop()
					else:
						pass
			else:
				pass
	else:
		for i, cand in enumerate(cands):
			path = path_to_pulses + str(cand)
			root = Tkinter.Tk()
			#root.geometry("800x500")
			root.bind('<Return>', next_image)
			for file in os.listdir(path):
				if file.startswith(file_id): #avoid looking at diagnostic plot. 
					img = Image.open(os.path.join(path, file))
					img = img.resize((800, 500), Image.ANTIALIAS)
					root.geometry('%dx%d' % (img.size[0],img.size[1]))
					tkpi = ImageTk.PhotoImage(img)
					label_image = Tkinter.Label(root, image=tkpi)
					label_image.place(x=0,y=0,width=img.size[0],height=img.size[1])
					root.title(file)				
					root.mainloop()
				else:
					pass
			print "Now ranking candidate %d from %s"%(cand,obs)
			root.destroy()
			input = raw_input("Provide a ranking for this candidate:")
			while input.isdigit() == False:
				input = raw_input("Oups. Please enter an integer:")
			ranks[i] = input

		pulse_IDs=pulse_IDs.flatten()
		pulse_IDs = pulse_IDs.astype(int)
		ranks = ranks.flatten()
		ranks = ranks.astype(int)
		path, txtfilename = os.path.split(txtfile)
		ranked_file = path + "/" + obs + '_pulses.txt'
		np.savetxt(ranked_file, np.column_stack([pulse_IDs, ranks]), delimiter='\t', header='PulseID\tRank',fmt="%s")
	
if __name__ == '__main__':
	#filename = 'puppi_57607_C0531+33_0603/pulses/puppi_57607_C0531+33_0603.hdf5'
	#select_cands(filename, DM_min=530, DM_max=570, Sigma_min=10, sort='Sigma')
	def parser():
		parser = argparse.ArgumentParser(description='View or rank an observation. Hit enter to view the next image. Rank 0 for real, 1 for "smudge", 2 for RFI, 3 for maybe')
		parser.add_argument('-view_only_mode', help="View candidates without ranking them", action='store_true')
		parser.add_argument('-rank', help="View only candidates with these/this rank(s). E.g. If you want to view \
		 					candidates of ranks 1 and 2 type: -rank 12. Default: Rank 0 only", default=[0], type=list)
		parser.add_argument('observation', help="Name of observation to view/rank. If using master option, this is the file name without the extension.")
		parser.add_argument('-create_cand_list', help="Create a list of candidates to rank", action='store_true')
		parser.add_argument('-not_dop263', help="If running script outside of dop263 (script must be in same dir as observation dir).", action='store_true')
		parser.add_argument('-master', help="Use this option if you want to view the master list of FRB pulses.", action='store_true')
		parser.add_argument('-multicomponents', help="Use this option to view only bursts that show multiple components. To be used in master view-only mode.", action='store_true')
		parser.add_argument('-multibursts', help="Use this option to view only candidates showing additional bursts. To be used in master view-only mode.", action='store_true')
		parser.add_argument('-start', help="Start viewer at this pulse ID (works exclusively in master mode at the moment).", default=None, type=int)
		parser.add_argument('-FRB', help="Name of FRB being viewed e.g.'121102'. Default: 121102", default=121102, type=int)
		return parser.parse_args()
	args = parser()

	obs = args.observation
	if args.FRB == 121102:		#"FRB" file_id only works for observations run using early version of pipeline
		#file_id = "FRB" 		#where files start with "FRB".In latest version, use "puppi"
		file_id = "puppi"
		obs_path = '/data/FRB121102/pipeline_products/'

	if args.FRB == 130628:
		file_id = "4"
		obs_path = '/data/gourdji/FRB130628_pipeline/test/'
	
	if args.not_dop263:
		obs_path = ''

	path_to_pulses = obs_path + obs + '/pulses/' #remove pulses directory from path if dealing with global list hdf5 file
	filename = path_to_pulses + obs + '.hdf5' #for select_cands

	if args.master:
		path_to_pulses = obs_path
		filename = path_to_pulses + obs + '.hdf5'
		#txtfile = path_to_pulses + obs + '.txt'
		if args.create_cand_list:
			select_cands(filename, Master=True)

		if args.view_only_mode:
			txtfile = path_to_pulses + obs + '_annotated.txt'
			masterlist_viewer(txtfile, '', view_only_mode=True, multibursts=args.multibursts, multicomponents=args.multicomponents)#, start=args.start) need to implement this
		else:
			txtfile = path_to_pulses + obs + '.txt'
			masterlist_viewer(txtfile, '', start=args.start)
		sys.exit()	

	if args.create_cand_list:
		select_cands(filename)


	if args.view_only_mode: 
		txtfile = path_to_pulses + obs + '_pulses.txt'
		ranks_to_view = args.rank
		ranks_to_view = map(int, ranks_to_view)
		viewer(txtfile, path_to_pulses, obs, view_only_mode=True, ranks_to_view=ranks_to_view)

	else:
		txtfile = path_to_pulses + obs + '_pulses_unranked.txt'
		viewer(txtfile, path_to_pulses, obs)

### Useful rsync command to only download relevant files in the observation's /pulses dir when transfering this dir over
#rsync -r --progress --include='*/' --include='*.png' --include='*.txt' --exclude='*'

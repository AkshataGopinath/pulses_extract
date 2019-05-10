#!/bin/bash -x

if [ $# -ne 1 ] && [ $# -ne 2 ]; then
   echo "Pipeline to process Arecibo data of FRB121102 on wombat."
   echo "The pipeline identify interesting pulses, store them in a SinglePulse.hdf5 database and produces diagnostic plots."
   echo ""
   echo "Usage: bash pulses_identify.sh fits_filename"
   echo "NB: use the command bash to run the pipeline"
   echo "Use the argument -single_core to avoid the pipeline to run in parallel"
   exit
fi

#Check that bash is used
if [ ! "$BASH_VERSION" ] ; then
    echo "Execute the script using the bash command. Exiting..."
    exit 1
fi

echo "Pipeline pulses_identify.sh starting..."
date

#Setting variables
SUB_DIR="/net/gpufaj/media/JWTHAO_9/FRB121102_processing/subbanded_files"
GENERAL_OUT_DIR="/net/gpufaj/media/JWTHAO_9/FRB121102_processing/pipeline_products"

ORIGINAL_FITS_FILE="$1"
FITS_NAME=${ORIGINAL_FITS_FILE##*/}
FITS_ID=${FITS_NAME%_subs_0001.fits}
SCRIPT_DIR="$( cd -P "$( dirname "$0" )" && pwd )/src"
OUT_DIR="$GENERAL_OUT_DIR/$FITS_ID"
FITS_FILE="$SUB_DIR/$FITS_NAME"

#Check that subbanded fits file exists 
if [ ! -e $FITS_FILE ]; then 
  echo ""
  echo "ATTENTION! Subbanded fits file $FITS_NAME not found. Exiting..."
  exit 1
fi  

#Set up the output folder
mkdir $OUT_DIR
cd $OUT_DIR
mkdir obs_data
mkdir pulses
mkdir periodic_cands
mkdir TEMP
cd TEMP

#Parallelisation parameters
if [ "$2" == "-single_core" ]; then
  n_cores=1
else
  n_cores=8
  #n_cores=`lscpu -p | egrep -v '#' | sort -u -t, -k 2,4 | wc -l`
fi

#Create .dat files
echo ".dat files creating..."
SECONDS=0
python $SCRIPT_DIR/write_prepsubband_call.py $SCRIPT_DIR $FITS_FILE $n_cores
bash $SCRIPT_DIR/parallel.sh jobs.txt $n_cores > /dev/null
duration=$SECONDS
echo ".dat files created. Time taken: $(($duration / 60)) m"

#Create .fft files
echo ".fft files creating..."
SECONDS=0
ls *.dat | awk '{printf("realfft %s\n",$1)}' > jobs.txt
bash $SCRIPT_DIR/parallel.sh jobs.txt $n_cores > /dev/null
duration=$SECONDS
echo ".fft files created. Time taken: $(($duration / 60)) m"

#Remove rednoise
echo "Rednoise removing..."
SECONDS=0
ls *.fft | awk '{printf("rednoise %s\n",$1)}' > jobs.txt
bash $SCRIPT_DIR/parallel.sh jobs.txt $n_cores > /dev/null
for inf_file in `ls *.inf`; do cp $inf_file ${inf_file%.inf}_red.inf; done
duration=$SECONDS
echo "Rednoise removed. Time taken: $(($duration / 60)) m"

#Create ACCEL files
echo "ACCEL files creating..."
SECONDS=0
ls *_red.fft | awk '{printf("accelsearch -zmax 20 %s\n",$1)}' > jobs.txt
bash $SCRIPT_DIR/parallel.sh jobs.txt $n_cores > /dev/null
duration=$SECONDS
echo "ACCEL files created. Time taken: $(($duration / 60)) m"

#Create .singlepulse files
echo ".singlepulse files creating..."
SECONDS=0
ls *.dat | awk '{printf("single_pulse_search.py -t 6.0 -b -m 150 %s\n",$1)}' > jobs.txt
bash $SCRIPT_DIR/parallel.sh jobs.txt $n_cores > /dev/null
duration=$SECONDS
echo ".singlepulse files created. Time taken: $(($duration / 60)) m"

#Saving best DM timeseries
cp ${FITS_ID}_TOPO_DM561.00.dat $OUT_DIR/obs_data
cp ${FITS_ID}_TOPO_DM561.00.inf $OUT_DIR/obs_data

#Create database and plots
echo "Database and plots creating..."
SECONDS=0
#Single pulse candidates
python ${SCRIPT_DIR}/pulses_extract.py -db_name ${FITS_ID}.hdf5 -fits $FITS_FILE -store_events -idL ${FITS_ID}_TOPO -store_dir $OUT_DIR/pulses \
  -folder $OUT_DIR/TEMP -plot_pulses -plot_statistics -parameters_id FRB121102_Puppi
#Periodic candidates
python $SCRIPT_DIR/periodic_candidates_plot.py -folder $OUT_DIR/TEMP -fits $FITS_FILE
for plot in `ls *periodic_cand*.ps`; do
  convert -rotate 90 -background white -alpha remove $plot $OUT_DIR/periodic_cands/${plot%.ps}.png
done
duration=$SECONDS
echo "Database and plots created. Time taken: $(($duration / 60)) m"

#Remove meta products
cd $OUT_DIR
rm -rf TEMP

echo "Pipeline pulses_identify.sh finished"
date

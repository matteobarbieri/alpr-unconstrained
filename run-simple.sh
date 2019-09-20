#!/bin/bash

check_file() 
{
	if [ ! -f "$1" ]
	then
		return 0
	else
		return 1
	fi
}

check_dir() 
{
	if [ ! -d "$1" ]
	then
		return 0
	else
		return 1
	fi
}


# Check if Darknet is compiled
check_file "darknet/libdarknet.so"
retval=$?
if [ $retval -eq 0 ]
then
	echo "Darknet is not compiled! Go to 'darknet' directory and 'make'!"
	exit 1
fi

lp_model="data/lp-detector/wpod-net_update1.h5"
debug_mode=false
input_dir=''
output_dir=''
csv_file=''


# Check # of arguments
usage() {
	echo ""
	echo " Usage:"
	echo ""
	echo "   bash $0 -i input/dir -o output/dir -c csv_file.csv [-h] [-l path/to/model]:"
	echo ""
	echo "   -i   Input dir path (containing JPG or PNG images)"
	echo "   -o   Output dir path"
	echo "   -c   Output CSV file path"
	echo "   -l   Path to Keras LP detector model (default = $lp_model)"
    echo "   -d   Debug mode: do not delete tmp folders (default false)"
	echo "   -h   Print this help information"
	echo ""
	exit 1
}

while getopts 'i:o:c:l:hd' OPTION; do
	case $OPTION in
		i) input_dir=$OPTARG;;
		o) output_dir=$OPTARG;;
		c) csv_file=$OPTARG;;
		d) debug_mode=true;;
		l) lp_model=$OPTARG;;
		h) usage;;
	esac
done

if [ -z "$input_dir"  ]; then echo "Input dir not set."; usage; exit 1; fi
if [ -z "$output_dir" ]; then echo "Ouput dir not set."; usage; exit 1; fi

# XXX csv_file parameter no longer required (for now)
#if [ -z "$csv_file"   ]; then echo "CSV file not set." ; usage; exit 1; fi

# Check if input dir exists
check_dir $input_dir
retval=$?
if [ $retval -eq 0 ]
then
	echo "Input directory ($input_dir) does not exist"
	exit 1
fi

# Check if output dir exists, if not, create it
check_dir $output_dir
retval=$?
if [ $retval -eq 0 ]
then
	mkdir -p $output_dir
fi

STAGE=5

# End if any error occur
set -e

# Detect vehicles
if [ $STAGE -le 1 ]; then
    echo "VEHICLE DETECTION"
    python vehicle-detection.py $input_dir $output_dir
fi

# Detect license plates
if [ $STAGE -le 2 ]; then
    echo "LICENSE PLATE DETECTION"
    # TODO fix the useless double argument?
    python simple-license-plate-detection.py $output_dir $output_dir
fi

# OCR
if [ $STAGE -le 3 ]; then
    echo "LICENSE PLATE OCR"
    python license-plate-ocr.py $output_dir
fi

# Draw output and generate list

#python gen-outputs.py $input_dir $output_dir > $csv_file
#python gen-outputs-simple.py $input_dir $output_dir
if [ $STAGE -le 4 ]; then
    echo "GENERATING RAW ANNOTATIONS"
    python generate-raw-annotations.py $input_dir $output_dir \
        --width 3840 --height 2160
fi

# Remove duplicates
if [ $STAGE -le 5 ]; then
    echo "PERFORMING POST PROCESSING ON ANNOTATIONS"
    python post-process-detections.py $input_dir $output_dir
fi

echo "DRAWING OUTPUTS"
if [ $STAGE -le 6 ]; then
    python annotate-images-from-json.py $input_dir $output_dir
fi

# Clean files and draw output
if [ "$debug_mode" = false ] ; then
    rm $output_dir/*_lp.png
    rm $output_dir/*car_*.png
    rm $output_dir/*_cars.txt
    rm $output_dir/*_lp.txt
    rm $output_dir/*.json
    rm $output_dir/*_str.txt
else
    mkdir $output_dir/results
    mv "${output_dir}/"*output.png $output_dir/results
fi

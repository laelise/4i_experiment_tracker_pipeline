#!/bin/bash

#SBATCH -p general
#SBATCH -N 1
#SBATCH --mem 64g
#SBATCH -n 8
#SBATCH -t 5:00:00
#SBATCH --mail-type=end
#SBATCH --mail-user=gasessio@email.unc.edu
#SBATCH -o 01_cellpose_segmentation_local.%j.out 
#SBATCH -e 01_cellpose_segmentation_local.%j.err

module purge
module load anaconda

# Check if the required argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <well_name>"
    exit 1
fi

well_name="$1"

conda activate /proj/purvislb/users/Garrett/env/GPU_4i_segment
python /proj/purvislb/users/Garrett/scripts/01_cellpose_segmentation_local.py "$well_name"

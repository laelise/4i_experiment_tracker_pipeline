#!/bin/bash

#SBATCH -p general
#SBATCH -N 1
#SBATCH --mem 64g
#SBATCH -n 8
#SBATCH -t 5:00:00
#SBATCH --mail-type=end
#SBATCH --mail-user=gasessio@email.unc.edu
#SBATCH -o 02_find_transforms_on_segmentation_df.%j.out 
#SBATCH -e 02_find_transforms_on_segmentation_df.%j.err

module purge
module load anaconda
conda activate /proj/purvislb/users/Garrett/env/GPU_4i_segment
python /proj/purvislb/users/Garrett/scripts/02_find_transforms_on_segmentation_df.py
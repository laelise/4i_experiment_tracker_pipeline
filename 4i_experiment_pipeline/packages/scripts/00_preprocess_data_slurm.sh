#!/bin/bash

#SBATCH -p general
#SBATCH -N 1
#SBATCH --mem 64g
#SBATCH -n 1
#SBATCH -t 1:00:00
#SBATCH --mail-type=end
#SBATCH --mail-user=gasessio@email.unc.edu
#SBATCH -o 00_preprocess_data.%j.out 
#SBATCH -e 00_preprocess_data.%j.err

module purge
module load anaconda
conda activate /proj/purvislb/users/Garrett/env/GPU_4i_segment
python /proj/purvislb/users/Garrett/scripts/00_preprocess_data.py
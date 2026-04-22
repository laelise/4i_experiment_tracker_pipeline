#!/bin/bash

# This script submits Slurm jobs for cell segmentation using cellpose

# List of wells to process
well_list=("B11" "C02" "C03" "C04" "C05" "C06" "C07" "C08" "C09" "C10" "C11" "D02" "D03" "D04" "D05" "E02" "E03" "E04" "E05")

# Path to the Slurm script
slurm_script="01_cellpose_segmentation_local_slurm.sh"

# Submit job for each well in the list
for well in "${well_list[@]}"; do
    sbatch "$slurm_script" "$well"
done

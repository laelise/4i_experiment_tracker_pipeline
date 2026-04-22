# ## About this notebook

# This notebook segments files selected for calculating alignment in each round.
# 
# Input:
# - pathway to a directory containing selected files for the segmentation (im_to_segment)
# - list of wells to process
# 
# Output:
# - segmented masks of selected channels

# ## Fill in info about the experiment to process

# Prepare for segmentation
import os
import sys
from tifffile import imread
import pickle
from skimage.io import imsave
import tensorflow as tf
import cellpose
from cellpose import models
from cellpose import utils

if __name__ == "__main__":
    # Check if the well name is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python 01_cellpose_segmentation_local.py <well_name>")
        sys.exit(1)

myWell = sys.argv[1]
print(myWell)

# define a pathway to a directory that contains images for segmentation (im_to_segment)
path_data = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/output_images'

# pathway to a directory to save segmented images
path_save = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/segmented'

# expected diameter of objects for segmentation in pixels (default 30)
selected_diameter = 30

# The below block is for using the GPU - Currently disabled for testing - CPU segmentation is enabled
#os.environ['CUDA_VISIBLE_DEVICES'] = '0'
#Is cellpose using the GPU, reports True or False
#cellpose.core.use_gpu(gpu_number=0, use_torch=True)
#!nvcc --version
#!nvidia-smi
#End disabled block

try:
    #os.mkdir(save_dir)
    os.mkdir(path_save)
    print('Directory for saving created.')
except:
    print('Directory not created.')

# load cellpose model
#model = models.Cellpose(gpu=True, model_type='cyto')
model = models.Cellpose(gpu=False, model_type='cyto')

# Process selected wells

# loop for segmentation 

file_list = os.listdir(os.path.join(path_data,myWell))
print(myWell)

try:
    os.mkdir(os.path.join(path_save,myWell))
    print(f'Directory for saving {myWell} labels created.')
except:
    pass

for file_name in file_list: 

    # specify pathway to the image
    im_path = os.path.join(path_data,myWell,file_name)

    # get an image
    im = imread(im_path)

    # segment the right plane
    labels, _, _, _ = model.eval(im, diameter=selected_diameter, channels=[0,0])

    # save segmentation
    path_save_temp = os.path.join(path_save,myWell,file_name.replace('im2segment','labels'))
    imsave(path_save_temp,labels)         
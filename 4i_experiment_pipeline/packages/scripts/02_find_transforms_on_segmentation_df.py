# ## About this notebook:

# This notebook calculates a set of transformations based on segmented masks.
# 
# Input:
# - pathway to a directory containing segmented labels
# - pathway to a directory containing data frames
# - list of wells to process
# - downscale factor (1 - no downscaling, 2 - will make images 4 times smaller)
# 
# Output:
# - a set of transforms for each well saved as pkl files
# 
# Downscale factor allows for calculations of transformations on smaller images (for huge images StackReg may run out of RAM - downscaling prevents solves the issue).
# 
# Optionally you can visualize alignment on downscaled images (visualization uses Napari).

# ## Fill in info about the experiment to process

# pathway to a directory with segmented masks for alignment (ex. im_segmented)
path_labels = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/segmented'

# pathway to a directory with data frames (ex. df)
path_df = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/output_df'

# list of wells to be processed (usually names as 'A3')
well_list = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09', 'B10', 'B11', 
             'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11', 
             'D02', 'D03', 'D04', 'D05', 'E02', 'E03', 'E04', 'E05']

# pathway to save transformations (ex. df)
path_save = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/output_df'

# specify a downscaling factor for the alignment
downscale_factor = 1 

# specify anchor round (to which alignment will be done)
anchor_round_selected = 1 # as named in the directory, default should be 1

# ## Prepare for processing

import os
import pickle
import pandas as pd
import numpy as np
from skimage import transform
from skimage.transform import downscale_local_mean
import matplotlib.pyplot as plt
from pystackreg import StackReg
import pystackreg

def read_labels(path_labels,myWell):
    
    labels_list = [x for x in os.listdir(os.path.join(path_labels,myWell)) if 'tif' in x]
    labels_list.sort()

    labels_im_list = []
    for lab_im_name in labels_list:

        lab_im = plt.imread(os.path.join(path_labels,myWell,lab_im_name))
        labels_im_list.append(lab_im)

    labels_im = np.array(labels_im_list)
    
    return labels_im

def rescale_transforms(tmat_org,downscale_factor):
     
    # rescale transformation
    if downscale_factor != 1:
        
        tmat = []

        for tranform_matrix in tmat_org:

            eu_transform_small = transform.EuclideanTransform(tranform_matrix)

            eu_transform = transform.EuclideanTransform(translation = eu_transform_small.translation * downscale_factor,
                                                        rotation = eu_transform_small.rotation)

            tmat.append(eu_transform)
            
    else:
        tmat = tmat_org
            
    return tmat

def find_transformation(labels_im,anchor_round,downscale_factor = 1):

    # resize the image
    labels_small = labels_im>0
    labels_small = downscale_local_mean(labels_small,(1,downscale_factor,downscale_factor))

    
    # find transformation
    tf = StackReg.RIGID_BODY
    sr = StackReg(tf)
    
    tmat_small = []
    for frame in range(labels_small.shape[0]):

        print(frame)
        
        if frame==anchor_round:
            tmat_frame = np.array([[1,0,0],[0,1,0],[0,0,1]])
        else:
            tmat_frame = sr.register(labels_small[anchor_round],labels_small[frame])

        tmat_small.append(tmat_frame)

    tmat_small = np.asarray(tmat_small)

    # rescale transformation
    tmat = rescale_transforms(tmat_small,downscale_factor)
            
    return tmat,tmat_small

def apply_transforms_set(tmat,movie):
    
    res = []
    
    for index,tranform_matrix in enumerate(tmat):
    
        eu_transform = transform.EuclideanTransform(tranform_matrix)

        # if you want to check only transformation without rotation
        #eu_transform_small = transform.EuclideanTransform(translation = eu_transform_small.translation, rotation = 0)

        temp = transform.warp(movie[index,:,:],eu_transform,output_shape=movie[index].shape)

        res.append(temp)

    res = np.array(res)
    
    return res

# ## Process the wells
for myWell in well_list:
    
    print(f'Processing well {myWell}.')
    
    # read in the data
    myData = pd.read_pickle(os.path.join(path_df,f'df_{myWell}.pkl'))
    
    # read in all the labels
    labels_im = read_labels(path_labels,myWell)
    
    # check if you have an expected number of files to align
    print(f'Number of label images {labels_im.shape[0]}')
    print(f'Number of unique rounds {len(set(myData.alignRound))}')
    
    # check which alignRound for the anchor round
    #anchor_round = myData.loc[myData.nameRound == anchor_round_selected,'alignRound'].tolist()[0]
    #anchor_round = int(anchor_round)
    #Had to manually set the anchor round here, since the modified info_csv wasn't parsed by the existing structure
    anchor_round = 0
    
    # find transformation
    tmat,tmat_small = find_transformation(labels_im,anchor_round,downscale_factor = downscale_factor)
    
    # save transformations
    save_file_path = os.path.join(path_save,f'tmat_{myWell}.pkl')
    pickle.dump(tmat, open(save_file_path, "wb"))
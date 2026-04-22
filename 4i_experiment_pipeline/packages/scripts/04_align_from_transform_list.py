# ## About this notebook:
# This notebook uses saved transformations to align all channels in a list of wells.
# 
# Input:
# - a set of transforms (one transform/round)
# - data frames with channel data for each channel
# - nd2 images
# 
# Output:
# - aligned tiffs 
# - updated data frames

# ## Fill in info about the experiment to process

# pathway to a directory with data frames (ex. df)
path_df = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/output_df'
path_tmat=path_df

# pathway to save aligned tiffs (ex. aligned_tiffs)
path_save = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/aligned_tiffs'

# list of wells to be processed (usually names as 'A3')
well_list = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09', 'B10', 'B11', 
             'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11', 
             'D02', 'D03', 'D04', 'D05', 'E02', 'E03', 'E04', 'E05']

# ## Prepare for processing
import os
import pickle
import pandas as pd
import numpy as np
import nd2
from tifffile import imsave
from skimage import transform
import ipywidgets as widgets
from IPython.display import display

# create directory for saving data frames if needed
try:
    os.mkdir(path_save)
    print('Directory for saving aligned tiffs created.')
except:
    print('Directory not created.')

# # Align and save images
for selected_well in well_list:
    
    print(f'Processing well {selected_well}.')
    
    # create output directory
    try:
        os.mkdir(os.path.join(path_save,selected_well))
        print('Sub-directory for saving aligned tiffs created.')
    except:
        print('Directory not created.')
        
    # open data frame
    df_name = f'df_{selected_well}.pkl'
    
    #myData = pd.read_pickle(os.path.join(path_df,df_name))
    with open(os.path.join(path_df,df_name), "rb") as fh: # in case of protocol 5 issues
        myData = pickle.load(fh)
        
    # open transformations
    tmat_name = f'tmat_{selected_well}.pkl'
    tmat_list = pickle.load(open(os.path.join(path_tmat,tmat_name), "rb"))
    
    for ind,my_signal in myData.iterrows():

        # get a path to the image file
        file_path = os.path.join(my_signal.dir,my_signal.sub_dir,my_signal.file)

        # get a handle to the nd2 file
        myIm = nd2.ND2File(file_path)

        # choose the right frame
        dask_im = myIm.to_dask()
        im = dask_im[my_signal.channel_in_file,:,:]

        # trim if needed
        if ((my_signal.width_min < my_signal.width) | (my_signal.height_min < my_signal.height)):

            im = im[:my_signal.height_min,:my_signal.width_min]

        # get the transform
        tf = tmat_list[int(my_signal.alignRound)]

        # apply transform
        im_alig = transform.warp(im,tf,output_shape=im.shape)
        im_alig[im_alig<0] = 0

        # get the range correct
        im_alig = im_alig*2**16

        # save image
        #alig_name = f'Round_{str(int(my_signal.nameRound)).zfill(2)}_well{my_signal.well}_{my_signal.signal}.tif'
        #Removed the int tag from my_signal.nameRound so that the new naming scheme could be parsed. Still avoiding leading zeros
        alig_name = f'Round_{str(my_signal.nameRound).zfill(2)}_well{my_signal.well}_{my_signal.signal}.tif'
        imsave(os.path.join(path_save,selected_well,alig_name),im_alig.astype('uint16'))

        # remember this in the df
        myData.loc[ind,'aligned_file_name'] = alig_name
        
    # save df    
    myData.to_pickle(os.path.join(path_df,df_name))
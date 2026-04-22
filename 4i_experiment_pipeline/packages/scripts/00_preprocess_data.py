# This script prepares 4i data for alignment. It can work for multiple wells from a single experiment as long as they share the 40 antibody set. If it's not the case, the subsets of an experiment should be processed separately.
# 
# Input:
# - a set of stitched nd2 images with 4i data (- see data structure details in the git readme file)
# - csv file translating optical configurations (OC) into the names of the channels (usually the names of antibodies or target proteins)
# 
# Output:
# - a data frame (saved as pkl file) with the info about all the images that will be processed in this experiment
# - a set of single channel tiff files of equal size
# ## Fill in info about the experiment to process

# %%
# pathway to a csv file with the info about the experiment
path_info_file=r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/info_exp.csv'

# pathway to a directory containing data 
path_data = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/data'

# pathway to a directory where the output will be saved (data frames)
path_save_df = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/output_df'

# pathway to a directory where the output will be saved (images)
path_save_im = r'/proj/purvislb/users/Garrett/112723_RPE_31day_Etop/experiment/output_images'

# list of wells to be processed (usually names as 'A3')
well_list = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B09', 'B10', 'B11', 
             'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09', 'C10', 'C11', 
             'D02', 'D03', 'D04', 'D05', 'E02', 'E03', 'E04', 'E05']

# %%
# decide which frames will be used for the alignment
# in the provided example all channels with 'DNA' signal will be used

def sel_2_align(myData):
    
    myData['alignIm'] = (myData.signal=='DNA').astype(int)
    
    return myData

# %% [markdown]
# ## Prepare for processing

# %%
import os
import re
import pickle
import pandas as pd
import numpy as np
import nd2
from tifffile import imsave

# %%
# create directory for saving data frames if needed
try:
    os.mkdir(path_save_df)
    print('Directory for saving data frames created.')
except:
    print('Directory not created.')
    
# create directory for saving images if needed    
try:
    os.mkdir(path_save_im)
    print('Directory for saving images created.')
except:
    print('Directory not created.')

# %%
def build_data_frame(path_info_file,path_data,myWell): 
    
    # read in the file with the info about the eperiment
    myDataRounds = pd.read_csv(path_info_file)
    #print(myDataRounds)

    # create a list of subdirectories
    myFiles = os.listdir(path_data)
    #print(myFiles)

    myData=pd.DataFrame()

    k=0
    round_index = 0
    
    for i,myRoundInfo in myDataRounds.iterrows():

        mySubDirName = [x for x in myFiles if (f'Round_{myRoundInfo.myRound}_' in x)]
        print(myRoundInfo.myRound)
        #print(mySubDirName)
        
        mySubDir = os.path.join(path_data,mySubDirName[0])
        #print(mySubDir)

        myFileName = [x for x in os.listdir(mySubDir) if f'Well{myWell}_Channel' in x][0]
        print(myFileName)

        # get a handle to the file
        myIm = nd2.ND2File(os.path.join(mySubDir,myFileName))

        # through the channels in the file
        for j in range(myIm.sizes['C']):

            # get the channel name (OC)
            myChannel = myIm.metadata.channels[j].channel.name

            # translate the OC into the signal name
            mySignal = myRoundInfo[myChannel]

            if mySignal == mySignal: # if this channel was admitted (otherwise no entry in the info file)

                myData.loc[k,'dir'] = path_data
                myData.loc[k,'sub_dir'] = mySubDirName
                
                myData.loc[k,'file'] = myFileName
                myData.loc[k,'channel_in_file'] = j
                
                myData.loc[k,'nameRound'] = myRoundInfo.myRound      
                myData.loc[k,'well'] = myWell

                myData.loc[k,'signal'] = myRoundInfo[myChannel]
                myData.loc[k,'width'] = myIm.sizes['X']
                myData.loc[k,'height'] = myIm.sizes['Y']
                
                myData.loc[k,'alignRound'] = round_index

                k = k+1
                
        round_index = round_index + 1 
                
    # calculate min size
    width_min = np.min(myData.width)
    height_min = np.min(myData.height)
    
    myData['width_min'] = width_min
    myData['height_min'] = height_min
    
    return myData

def check_selection_to_align(myData):

    t  = myData.groupby(['nameRound']).sum()
    test1 = list(t.alignIm)==([1]*len(t))
    
    if test1:
        print('Data preparation passed tests.')
    else:
        print('Error - stop and report.')
        
def save_2align_files(myData,save_dir):

    saved = 0
    for ind,my_signal in myData.iterrows():

        if my_signal.alignIm == 1:

            # construct the path
            file_path = os.path.join(my_signal.dir,my_signal.sub_dir,my_signal.file)

            # get a handle to the nd2 file
            myIm = nd2.ND2File(file_path)

            # choose the right frame
            dask_im = myIm.to_dask()
            im = dask_im[my_signal.channel_in_file,:,:]
            
            # trim if needed
            my_well = my_signal.well
            my_round = str(int(my_signal.alignRound)).zfill(3)
            
            if ((my_signal.width_min < my_signal.width) | (my_signal.height_min < my_signal.height)):
                
                im = im[:my_signal.height_min,:my_signal.width_min]
                print(f'Image from well {my_well} from round{my_round} trimmed.')
                
            else:
                
                print(f'Image from well {my_well} from round{my_round} not trimmed.')

            # save the image
            imsave(os.path.join(save_dir,f'im2segment_{my_well}_round_{my_round}.tif'),im.astype('uint16'))
            saved = saved + 1
    
    if saved == 0: 
        print(f'Saved {saved} images.')
    elif saved == 1:
        print(f'Saved {saved} image.')
    else:
        print(f'Saved {saved} images.')

# %% [markdown]
# ## Process selected wells

# %%
for myWell in well_list:
    
    print(f'Processing well {myWell}:')
    
    # create a data frame
    myData = build_data_frame(path_info_file,path_data,myWell)

    # mark images used to calculate the alignment
    myData = sel_2_align(myData)
    
    # test if number of images chosen for the alignment matches the number of rounds
    check_selection_to_align(myData)

    # save data frame
    myData.to_pickle(os.path.join(path_save_df,f'df_{myWell}.pkl'))
    myData.to_csv(os.path.join(path_save_df,f'df_{myWell}.csv'))

    # save channels to align
    try:
        os.mkdir(os.path.join(path_save_im,myWell))
        print(f'Directory {myWell} for images created.')
    except:
        pass
    
    save_2align_files(myData,os.path.join(path_save_im,myWell))

# %% [markdown]
# 



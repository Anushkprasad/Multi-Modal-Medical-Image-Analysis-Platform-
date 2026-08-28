# NIH ChestX-ray14 dataset

This project expects the NIH ChestX-ray14 dataset to be placed inside this folder.

## Required files after download

- images/  
  - all chest X-ray DICOM/JPEG image files from the NIH release
- Data_Entry_2017.csv  
  - pathology labels and image file names
- train_list.txt  
- val_list.txt  
- test_list.txt  

## Dataset source

Use the official NIH ChestX-ray14 dataset release, usually hosted on Kaggle and/or the NIH Box mirror.

## Manual download steps

1. Create a Kaggle account at https://www.kaggle.com
2. Accept the dataset terms for the NIH ChestX-ray14 archive
3. Download the dataset zip file to this workspace, or to a known location on your machine
4. Extract it into:
   E:\member3_multimodal\data\nih_chestxray14\
5. Ensure that the extracted folder contains the image files and the label CSV/text files listed above

## Expected pathology labels

Atelectasis
Cardiomegaly
Consolidation
Edema
Effusion
Emphysema
Fibrosis
Hernia
Infiltration
Mass
Nodule
Pleural_Thickening
Pneumonia
Pneumothorax

This repository intentionally does not create synthetic clinical notes and does not modify the existing ClinicalBERT or fusion code.

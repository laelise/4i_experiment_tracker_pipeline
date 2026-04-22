# 4i_pipeline

Canonical 4i pipeline notebooks (do not rename):
- 00_preprocess_data.ipynb
- 01_cellpose_segmentation_local.ipynb
- 02_find_transforms_on_segmentation_df.ipynb
- 03_find_transformation_manually.ipynb
- 04_align_from_transform_list.ipynb
- 04_align_from_transform_single.ipynb
- 05_create_mask.ipynb
- 06_calculate_cell_properties.ipynb
- 07_adata_conversion.ipynb

Run in order as part of a batch processing workflow. Modernize using `src/ring_functions_4i.py` update if needed.
# Daily Experiment Logs

Track what you run in the single-cell analysis pipeline day by day.

## Auto-Logging (Recommended)

Run the session tracker at the end of your coding day:
```python
# Open and run: logs/session_tracker.ipynb
# It will:
# 1. Scan all notebooks/scripts modified today
# 2. Auto-generate a log entry: logs/YYYY-MM-DD_session_log.md
# 3. Record timestamps and file paths
```

Then open the generated log and add your notes, parameters, and findings.

## Manual Logging

If you prefer to manually create logs, follow the format below.

## Format

Create a new log file for each experiment run:
- **Filename:** `YYYY-MM-DD_experiment_name.md` (e.g., `2026-04-02_LPS246_initial_run.md`)
- **Contents:** Record parameters, results, issues, next steps

## Template

```markdown
## Date: YYYY-MM-DD
Dataset: [name]
Project: [e.g., LPS246_Tagto_Abema_Co_3]

### Steps Run
- [ ] 00_preprocess_data
- [ ] 01_cellpose_segmentation_local
- [ ] 02_find_transforms_on_segmentation_df
- [ ] 03_find_transformation_manually
- [ ] 04_align_from_transform_list
- [ ] 05_create_mask
- [ ] 06_calculate_cell_properties
- [ ] 07_adata_conversion

### Parameters Used
- threshold: X
- batch_size: Y
- Other: Z

### Results
- Cells segmented: N
- Run time: X hours
- Output location: /path/to/output

### Issues / Observations
- Issue 1
- Issue 2

### Next Steps
- [ ] Task 1
- [ ] Task 2
```

## Usage
1. Copy the template above into a new `.md` file with today's date
2. Fill in as you run the pipeline
3. Keep for reference on future runs

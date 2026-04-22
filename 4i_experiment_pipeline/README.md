# Single Cell Analysis

Consolidated single-cell analysis pipeline and visualization notebooks for liposarcoma and general single-cell studies.

## Quick Start

### Run the Pipeline
1. Read [4i_pipeline/README.md](4i_pipeline/README.md) for step-by-step details
2. Run notebooks in sequence: `00_preprocess_data.ipynb` → `01_cellpose_segmentation_local.ipynb` → ... → `07_adata_conversion.ipynb`
3. **Track your run:** Create a daily log in `logs/` using the tracker (see [logs/README.md](logs/README.md))

### Analyze Results
- Use notebooks in `analysis/` for visualization, clustering, and plotting
- Subdirectories: `general/`, `feature_comparison/`, `PHATE/`, `slingshot/`, `liposarcoma/`

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `4i_pipeline/` | Core pipeline notebooks (run in order) |
| `analysis/` | Analysis & visualization notebooks by category |
| `src/` | Shared Python scripts (helpers, utilities) |
| `environment/` | Conda environment YAML files |
| `logs/` | Daily experiment tracking & results |
| `packages/` | Package definitions & conda environments |

## Environment Setup

```bash
# Activate an environment (example)
conda env create -f environment/python_3_7.yaml
conda activate <env_name>
```

## Daily Workflow

1. **Start a new analysis:** Run `logs/00_session_tracker.ipynb` at end of day (auto-generates log)
2. **Run pipeline:** Execute `4i_pipeline` notebooks in sequence
3. **Analyze:** Run notebooks from `analysis/` for visualization, clustering, and exploration
4. **Log results:** Open your generated log and add findings, parameters, and next steps

## Revert Reorganization

If needed, undo all folder moves:
```powershell
powershell -ExecutionPolicy Bypass -File undo_reorg.ps1
```
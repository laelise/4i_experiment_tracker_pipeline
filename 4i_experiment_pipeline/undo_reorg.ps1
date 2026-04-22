# Undo reorganization script (single_cell_analysis)
# Run from this folder: `powershell -ExecutionPolicy Bypass -File undo_reorg.ps1`

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Move notebooks back
Move-Item -Path notebooks\analysis\general\*.ipynb -Destination general_analysis -Force
Move-Item -Path notebooks\analysis\feature_comparison\* -Destination general_analysis\feature_comparison_tools -Force
Move-Item -Path notebooks\analysis\PHATE\* -Destination general_analysis\PHATE_tools -Force
Move-Item -Path notebooks\analysis\slingshot\* -Destination general_analysis\slingshot_tools -Force
Move-Item -Path notebooks\analysis\liposarcoma\*.ipynb -Destination liposarcoma_analysis -Force

# Move yaml files back
Move-Item -Path environment\*.yaml -Destination python_environments -Force

# Move scripts back (if they exist)
Move-Item -Path src\delve_general.py -Destination general_analysis\delve.py -Force
Move-Item -Path src\kh_general.py -Destination general_analysis\kh.py -Force
Move-Item -Path src\delve_liposarcoma.py -Destination liposarcoma_analysis\delve.py -Force
Move-Item -Path src\kh_liposarcoma.py -Destination liposarcoma_analysis\kh.py -Force
Move-Item -Path src\ring_functions_4i.py -Destination 4i_pipeline\ring_functions.py -Force
Move-Item -Path src\ring_functions_packages.py -Destination packages\ring_functions.py -Force

# Optional cleanup (leave new directories in place if you prefer)
# Remove-Item -Recurse -Force notebooks\analysis
# Remove-Item -Recurse -Force src\* (be careful!)

Write-Host "Undo script completed. Check whether any files remain in new folders and delete manually if not needed."

# repo-tree-generator

A small Python script that turns an entire project into one clean text file.

## What it does
- Scans a folder
- Skips junk (node_modules, .git, images, large files)
- Keeps only code/config/schema files
- Writes a tree + schema list + file contents into one output file

## How to use
1. Run:
   ```bash
   python project_dumper.py

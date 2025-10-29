# Maya 2022 Python Scripts

A collection of Python scripts for **Autodesk Maya 2022**.  
These scripts aim to automate simple workflows.

## Available Scripts

### `scripts/nurbs_road_builder.py`

Creates a NURBS road network from a selected centerline curve. The script
builds multiple offset curves for the roadway, drains, curbs, and sidewalks,
then lofts surfaces between them to form a complete section. A UI appears on
execution so you can adjust the offsets before generating the geometry.

## Requirements
- Autodesk Maya **2022**
- Python **3.9** or higher

## Usage
1. Load the script into Maya’s **Script Editor** or add it to a **Shelf**.
2. Execute the script to run the desired automation inside Maya.
3. Follow any on-screen prompts or UI elements to configure the tool.

## License
MIT License

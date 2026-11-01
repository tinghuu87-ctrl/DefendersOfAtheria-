"""Refresh reusable placements and save repository/portable linked map variants."""
import bpy
import os
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=Path(os.environ.get('ATHERIA_REUSABLE_PORTALS_OUT','/workspace/atheria-blockout/reusable-enemy-portals'))
spec=importlib.util.spec_from_file_location('reuse',HERE/'place_enemy_portals.py')
reuse=importlib.util.module_from_spec(spec);spec.loader.exec_module(reuse)
scene=bpy.context.scene
reuse.MODE='LANES';reuse.main()
study=bpy.data.scenes['Atheria / Enemy portal design studies']
bpy.context.window.scene=study
for i,name in enumerate(reuse.NAMES):reuse.place(study,'Study '+name,name,((i-1)*10,0,0),0,1)
bpy.context.window.scene=scene
library=next(l for l in bpy.data.libraries if Path(bpy.path.abspath(l.filepath)).name=='Atheria_Portal_Library.blend')
library.filepath='//../assets/Atheria_Portal_Library.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE.parent/'vestergate/vestergate_with_portals.blend'),relative_remap=False)
library.filepath='//Atheria_Portal_Library.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'vestergate_with_portals.blend'),relative_remap=False)

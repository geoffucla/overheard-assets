#!/usr/bin/env python3
"""Overlay a region's desk guides on the shared ones.
Usage: build_desks.py BASE_DESKS_DIR REGION_KEY OUT_DESKS_DIR
Copies every file in BASE_DESKS_DIR to OUT_DESKS_DIR, then copies regions/REGION_KEY/desks/* over it (a region file replaces
the base file of the same name; a new name, such as 14_texas_tea.md, is added). REGION_KEY bay has no overrides, so its output
is byte-identical to BASE_DESKS_DIR. The regions folder is found next to this script (or in BASE_DESKS_DIR/../regions)."""
import os, sys, shutil
base, key, out = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
rdir = os.path.join(here, 'regions', key, 'desks')
if not os.path.isdir(rdir): rdir = os.path.join(os.path.dirname(os.path.abspath(base)), 'regions', key, 'desks')
os.makedirs(out, exist_ok=True)
for f in sorted(os.listdir(base)): shutil.copy(os.path.join(base, f), os.path.join(out, f))
n = 0
if os.path.isdir(rdir):
    for f in sorted(os.listdir(rdir)):
        shutil.copy(os.path.join(rdir, f), os.path.join(out, f)); n += 1
print(f'{key}: {n} regional desk files applied -> {out}')

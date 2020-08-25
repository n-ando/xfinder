#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from distutils.core import setup
import py2exe

option = {
    "compressed"    :    1,
    "optimize"      :    2,
    "bundle_files"  :    3,
    "includes"      : ["Tkinter", "ttk"]
}

setup(
    options = {
        "py2exe"    :    option
    },
    windows = [{
    "script" : "xfinder.py",
     "icon_resources": [(1, "dist/raspi.ico")]
    }],
    zipfile = None
)

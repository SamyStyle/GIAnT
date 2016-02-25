# -*- coding: utf-8 -*-

from libavg import app
from Draw import MainDrawer
import Options
import F_Formations
import Video
from global_values import resolution

"""start parameter"""
Options.SHOW_F_FORMATIONS = False
Options.LOAD_F_FORMATIONS = False
Options.COLOR_SCHEME = 0
F_Formations.DURATION = 4000
F_Formations.DISTANCE = 80
F_Formations.MAX_DRIFT = 55
F_Formations.ANGLE = 90

Video.path = "csv/M2U00003.MPG"

# minimum recommended resolution: 1040x331 px!
app.App().run(MainDrawer(), app_resolution=resolution["1500x800"])

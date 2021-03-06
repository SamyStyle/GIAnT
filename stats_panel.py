# -*- coding: utf-8 -*-
# GIAnT Group Interaction Analysis Toolkit
# Copyright (C) 2017 Interactive Media Lab Dresden
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import helper
import global_values

from libavg import avg, player

player.loadPlugin("heatmap")

X_MARGIN = 58
LINE_SPACING = 25
COL_WIDTH = 120
COL_MARGIN = 170

class StatsPanel(avg.DivNode):

    def __init__(self, session, vis_params, parent, **kwargs):
        super(StatsPanel, self).__init__(**kwargs)
        self.registerInstance(self, parent)

        self.__session = session
        colors = [vis_params.get_user_color(i) for i in range(4)]
        self.__init_user_legend(colors)

        pos = avg.Point2D(200,0)
        self.__plot = ParallelCoordPlotNode(pos=pos, size=self.size-pos, obj_colors=colors,
                attrib_names = ["Movement<br/>(meters/min)", "Avg. dist from wall<br/>(meters)", "Touches/min"],
                parent=self
        )
        # Calc ranges
        dist_travelled, dist_from_wall, num_touches = self.__get_user_data(0, session.duration)
        for i, attr in enumerate((dist_travelled, dist_from_wall, num_touches)):
            interval = 0, max(attr)*2
            if i == 2:
                is_int = True # num_touches
            else:
                is_int = False
            self.__plot.set_attr_interval(i, interval, is_int)

        vis_params.subscribe(vis_params.CHANGED, self.__update)

    def __init_user_legend(self, colors):
        for i, color in enumerate(colors):
            pos = avg.Point2D(20, 8+44*i)
            avg.RectNode(pos=pos, size=(30,20), color=global_values.COLOR_FOREGROUND, fillcolor=color,
                    fillopacity=1.0, parent=self)
            avg.WordsNode(pos=pos+(40,0), fontsize=global_values.FONT_SIZE, text="User "+str(i+1), parent=self)

    def __update(self, vis_params):
        start_time = vis_params.get_time_interval()[0]
        end_time = vis_params.get_time_interval()[1]

        dist_travelled, dist_from_wall, num_touches = self.__get_user_data(start_time, end_time)
        for i, attr in enumerate((dist_travelled, dist_from_wall, num_touches)):
            self.__plot.set_attr_vals(i, attr)
        self.__plot.set_objs_visible([vis_params.get_user_visible(i) for i in range(4)])

        self.__plot.update()

    def __get_user_data(self, start_time, end_time):
        time_diff = (end_time - start_time)/60  # In minutes
        dist_travelled = []
        dist_from_wall = []
        num_touches = []
        for user in self.__session.users:
            speed = user.getDistTravelled(start_time, end_time)/time_diff      # meters/min
            dist_travelled.append(speed)
            dist_from_wall.append(user.getAvgDistFromWall(start_time, end_time))
            touch_freq = len(user.getTouches(start_time, end_time))/time_diff  # touches/min
            num_touches.append(touch_freq)
        return dist_travelled, dist_from_wall, num_touches


class ParallelCoordPlotAttrib:

    def __init__(self, name):
        self.name = name

        self.min = 0
        self.max = 0
        self.vals = []
        self.is_int = False


class ParallelCoordPlotNode(avg.DivNode):

    MARGIN = (60,20)

    def __init__(self, obj_colors, attrib_names, parent, **kwargs):
        super(ParallelCoordPlotNode, self).__init__(**kwargs)
        self.registerInstance(self, parent)

        self.__obj_colors = obj_colors
        self.__num_objs = len(obj_colors)
        self.__attribs = []
        for name in attrib_names:
            self.__attribs.append(ParallelCoordPlotAttrib(name))

        self.__line_container = avg.DivNode(pos=(0,self.MARGIN[1]*3), size=(self.width, self.height-self.MARGIN[1]*5),
                crop=True, parent=self)
        self.__axis_nodes = []
        self.__attrib_nodes = []
        self.__is_obj_visible = [True] * 4

    def set_attr_vals(self, i, vals):
        assert(self.__num_objs == len(vals))
        self.__attribs[i].vals = vals

    def set_attr_interval(self, i, interval, is_int):
        self.__attribs[i].min = interval[0]
        self.__attribs[i].max = interval[1]
        self.__attribs[i].is_int = is_int

    def set_objs_visible(self, is_obj_visible):
        assert(self.__num_objs == len(is_obj_visible))
        self.__is_obj_visible = is_obj_visible

    def update(self):
        helper.unlink_node_list(self.__axis_nodes)
        self.__axis_nodes = []
        helper.unlink_node_list(self.__attrib_nodes)
        self.__attrib_nodes = []

        width_per_attr = (self.width - self.MARGIN[0] * 2) / (len(self.__attribs) - 1)
        axis_x_pos = [i*width_per_attr + self.MARGIN[0] for i in range(len(self.__attribs))]

        # axes
        for i in range(len(self.__attribs)):
            x_pos = axis_x_pos[i]
            axis_node = avg.DivNode(pos=(x_pos, 0), parent=self)
            avg.LineNode(pos1=(0,self.MARGIN[1]*3), pos2=(0,self.height-self.MARGIN[1]*2),
                    color=global_values.COLOR_FOREGROUND, parent=axis_node)

            attrib = self.__attribs[i]
            avg.WordsNode(pos=(0, 0), alignment="center", fontsize=global_values.FONT_SIZE, text=attrib.name,
                    linespacing=-4, parent=axis_node)
            avg.WordsNode(pos=(0,self.MARGIN[1]*2), alignment="center", fontsize=global_values.FONT_SIZE,
                    text=self.__format_label(attrib.max, attrib.is_int), parent=axis_node)
            avg.WordsNode(pos=(0,self.height-self.MARGIN[1]*2), alignment="center", fontsize=global_values.FONT_SIZE,
                    text=self.__format_label(attrib.min, attrib.is_int), parent=axis_node)
            self.__axis_nodes.append(axis_node)

        axis_height = self.height - self.MARGIN[1]*5

        # Value polylines
        for i in range(self.__num_objs):
            color = self.__obj_colors[i]
            posns = []
            for j, attrib in enumerate(self.__attribs):
                val = float(attrib.vals[i])
                rel_y_pos = (val-attrib.min) / (attrib.max-attrib.min)
                y_pos = axis_height - rel_y_pos * axis_height
                posns.append((axis_x_pos[j], y_pos))
            polyline = avg.PolyLineNode(pos=posns, color=color, parent=self.__line_container)
            polyline.active = self.__is_obj_visible[i]
            self.__attrib_nodes.append(polyline)

    def __format_label(self, val, is_int):
        if is_int:
            return "{}".format(int(val))
        else:
            return "{}".format(round(val,2))

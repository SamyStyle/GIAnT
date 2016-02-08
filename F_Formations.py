# -*- coding: utf-8 -*-
import Util
import math
import libavg
import User
import global_values
import Time_Frame
import time

DURATION = 10000    # minimal duration in ms for formation to be counted as f-formation
DISTANCE = 100      # maximum distance in cm between users
ANGLE = 90         # maximum viewing angle between users
MOVEMENT = 100      # movement limit for users in cm (they need to be standing approx at one spot for a f-formation)


class F_Formations(libavg.DivNode):
    """
    Overlay for F-Formations.
    """

    def __init__(self, parent, **kwargs):
        super(F_Formations, self).__init__(**kwargs)
        self.registerInstance(self, parent)

        self.crop = True

        self.f_formations = []                                      # contains all detected f_formations
        self.f_formation_nodes = []                                 # contains libavg f-formation nodes
        self.f_formation_line_nodes = []                            # contains f-formation indication lines
        self.__step_size = global_values.time_step_size * 32        # step size for drawing f-formations
        self.__user_colors = [Util.get_user_color_as_hex(i, 1) for i in range(len(User.users))]  # colors from scheme

        # load f-formations (can take a few seconds)
        self.load_f_formations()

        # initial update
        self.update_time_frame(Time_Frame.total_range)

    def load_f_formations(self):
        """
        Loading of F-Formation with given specific parameters.
        Iterates over the whole time span for each possible unique user-to-user combination.
        """
        # create tuple of users to check against existing f-formation
        user_list = []
        for i in range(len(User.users)):
            for j in range(len(User.users)):
                if j > i:
                    user_list.append((i, j))

        print "Searching for F-Formations..."
        start_time = time.time()

        # for each user-to-user connection
        for i, users in enumerate(user_list):
            t = Time_Frame.total_range[0]
            timer = 0
            flag = False
            initial_p1 = initial_p2 = (-1000, -1000)
            delta_p1 = delta_p2 = 0
            # go through time by global_values.time_step_size steps
            while t < Time_Frame.total_range[1]:
                pos_values_1 = User.users[users[0]].get_head_position_averaged(int(t/global_values.time_step_size))
                pos_values_2 = User.users[users[1]].get_head_position_averaged(int(t/global_values.time_step_size))
                dir_values_1 = User.users[users[0]].get_head_orientation_averaged(int(t/global_values.time_step_size))
                dir_values_2 = User.users[users[1]].get_head_orientation_averaged(int(t/global_values.time_step_size))
                p1 = (pos_values_1[0], pos_values_1[1])
                p2 = (pos_values_2[0], pos_values_2[1])
                v1 = (dir_values_1[0], dir_values_1[1])
                v2 = (dir_values_2[0], dir_values_2[1])

                formation = self.check_for_f_formation(p1, p2, v1, v2)

                if formation >= 1:
                    if timer == 0:
                        initial_p1 = User.users[users[0]].get_head_position_averaged(int(t/global_values.time_step_size))
                        initial_p1 = (initial_p1[0], initial_p1[1])
                        initial_p2 = User.users[users[1]].get_head_position_averaged(int(t/global_values.time_step_size))
                        initial_p2 = (initial_p2[0], initial_p2[1])
                    if timer >= DURATION:
                        flag = True

                    delta_p1 = point_distance(initial_p1, p1)
                    delta_p2 = point_distance(initial_p2, p2)

                    timer += global_values.time_step_size
                else:
                    if flag:
                        # time, dur, user1, user2
                        self.f_formations.append([t, timer, users[0], users[1]])
                        flag = False
                    timer = 0
                    initial_p1 = initial_p2 = (-1000, -1000)

                t += global_values.time_step_size

        print "Searching done ({}s). Found {} F-Formations.".format(round((time.time() - start_time), 3),
                                                                    len(self.f_formations))

    def check_for_f_formation(self, pos1, pos2, look_vector1, look_vector2):
        """
        Check if two positions, each with a looking direction, are in a F-Formation.
        :param pos1: Position in cm.
        :param pos2: Position in cm.
        :param look_vector1:
        :param look_vector2:
        :return: Strength of F-Formation.
        """

        strength = 0

        # Distance of positions. (1m seems a good approx. Distance for a f-formation. 2m is already pretty far!)
        distance = point_distance(pos1, pos2)
        if distance <= DISTANCE:
            strength = 0.5

            # Viewing angle between the two positions.
            v1 = normalize(look_vector1)
            v2 = normalize(look_vector2)
            pos1_2_dir = normalize((look_vector2[0] - look_vector1[0], look_vector2[1] - look_vector1[1]))
            pos2_1_dir = normalize((look_vector1[0] - look_vector2[0], look_vector1[1] - look_vector2[1]))
            diff_angle_1 = math.degrees(angle(v1, pos1_2_dir))
            diff_angle_2 = math.degrees(angle(v2, pos2_1_dir))

            if diff_angle_1 <= ANGLE and diff_angle_2 <= ANGLE:
                strength = 1

        return strength

    def update_time_frame(self, interval):
        """
        Called by the publisher time_frame to update the visualization to the new interval.
        :param interval: (start, end): new interval start and end as list
        """
        # delete old line nodes and indicators
        for i, node in enumerate(self.f_formation_nodes):
            node.unlink()
        for i, node in enumerate(self.f_formation_line_nodes):
            node.unlink()

        self.__draw_f_formations(interval=interval, colored=True)

    def __draw_f_formations(self, interval, colored=False):
        """
        Colored Polygon for F-Formations.
        :param interval: Current time interval.
        """
        # update f-formation positions (a formation has [time, duration, user1, user2])
        for i, formation in enumerate(self.f_formations):
            duration = formation[1]
            start = max(formation[0] - duration, interval[0])
            end = min(formation[0], interval[1])
            user_1 = formation[2]
            user_2 = formation[3]

            positions_user_1 = []
            positions_user_2 = []
            position_middle = []

            curr_time = start
            while curr_time <= end:
                x = value_to_pixel(curr_time, self.width, interval)
                y_1 = value_to_pixel(User.users[user_1].get_head_position_averaged(
                    int(curr_time/global_values.time_step_size))[0], self.height, global_values.x_range)
                y_2 = value_to_pixel(User.users[user_2].get_head_position_averaged(
                    int(curr_time/global_values.time_step_size))[0], self.height, global_values.x_range)
                thickness_1 = self.__get_thickness(user_1, curr_time)
                thickness_2 = self.__get_thickness(user_2, curr_time)
                if y_1 <= y_2:
                    y_1 += thickness_1
                    y_2 -= thickness_2
                elif abs(y_2 - y_1) <= thickness_1 + thickness_2:
                    pass
                else:
                    y_1 -= thickness_1
                    y_2 += thickness_2

                positions_user_1.append((x, y_1))
                positions_user_2.append((x, y_2))

                if colored:
                    y_half = (y_2 - y_1)/2
                    position_middle.append((x, y_1 + y_half))

                curr_time += self.__step_size
            # add last points to make clean cut at end of interval if step_size > global_values.time_step_size
            else:
                x = value_to_pixel(end, self.width, interval)
                y_1 = value_to_pixel(User.users[user_1].get_head_position_averaged(
                    int(end/global_values.time_step_size))[0], self.height, global_values.x_range)
                y_2 = value_to_pixel(User.users[user_2].get_head_position_averaged(
                    int(end/global_values.time_step_size))[0], self.height, global_values.x_range)
                thickness_1 = self.__get_thickness(user_1, end)
                thickness_2 = self.__get_thickness(user_2, end)
                if y_1 <= y_2:
                    y_1 += thickness_1
                    y_2 -= thickness_2
                elif abs(y_2 - y_1) <= thickness_1 + thickness_2:
                    pass
                else:
                    y_1 -= thickness_1
                    y_2 += thickness_2

                positions_user_1.append((x, y_1))
                positions_user_2.append((x, y_2))
                if colored:
                    y_half = (y_2 - y_1)/2
                    position_middle.append((x, y_1 + y_half))

            # create polygon with points of user 1 and 2
            if colored:
                positions_user_1.extend(list(reversed(position_middle)))
                positions_user_2.extend(list(reversed(position_middle)))
                self.f_formation_nodes.append(libavg.PolygonNode(pos=positions_user_1, parent=self, opacity=0,
                                                                 fillcolor=self.__user_colors[user_1], fillopacity=1,
                                                                 blendmode="add"))
                self.f_formation_nodes.append(libavg.PolygonNode(pos=positions_user_2, parent=self, opacity=0,
                                                                 fillcolor=self.__user_colors[user_2], fillopacity=1,
                                                                 blendmode="add"))
            else:
                positions_user_1.extend(list(reversed(positions_user_2)))
                self.f_formation_nodes.append(libavg.PolygonNode(pos=positions_user_1, parent=self, opacity=0,
                                                                 fillcolor=global_values.COLOR_FOREGROUND,
                                                                 fillopacity=1, blendmode="add"))

            # create indication line
            start_px = value_to_pixel(start, self.width, interval)
            end_px = value_to_pixel(end, self.width, interval)
            self.f_formation_line_nodes.append(libavg.LineNode(pos1=(start_px, 10), pos2=(end_px, 10), strokewidth=5,
                                                               color=global_values.COLOR_FOREGROUND, blendmode="add",
                                                               parent=self))

    def __get_thickness(self, user_id, t):
        """
        Get thickness of line in visualization.
        :param user_id: User ID
        :param t: time in ms
        :return: Thickness in pixel.
        """
        # get z position from user (distance from wall in cm)
        distance = User.users[user_id].get_head_position_averaged(int(t/global_values.time_step_size))[2]
        distance = (distance - global_values.z_range[0]) / float(global_values.z_range[1] - global_values.z_range[0])
        thickness = 2 + pow(distance, 3) * self.height/12
        return thickness/2


def value_to_pixel(value, max_px, interval):
    """
    Calculate pixel position for F-Formation position.
    :param value: Value to be converted into pixel position
    :param max_px: Maximum possible value
    :param interval: Current interval
    :return: pixel position
    """
    a = (interval[1] - interval[0]) / max_px
    return value / a - interval[0] / a


def point_distance(p1, p2):
    """
    Distance between two 2D-Points.
    :param p1: Point 1
    :param p2: Point 2
    :return: Distance
    """
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def dot_product(v1, v2):
    """
    Dot product.
    :param v1: Vector 1
    :param v2: Vector 2
    :return:
    """
    return sum((a * b) for a, b in zip(v1, v2))


def length(v):
    """
    Length of a Vector
    :param v: Vector
    :return: Length
    """
    return math.sqrt(dot_product(v, v))


def normalize(v):
    """
    Normalize vector.
    :param v: Vector
    :return: Normalized Vector
    """
    if length(v) == 0:
        return 0, 0
    else:
        return v[0]/length(v), v[1]/length(v)


def angle(v1, v2):
    """
    Angle between two vectors
    :param v1: Vector 1
    :param v2: Vector 2
    :return: Angle in radians
    """
    if length(v1) == 0 or length(v2) == 0:
        return 0
    else:
        return math.acos(dot_product(v1, v2) / (length(v1) * length(v2)))

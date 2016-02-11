import libavg
from libavg import widget, avg
from Time_Frame import main_time_frame
import global_values
import User
import Util
import Line_Visualization
import F_Formations

SHOW_F_FORMATIONS = True
LOAD_F_FORMATIONS = True
COLOR_SCHEME = 1


class Options(libavg.DivNode):
    def __init__(self, nodes, parent, **kwargs):
        super(Options, self).__init__(**kwargs)
        self.registerInstance(self, parent)

        self.nodes = nodes  # DivNodes containing user data
        self.parent_div = parent

        # rect for coloured border and background
        self.background_rect = libavg.RectNode(pos=(0, 0), size=self.size, parent=self, strokewidth=1, fillopacity=1,
                                               color=global_values.COLOR_BACKGROUND,
                                               fillcolor=global_values.COLOR_BACKGROUND)

        icon_size = (15, 15)
        button_size = (30, 30)
        # rect for play button border
        self.play_rect = libavg.RectNode(pos=(0, self.height - button_size[1]), size=button_size, parent=self,
                                         strokewidth=1, fillopacity=0, color=global_values.COLOR_FOREGROUND,
                                         sensitive=False)

        # play button
        icon_h_size = (icon_size[0]/2, icon_size[1]/2)
        self.play_button = widget.ToggleButton(uncheckedUpNode=avg.ImageNode(href="images/play.png", pos=icon_h_size, size=icon_size),
                                               uncheckedDownNode=avg.ImageNode(href="images/play.png", pos=icon_h_size, size=icon_size),
                                               checkedUpNode=avg.ImageNode(href="images/pause.png", pos=icon_h_size, size=icon_size),
                                               checkedDownNode=avg.ImageNode(href="images/pause.png", pos=icon_h_size, size=icon_size),
                                               # activeAreaNode=avg.DivNode(pos=(-15, -15), size=(30, 30)),
                                               pos=(0, self.play_rect.pos[1]), size=button_size, parent=self)
        self.play_button.subscribe(widget.CheckBox.TOGGLED, lambda checked: self.__play_pause(checked))

        # user buttons
        self.user_buttons = []
        self.user_texts = []
        for i in range(len(User.users)):
            user_color = Util.get_user_color_as_hex(i, 1)
            size = (70, 30)
            self.user_buttons.append(
                widget.ToggleButton(uncheckedUpNode=avg.RectNode(size=size, fillopacity=0, strokewidth=1, color=user_color),
                                    uncheckedDownNode=avg.RectNode(size=size, fillopacity=0, strokewidth=1, color=user_color),
                                    checkedUpNode=avg.RectNode(size=size, fillopacity=1, strokewidth=1, color=user_color, fillcolor=user_color),
                                    checkedDownNode=avg.RectNode(size=size, fillopacity=1, strokewidth=1, color=user_color, fillcolor=user_color),
                                    pos=(i * 80 + 50, self.height - size[1]), size=size, parent=self, enabled=True))
            self.user_buttons[i].checked = True
            self.user_texts.append(avg.WordsNode(color=global_values.COLOR_BACKGROUND,
                                                 parent=self, sensitive=False, text="User {}".format(i + 1),
                                                 alignment="center"))
            self.user_texts[i].pos = (self.user_buttons[i].pos[0] + self.user_buttons[i].width/2, self.user_buttons[i].pos[1] + 6)

        # TODO: the lambda has set the user_id always as the largest i (was always 3) when put in above for loop
        self.user_buttons[0].subscribe(widget.CheckBox.TOGGLED, lambda checked: self.__toggle_user(checked, user_id=0))
        self.user_buttons[1].subscribe(widget.CheckBox.TOGGLED, lambda checked: self.__toggle_user(checked, user_id=1))
        self.user_buttons[2].subscribe(widget.CheckBox.TOGGLED, lambda checked: self.__toggle_user(checked, user_id=2))
        self.user_buttons[3].subscribe(widget.CheckBox.TOGGLED, lambda checked: self.__toggle_user(checked, user_id=3))

        # smoothness slider
        self.smoothness_text = avg.WordsNode(pos=(500, self.height - 32), color=global_values.COLOR_FOREGROUND,
                                             parent=self, text="Smoothness: {}s".format(
                                                 global_values.averaging_count * global_values.time_step_size / 1000))
        self.smoothness_slider = widget.Slider(pos=(495, self.height - 12), width=180, parent=self, range=(2, 2000))
        self.smoothness_slider.thumbPos = global_values.averaging_count
        self.smoothness_slider.subscribe(widget.Slider.THUMB_POS_CHANGED, lambda pos: self.__change_smoothness(pos))
        # smoothness default button
        icon_size = (12, 12)
        button_size = (20, 20)
        icon_h_size = (icon_size[0]/2, icon_size[1]/2)
        self.default_button = widget.ToggleButton(uncheckedUpNode=avg.ImageNode(href="images/reload.png", pos=icon_h_size, size=icon_size),
                                                  uncheckedDownNode=avg.ImageNode(href="images/reload.png", pos=icon_h_size, size=icon_size),
                                                  checkedUpNode=avg.ImageNode(href="images/reload.png", pos=icon_h_size, size=icon_size),
                                                  checkedDownNode=avg.ImageNode(href="images/reload.png", pos=icon_h_size, size=icon_size),
                                                  pos=(650, self.height - 32), size=button_size, parent=self)
        self.default_button.subscribe(widget.CheckBox.TOGGLED, lambda pos: self.__default_smoothness(global_values.default_averaging_count))

        # f-formations button
        size = (100, 30)
        self.f_button = widget.ToggleButton(uncheckedUpNode=avg.RectNode(size=size, fillopacity=0, strokewidth=1, color=global_values.COLOR_FOREGROUND),
                                            uncheckedDownNode=avg.RectNode(size=size, fillopacity=0, strokewidth=1, color=global_values.COLOR_FOREGROUND),
                                            uncheckedDisabledNode=avg.RectNode(size=size, fillopacity=0, strokewidth=1, color=global_values.COLOR_SECONDARY),
                                            checkedUpNode=avg.RectNode(size=size, fillopacity=1, strokewidth=1, color=global_values.COLOR_FOREGROUND, fillcolor=global_values.COLOR_FOREGROUND),
                                            checkedDownNode=avg.RectNode(size=size, fillopacity=1, strokewidth=1, color=global_values.COLOR_FOREGROUND, fillcolor=global_values.COLOR_FOREGROUND),
                                            checkedDisabledNode=avg.RectNode(size=size, fillopacity=0, strokewidth=1, color=global_values.COLOR_SECONDARY),
                                            pos=(self.user_buttons[3].pos[0] + self.user_buttons[3].width + 20, self.height - size[1]),
                                            size=size, parent=self)
        self.f_button.checked = SHOW_F_FORMATIONS and LOAD_F_FORMATIONS
        self.f_button.subscribe(widget.CheckBox.TOGGLED, lambda checked: self.__toggle_f_formations(checked))
        self.f_button_text = avg.WordsNode(pos=(self.f_button.pos[0] + 50, self.f_button.pos[1] + 6),
                                           color=global_values.COLOR_BACKGROUND, parent=self,
                                           text="F-Formations", sensitive=False, alignment="center")
        if not SHOW_F_FORMATIONS: self.__toggle_f_formations(SHOW_F_FORMATIONS and LOAD_F_FORMATIONS)
        if not LOAD_F_FORMATIONS:
            self.f_button.enabled = False
            self.f_button_text.color = global_values.COLOR_FOREGROUND

        # subscribe to global time_frame
        main_time_frame.subscribe(self)

    def __toggle_user(self, checked, user_id):
        if checked:
            User.users[user_id].selected = True
            for i, node in enumerate(self.nodes):
                if isinstance(node, Line_Visualization.Line_Visualization):
                    node.data_div.appendChild(node.user_divs[user_id])
                    self.user_texts[user_id].color = global_values.COLOR_BACKGROUND
        else:
            User.users[user_id].selected = False
            for i, node in enumerate(self.nodes):
                if isinstance(node, Line_Visualization.Line_Visualization):
                    node.user_divs[user_id].unlink()
                    self.user_texts[user_id].color = global_values.COLOR_FOREGROUND

        # publish changes
        main_time_frame.publish()

    def __toggle_f_formations(self, checked):
        if checked:
            for i, node in enumerate(self.nodes):
                if isinstance(node, F_Formations.F_Formations):
                    self.parent_div.appendChild(node)
                    self.f_button_text.color = global_values.COLOR_BACKGROUND
        else:
            for i, node in enumerate(self.nodes):
                if isinstance(node, F_Formations.F_Formations):
                    node.unlink()
                    self.f_button_text.color = global_values.COLOR_FOREGROUND

    def __change_smoothness(self, value):
        global_values.averaging_count = int(value)
        global_values.samples_per_pixel = max(0.1, min(0.3, 50 / value))
        self.smoothness_text.text = "Smoothness: {}s".format(
            global_values.averaging_count * global_values.time_step_size / 1000.0)

        # publish changes
        main_time_frame.publish(draw_lines=True)

    def __default_smoothness(self, value):
        self.__change_smoothness(value)
        self.smoothness_slider.thumbPos = global_values.averaging_count

    def __play_pause(self, checked):
        self.parent_div.play_pause()

    def update_time_frame(self, interval, draw_lines):
        """
        Called by the publisher time_frame to update the visualization if changes are made.
        :param interval: (start, end): new interval start and end as list
        """
        if self.play_button.checked is not main_time_frame.play:
            self.play_button.checked = main_time_frame.play

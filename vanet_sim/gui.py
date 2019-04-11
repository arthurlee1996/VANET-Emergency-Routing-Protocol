"""Contains all graphical user interface (GUI) code."""


__author__ = 'Adam Morrissett', 'Steven M. Hernandez'


import tkinter as tk

from vanet_sim import vehicle_net, road_net, simulation


_GUI_REFRESH_PERIOD = 150  # GUI refresh period in ms
_NODE_DIAMETER = 25  # Diameter of node widgets on GUI
_PADDING = 25  # Padding around canvas to prevent cropping

VEHICLE_COLOR_DEFAULT = '#FFA500'
VEHICLE_COLOR_AFFECTED = "#000000"
VEHICLE_COLOR_RECEIVED_BEFORE_AFFECTED = "#999999"
VEHICLE_COLOR_CURRENT_FORWARDER = "#00FF00"
VEHICLE_COLOR_RECEIVED_EARLY = "#00A500"


class MapFrame(tk.Frame):
    def __init__(self, master, d_time, time_dur, road_map, vehicles, *args,
                 **kwargs):
        super(MapFrame, self).__init__(master, *args, **kwargs)
        self.time_dur = time_dur
        self.road_map = road_map
        self.vehicles = vehicles
        self.simulator = simulation.Simulation(d_time=d_time,
                                               road_map=road_map,
                                               vehicle_net=vehicles)
        self.vehicle_widgets = {}

        c_width, c_height = self._calc_canvas_bounds()
        self.canvas = tk.Canvas(self, width=c_width, height=c_height)
        self.canvas.pack()

        self._draw_map()
        self._draw_vehicles()

    def _draw_map(self):
        """Draws the road map."""

        for key in self.road_map.road_dict:
            r = self.road_map.road_dict[key]

            x1 = (_NODE_DIAMETER / 2) + r.start_node.x_pos
            y1 = (_NODE_DIAMETER / 2) + r.start_node.y_pos
            x2 = (_NODE_DIAMETER / 2) + r.end_node.x_pos
            y2 = (_NODE_DIAMETER / 2) + r.end_node.y_pos

            if r.is_obstructed:
                self.canvas.create_line(x1 + _PADDING, y1 + _PADDING, x2 + _PADDING, y2 + _PADDING, fill='red')
            else:
                self.canvas.create_line(x1 + _PADDING, y1 + _PADDING, x2 + _PADDING, y2 + _PADDING, fill='black')

        # Intersections are drawn after roads so the road lines do not
        # cut into the intersection widgets.
        for key in self.road_map.int_dict:
            i = self.road_map.int_dict[key]

            x1 = i.x_pos
            y1 = i.y_pos
            x2 = i.x_pos + _NODE_DIAMETER
            y2 = i.y_pos + _NODE_DIAMETER

            self.canvas.create_oval(x1 + _PADDING, y1 + _PADDING, x2 + _PADDING, y2 + _PADDING, fill='#FFFFFF')

            x = (_NODE_DIAMETER / 2) + i.x_pos
            y = (_NODE_DIAMETER / 2) + i.y_pos

            self.canvas.create_text(x + _PADDING, y + _PADDING, text=i.name)

    def _calc_canvas_bounds(self):
        """Calculates the minimum canvas size to fit road network."""

        max_x = 0
        max_y = 0

        for key in self.road_map.int_dict:
            i = self.road_map.int_dict[key]

            if i.x_pos > max_x:
                max_x = i.x_pos

            if i.y_pos > max_y:
                max_y = i.y_pos

        return max_x + _NODE_DIAMETER + (2 * _PADDING), max_y + _NODE_DIAMETER + (2 * _PADDING)

    def _draw_vehicles(self):
        """Draws all vehicles in their starting positions."""

        for v in vehicles:
            x0 = v.x + (_NODE_DIAMETER / 2) - 5
            y0 = v.y + (_NODE_DIAMETER / 2) - 5
            x1 = v.x + (_NODE_DIAMETER / 2) + 5
            y1 = v.y + (_NODE_DIAMETER / 2) + 5

            self.vehicle_widgets[v.id] = self.canvas.create_oval(
                x0 + _PADDING, y0 + _PADDING, x1 + _PADDING, y1 + _PADDING, fill=VEHICLE_COLOR_DEFAULT)

    def _redraw_vehicles(self):
        for v in self.vehicles:
            w_id = self.vehicle_widgets[v.id]
            w_pos = self.canvas.coords(w_id)

            # Movement updates are based on widget midpoints
            mid_x0 = (w_pos[0] + w_pos[2]) / 2
            mid_y0 = (w_pos[1] + w_pos[3]) / 2
            mid_x1 = v.x + _NODE_DIAMETER / 2
            mid_y1 = v.y + _NODE_DIAMETER / 2

            d_x = mid_x1 - mid_x0
            d_y = mid_y1 - mid_y0

            self.canvas.move(w_id, d_x + _PADDING, d_y + _PADDING)

            fill_color = None
            if v.is_current_forwarder:
                fill_color = VEHICLE_COLOR_CURRENT_FORWARDER
            elif v.affected_at is not None and v.received_at is not None and v.affected_at < v.received_at:
                fill_color = VEHICLE_COLOR_RECEIVED_BEFORE_AFFECTED
            elif v.affected_at is not None and v.received_at is None:
                fill_color = VEHICLE_COLOR_AFFECTED
            elif v.received_at is not None and v.affected_at is None:
                fill_color = VEHICLE_COLOR_RECEIVED_EARLY

            if fill_color is not None:
                self.canvas.itemconfig(w_id, fill=fill_color)

    def step_sim(self):
        """Steps simulation and updates GUI."""

        self.simulator.step()
        self._redraw_vehicles()
        self.canvas.update()

        if self.simulator.cur_time <= self.time_dur:
            self.canvas.after(_GUI_REFRESH_PERIOD, self.step_sim)


if __name__ == '__main__':
    road_map = road_net.RoadMap(intersection_file='../intersections.csv',
                                road_file='../roads.csv')

    vehicles = vehicle_net.build_vehicle_net(filepath='../vehicles.csv',
                                             road_map=road_map)

    root = tk.Tk()
    root.title('PySim')
    frame = MapFrame(root, d_time=1, time_dur=50,
                     road_map=road_map, vehicles=vehicles)
    frame.pack()
    frame.step_sim()
    root.mainloop()

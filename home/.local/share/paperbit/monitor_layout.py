"""Wait for GDK monitor geometry and rebuild layouts when it changes."""
from gi.repository import GLib


class MonitorLayouts:
    def __init__(self, display, create, destroy):
        self.create = create
        self.destroy = destroy
        self.monitors = {}
        self.display = display
        self.handlers = [display.connect('monitor-added', self.watch),
                         display.connect('monitor-removed', self.remove)]
        for index in range(display.get_n_monitors()):
            self.watch(display, display.get_monitor(index))

    def watch(self, display, monitor):
        if monitor in self.monitors:
            return
        state = {'timer': None, 'layout': None, 'candidate': None}
        self.monitors[monitor] = state
        state['handlers'] = [monitor.connect('notify::geometry', self.changed),
                             monitor.connect('notify::scale-factor', self.changed)]
        self.changed(monitor)

    def changed(self, monitor, *unused):
        state = self.monitors.get(monitor)
        if state is None:
            return
        if state['timer'] is not None:
            GLib.source_remove(state['timer'])
        state['candidate'] = None
        state['timer'] = GLib.timeout_add(250, self.settle, monitor)

    def settle(self, monitor):
        state = self.monitors[monitor]
        geometry = monitor.get_geometry()
        layout = (geometry.x, geometry.y, geometry.width, geometry.height,
                  monitor.get_scale_factor())
        # A newly announced Wayland output can initially report 0 x 0.
        # Require two equal, valid snapshots before laying out its panels.
        if geometry.width <= 0 or geometry.height <= 0:
            state['candidate'] = None
            return True
        if layout != state['candidate']:
            state['candidate'] = layout
            return True
        if layout != state['layout']:
            if state['layout'] is not None:
                self.destroy(self.display, monitor)
            self.create(self.display, monitor)
            state['layout'] = layout
        state['timer'] = None
        return False

    def remove(self, display, monitor):
        state = self.monitors.pop(monitor, None)
        if state is None:
            return
        if state['timer'] is not None:
            GLib.source_remove(state['timer'])
        for handler in state['handlers']:
            monitor.disconnect(handler)
        self.destroy(display, monitor)

    def close(self):
        for handler in self.handlers:
            self.display.disconnect(handler)
        for monitor in list(self.monitors):
            self.remove(self.display, monitor)

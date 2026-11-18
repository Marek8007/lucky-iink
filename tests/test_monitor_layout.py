"""Regression checks for monitors announced before their geometry is ready."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       'home/.local/share/paperbit'))
from monitor_layout import MonitorLayouts


class Clock:
    def __init__(self):
        self.sources = {}
        self.next_id = 0

    def timeout_add(self, interval, callback, *args):
        self.next_id += 1
        self.sources[self.next_id] = (callback, args)
        return self.next_id

    def source_remove(self, source):
        del self.sources[source]

    def tick(self):
        for source, (callback, args) in list(self.sources.items()):
            if not callback(*args):
                self.sources.pop(source, None)


class MonitorLayoutTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        patcher = patch('monitor_layout.GLib', self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.monitor = Mock()
        self.geometry(0, 0)
        self.monitor.get_scale_factor.return_value = 1
        self.display = Mock()
        self.display.get_n_monitors.return_value = 1
        self.display.get_monitor.return_value = self.monitor
        self.create, self.destroy = Mock(), Mock()
        self.layouts = MonitorLayouts(self.display, self.create, self.destroy)
        self.addCleanup(self.layouts.close)

    def geometry(self, width, height):
        self.monitor.get_geometry.return_value = SimpleNamespace(
            x=0, y=-height, width=width, height=height)

    def ready(self):
        self.geometry(1920, 1080)
        self.clock.tick()
        self.clock.tick()

    def test_boot_waits_for_nonzero_stable_geometry(self):
        for _ in range(4):
            self.clock.tick()
        self.create.assert_not_called()
        self.geometry(1920, 1080)
        self.clock.tick()
        self.create.assert_not_called()
        self.clock.tick()
        self.create.assert_called_once_with(self.display, self.monitor)
        self.assertFalse(self.clock.sources)

    def test_resolution_changes_rebuild_after_settling(self):
        self.ready()
        self.geometry(1280, 720)
        self.layouts.changed(self.monitor)
        self.clock.tick()
        self.geometry(1600, 900)
        self.clock.tick()
        self.destroy.assert_not_called()
        self.clock.tick()
        self.destroy.assert_called_once_with(self.display, self.monitor)
        self.assertEqual(self.create.call_count, 2)

    def test_repeated_notifications_do_not_duplicate_panels(self):
        self.ready()
        self.layouts.changed(self.monitor)
        self.clock.tick()
        self.clock.tick()
        self.create.assert_called_once()
        self.destroy.assert_not_called()

    def test_scale_change_rebuilds(self):
        self.ready()
        self.monitor.get_scale_factor.return_value = 2
        self.layouts.changed(self.monitor)
        self.clock.tick()
        self.clock.tick()
        self.assertEqual(self.create.call_count, 2)

    def test_unplug_cancels_pending_layout_and_replug_works(self):
        self.layouts.remove(self.display, self.monitor)
        self.assertFalse(self.clock.sources)
        self.clock.tick()
        self.create.assert_not_called()
        self.layouts.watch(self.display, self.monitor)
        self.ready()
        self.create.assert_called_once()


if __name__ == '__main__':
    unittest.main()

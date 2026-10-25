"""Windows Qt smoke test. Run on the GitHub Actions Windows runner, before packaging.

Exercises the real Qt event loop and detects errors thrown during repaint.
"""
import os
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from studio.app import MainWindow


def main():
    app = QApplication.instance() or QApplication([])
    failures = []
    def catch_exception(kind, exc, tb):
        failures.append(''.join(traceback.format_exception(kind, exc, tb)))
        app.quit()
    sys.excepthook = catch_exception
    # Avoid prompting about unrelated user recovery data in CI.
    MainWindow.offer_recovery = lambda self: None
    win = MainWindow()
    win.autosave_timer.stop()
    win.show()
    stages = []
    for _ in range(10):
        stages.extend((lambda: win.showMaximized(), lambda: win.showNormal()))
    stages += [
        lambda: win.resize(1200, 800),
        lambda: win.nft_manager_dock.show(),
        lambda: win.nft_manager_dock.hide(),
        lambda: win.animator_dock.show(),
        lambda: win.animator_dock.hide(),
        lambda: win.advanced_animator_dock.show(),
        lambda: win.advanced_animator_dock.hide(),
        lambda: win.restore_snapshot(win.snapshot()),
        lambda: win.canvas.update(),
    ]
    def step(index=0):
        if failures or index >= len(stages):
            app.quit()
            return
        try:
            stages[index]()
            app.processEvents()
        except Exception:
            failures.append(traceback.format_exc())
            app.quit()
            return
        QTimer.singleShot(70, lambda: step(index + 1))
    QTimer.singleShot(150, step)
    QTimer.singleShot(20000, lambda: (failures.append('GUI smoke test timed out'), app.quit()))
    app.exec()
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        return 1
    print('Windows GUI smoke test passed: maximize/restore, dock lifecycle, snapshot, repaint')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

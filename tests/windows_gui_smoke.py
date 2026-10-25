
"""Windows Qt smoke test with startup and event-loop diagnostics."""

import sys
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


def main():
    print("SMOKE: Starting Qt application", flush=True)
    app = QApplication.instance() or QApplication([])
    failures = []

    def catch_exception(kind, exc, tb):
        message = "".join(traceback.format_exception(kind, exc, tb))
        failures.append(message)
        print(message, file=sys.stderr, flush=True)
        app.quit()

    sys.excepthook = catch_exception

    print("SMOKE: Importing MainWindow", flush=True)
    from studio.app import MainWindow

    print("SMOKE: Creating MainWindow", flush=True)
    MainWindow.offer_recovery = lambda self: None
    win = MainWindow()

    if hasattr(win, "autosave_timer"):
        win.autosave_timer.stop()

    print("SMOKE: Showing window", flush=True)
    win.show()

    stages = []

    for _ in range(10):
        stages.extend([
            lambda: win.showMaximized(),
            lambda: win.showNormal(),
        ])

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
            print(
                f"SMOKE: Running stage {index + 1}/{len(stages)}",
                flush=True,
            )
            stages[index]()
            app.processEvents()
        except Exception:
            message = traceback.format_exc()
            failures.append(message)
            print(message, file=sys.stderr, flush=True)
            app.quit()
            return

        QTimer.singleShot(70, lambda: step(index + 1))

    def timeout():
        failures.append("GUI smoke test timed out")
        print("SMOKE: Timeout", file=sys.stderr, flush=True)
        app.quit()

    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(timeout)
    timeout_timer.start(20000)

    QTimer.singleShot(150, step)

    print("SMOKE: Entering Qt event loop", flush=True)
    app.exec()
    timeout_timer.stop()

    if failures:
        print("\n".join(failures), file=sys.stderr, flush=True)
        return 1

    print("Windows GUI smoke test passed", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise


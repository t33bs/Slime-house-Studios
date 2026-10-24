# v35 startup crash hotfix

Fixes `AttributeError: 'MainWindow' object has no attribute 'mask_brush'` during launch.

Root cause: v34 connected `self.mask_brush.valueChanged` before creating `self.mask_brush`. v35 moves the signal connection immediately after the QSpinBox is created.

Verification: 95 automated tests passed, 45 subtests passed, including a new regression test asserting correct initialization order. Windows EXE startup has not yet been tested. Build this source through the existing GitHub Actions workflow.

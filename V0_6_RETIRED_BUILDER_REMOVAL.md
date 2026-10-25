# v0.6 — Retired Desktop Pet Builder cleanup

Removed the retired dock/widget construction, hidden button, dock lifecycle hooks, canvas overlay, mouse tools, cursor entries, and 26 legacy builder helper methods. Snapshot restoration no longer accesses destroyed pet widgets. Legacy `pet_anchors` and `pet_regions` JSON values are preserved for backwards compatibility with existing projects. The separate Friendly Animator repository is untouched.

Four obsolete GUI tests were archived under `retired_tests/` (renamed `.retired` so pytest does not collect them); the phase/workshop tests now check removal, and a dedicated regression test was added. The legacy `pet_sprite_wizard.py` backend and related backend tests remain for now; these are not exposed through the Studio UI. No Windows EXE has been built or validated from this source.

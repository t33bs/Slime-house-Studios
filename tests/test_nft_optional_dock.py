import unittest
from pathlib import Path
APP=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text(encoding='utf-8')
class NFTDockTests(unittest.TestCase):
    def test_optional_dock(self):
        self.assertIn("self.nft_manager_dock=QDockWidget(",APP)
        self.assertIn("self.nft_manager_dock.hide()",APP)
        self.assertIn("self.nft_manager_button.clicked.connect(self.toggle_nft_manager)",APP)
    def test_worksheet_and_traits_in_nft_dock(self):
        self.assertIn("self.nft_manager_tabs.addTab(worksheet,'NFT Worksheet')",APP)
        self.assertIn("self.nft_manager_tabs.addTab(nft,'Trait Generator')",APP)
        self.assertNotIn("self.tabs.addTab(worksheet,'NFT Worksheet')",APP)
    def test_preserve_worksheet_state(self):
        self.assertIn("self.nft_manager_dock.hide()",APP)
        self.assertNotIn("self.nft_manager_dock.setWidget(None)",APP)

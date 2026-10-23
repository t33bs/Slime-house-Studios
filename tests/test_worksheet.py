import csv, tempfile, unittest
from pathlib import Path
from openpyxl import Workbook
from studio.worksheet import NFTWorksheet

class WorksheetTests(unittest.TestCase):
    def test_csv_lookup_edit_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'traits.csv'
            path.write_text('NFT Number,Fur,Sword\n0059,Ginger,Katana\n0060,Gold,Claymore\n',encoding='utf-8')
            sheet=NFTWorksheet();self.assertEqual(sheet.load(path),2)
            i,row=sheet.lookup('59');self.assertEqual(row['Fur'],'Ginger')
            sheet.edit(i,{'Sword':'Rapier'});out=Path(tmp)/'new.csv';sheet.export(out)
            reload=NFTWorksheet();reload.load(out);self.assertEqual(reload.lookup('0059')[1]['Sword'],'Rapier')
            self.assertEqual(sheet.lookup('0060')[1]['Fur'],'Gold')
    def test_xlsx_lookup_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'traits.xlsx';wb=Workbook();ws=wb.active
            ws.append(['Token ID','Armor','Background']);ws.append([59,'Emerald','Burning room']);wb.save(path)
            sheet=NFTWorksheet();sheet.load(path);i,row=sheet.lookup('0059')
            self.assertEqual(row['Armor'],'Emerald');sheet.edit(i,{'Armor':'Platinum'})
            out=Path(tmp)/'updated.xlsx';sheet.export(out)
            reread=NFTWorksheet();reread.load(out);self.assertEqual(reread.lookup('59')[1]['Armor'],'Platinum')
    def test_not_found_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.csv';p.write_text('ID,Fur\n1,Red\n001,Blue\n')
            s=NFTWorksheet();s.load(p)
            with self.assertRaises(ValueError):s.lookup('1')
            with self.assertRaises(LookupError):s.lookup('3')
    def test_reject_invalid_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.csv';p.write_text('ID,ID\n1,2\n')
            with self.assertRaises(ValueError):NFTWorksheet().load(p)

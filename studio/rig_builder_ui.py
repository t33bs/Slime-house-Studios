"""Compact creature rig and sprite-sheet builder dialog."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QListWidget,QSpinBox,QComboBox,QFileDialog,QMessageBox,QFormLayout,QInputDialog,QScrollArea
from .creature_rig import CreatureRig
from .app import qimage

class RigBuilderDialog(QDialog):
    def __init__(self,parent=None,size=(128,128)):
        super().__init__(parent);self.setWindowTitle('Creature Rig & Sprite Sheet Builder');self.resize(790,620)
        self.rig=CreatureRig(size);self.selected=-1
        root=QVBoxLayout(self)
        root.addWidget(QLabel('1. Import transparent body-part PNGs  →  2. Position parts  →  3. Save frames  →  4. Export sheet'))
        main=QHBoxLayout();root.addLayout(main)
        left=QVBoxLayout();main.addLayout(left,1)
        self.parts=QListWidget();self.parts.currentRowChanged.connect(self.select_part);left.addWidget(self.parts)
        add=QPushButton('+ Add body-part PNG');add.clicked.connect(self.add_part);left.addWidget(add)
        form=QFormLayout();left.addLayout(form)
        self.x=QSpinBox();self.y=QSpinBox()
        for widget in (self.x,self.y):widget.setRange(-2048,2048);widget.valueChanged.connect(self.update_position)
        form.addRow('X position',self.x);form.addRow('Y position',self.y)
        self.animation=QComboBox();self.animation.setEditable(True);self.animation.addItems(['Idle','Walking','Eating','Sleeping','Happy bounce','Custom'])
        left.addWidget(QLabel('Animation name'));left.addWidget(self.animation)
        save_frame=QPushButton('Save current pose as next frame');save_frame.clicked.connect(self.save_frame);left.addWidget(save_frame)
        self.count=QLabel('0 frames saved');left.addWidget(self.count)
        right=QVBoxLayout();main.addLayout(right,2)
        self.preview=QLabel();self.preview.setMinimumSize(350,350);self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet('background:#26303b;border:1px solid #536454;');right.addWidget(self.preview,1)
        right.addWidget(QLabel('Each saved frame remembers every part position. Select a part to adjust its pose.'))
        self.columns=QSpinBox();self.columns.setRange(1,32);self.columns.setValue(4)
        right.addWidget(QLabel('Sheet columns'));right.addWidget(self.columns)
        actions=QHBoxLayout();right.addLayout(actions)
        for label,fn in [('Save editable rig',self.save_project),('Open rig',self.open_project),('Export PNG + JSON',self.export)]:
            button=QPushButton(label);button.clicked.connect(fn);actions.addWidget(button)
        self.refresh()
    def refresh(self):
        image=self.rig.render();pix=QPixmap.fromImage(qimage(image))
        self.preview.setPixmap(pix.scaled(350,350,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation))
        self.count.setText(f'{sum(len(v) for v in self.rig.animations.values())} frames saved')
    def add_part(self):
        from PIL import Image
        files,_=QFileDialog.getOpenFileNames(self,'Import body-part PNGs','','PNG images (*.png)')
        for file in files:
            self.rig.add_part(Path(file).stem,Image.open(file).convert('RGBA'))
            self.parts.addItem(Path(file).stem)
        if files:self.parts.setCurrentRow(len(self.rig.parts)-1)
        self.refresh()
    def select_part(self,index):
        self.selected=index
        if index<0 or index>=len(self.rig.parts):return
        part=self.rig.parts[index]
        self.x.blockSignals(True);self.y.blockSignals(True)
        self.x.setValue(part['x']);self.y.setValue(part['y'])
        self.x.blockSignals(False);self.y.blockSignals(False)
    def update_position(self):
        if 0<=self.selected<len(self.rig.parts):
            self.rig.parts[self.selected]['x']=self.x.value();self.rig.parts[self.selected]['y']=self.y.value();self.refresh()
    def save_frame(self):
        if not self.rig.parts:QMessageBox.warning(self,'No parts','Import a body-part PNG first.');return
        name=self.animation.currentText().strip() or 'Custom';self.rig.save_frame(name);self.refresh()
    def save_project(self):
        path,_=QFileDialog.getSaveFileName(self,'Save editable creature rig','creature.rig.json','Rig projects (*.json)')
        if path:self.rig.save_project(path)
    def open_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Open creature rig','','Rig projects (*.json)')
        if not path:return
        try:self.rig=CreatureRig.load_project(path);self.parts.clear();self.parts.addItems([p['name'] for p in self.rig.parts]);self.refresh()
        except Exception as exc:QMessageBox.warning(self,'Open failed',str(exc))
    def export(self):
        folder=QFileDialog.getExistingDirectory(self,'Export transparent sprite sheet')
        if not folder:return
        try:
            path=self.rig.export(folder,columns=self.columns.value());QMessageBox.information(self,'Exported',f'Saved {path.name} and matching JSON metadata.')
        except Exception as exc:QMessageBox.warning(self,'Export failed',str(exc))

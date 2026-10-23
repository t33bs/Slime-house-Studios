"""Native Qt interface; no browser, Electron or JavaScript."""
import json
import sys
from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt, QRect, QPoint, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QPen, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QListWidget, QFileDialog, QMessageBox, QComboBox,
    QSpinBox, QFormLayout, QGroupBox, QInputDialog, QCheckBox)
from .core import Layer, composite, frames_for, export_apng

def resource_path(relative):
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / relative



def qimage(pil):
    img = pil.convert('RGBA')
    return QImage(img.tobytes('raw', 'RGBA'), img.width, img.height, QImage.Format.Format_RGBA8888).copy()


class Slime(QWidget):
    def __init__(self, color='#8cbba1'):
        super().__init__(); self.color = QColor(color); self.setFixedSize(50, 42)
    def paintEvent(self, event):
        p=QPainter(self); p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.color)
        # Transparent background and square, quiet pixel shapes.
        for x,y,w,h in [(12,8,26,5),(8,13,34,6),(5,19,40,13),(10,32,30,5)]:p.drawRect(x,y,w,h)
        p.setBrush(QColor('#27313a'));p.drawRect(17,22,4,5);p.drawRect(30,22,4,5)
        p.drawRect(23,30,6,2)


class Canvas(QWidget):
    def __init__(self, window):
        super().__init__();self.window=window;self.zoom=4;self.drag=None;self.setMinimumSize(350,350)
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#161d27'))
        w,h=self.window.size_px; z=min((self.width()-24)/w,(self.height()-24)/h,12)
        z=max(.1,z);self.zoom=z; self.ox=(self.width()-w*z)/2;self.oy=(self.height()-h*z)/2
        for y in range(0,h,8):
            for x in range(0,w,8):
                p.fillRect(QRect(round(self.ox+x*z),round(self.oy+y*z),round(min(8,w-x)*z+1),round(min(8,h-y)*z+1)),QColor('#293240' if (x//8+y//8)%2 else '#343e4c'))
        image=self.window.current_image()
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,False)
        p.drawImage(QRect(round(self.ox),round(self.oy),round(w*z),round(h*z)),qimage(image))
        p.setPen(QPen(QColor('#93c6ae'),1));p.drawRect(QRect(round(self.ox),round(self.oy),round(w*z),round(h*z)))
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton and self.window.selected_layer() is not None:
            self.drag=(e.position().x(),e.position().y(),self.window.selected_layer().x,self.window.selected_layer().y)
    def mouseMoveEvent(self,e):
        if self.drag:
            mx,my,x,y=self.drag; layer=self.window.selected_layer()
            if layer:
                layer.x=x+round((e.position().x()-mx)/self.zoom)
                layer.y=y+round((e.position().y()-my)/self.zoom)
                self.window.update_controls();self.update()
    def mouseReleaseEvent(self,e):self.drag=None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Slime House Studios');self.setWindowIcon(QIcon(str(resource_path('assets/slime_mascot.png'))));self.resize(1200,760)
        self.size_px=(64,64);self.layers=[];self.preview_frames=[];self.preview_index=0
        self.timer=QTimer(self);self.timer.timeout.connect(self.next_frame)
        root=QWidget();self.setCentralWidget(root);layout=QHBoxLayout(root)
        left=QVBoxLayout();layout.addLayout(left,1)
        left.addWidget(QLabel('SLIME HOUSE STUDIOS'))
        left.addWidget(QLabel('Pixel Art · Animation · NFT Creation'))
        slimes=QHBoxLayout();slimes.addWidget(Slime());slimes.addWidget(Slime('#91adc5'));slimes.addWidget(Slime('#c1a4be'));left.addLayout(slimes)
        self.canvas_sizes=QComboBox();self.canvas_sizes.addItems(['32 × 32','64 × 64','128 × 128','256 × 256','512 × 512','Custom…']);self.canvas_sizes.setCurrentIndex(1)
        self.canvas_sizes.currentIndexChanged.connect(self.change_size);left.addWidget(QLabel('Canvas size'));left.addWidget(self.canvas_sizes)
        add=QPushButton('Import transparent PNG layer');add.clicked.connect(self.import_png);left.addWidget(add)
        self.layer_list=QListWidget();self.layer_list.currentRowChanged.connect(self.update_controls);left.addWidget(self.layer_list)
        move=QHBoxLayout()
        for name,fn in [('↑',lambda:self.move_layer(1)),('↓',lambda:self.move_layer(-1)),('Remove',self.remove_layer)]:
            b=QPushButton(name);b.clicked.connect(fn);move.addWidget(b)
        left.addLayout(move)
        form=QFormLayout();self.x_spin=QSpinBox();self.y_spin=QSpinBox()
        for s in (self.x_spin,self.y_spin):s.setRange(-4096,4096);s.valueChanged.connect(self.set_layer_position)
        form.addRow('Layer X',self.x_spin);form.addRow('Layer Y',self.y_spin);left.addLayout(form)
        self.canvas=Canvas(self);layout.addWidget(self.canvas,3)
        right=QVBoxLayout();layout.addLayout(right,1)
        right.addWidget(QLabel('ANIMATION STUDIO'))
        self.effect=QComboBox();self.effect.addItems(['Float','Bounce','Twitch','Pulse','Blink']);right.addWidget(self.effect)
        self.frames=QSpinBox();self.frames.setRange(2,60);self.frames.setValue(8)
        self.strength=QSpinBox();self.strength.setRange(1,40);self.strength.setValue(3)
        self.duration=QSpinBox();self.duration.setRange(20,2000);self.duration.setValue(100)
        f=QFormLayout();f.addRow('Frames',self.frames);f.addRow('Strength (px)',self.strength);f.addRow('Frame duration (ms)',self.duration);right.addLayout(f)
        preview=QPushButton('Preview animation');preview.clicked.connect(self.start_preview);right.addWidget(preview)
        stop=QPushButton('Stop preview');stop.clicked.connect(self.stop_preview);right.addWidget(stop)
        export=QPushButton('Export verified APNG');export.clicked.connect(self.save_apng);right.addWidget(export)
        png=QPushButton('Export transparent PNG');png.clicked.connect(self.save_png);right.addWidget(png)
        save=QPushButton('Save project JSON');save.clicked.connect(self.save_project);right.addWidget(save)
        load=QPushButton('Open project JSON');load.clicked.connect(self.load_project);right.addWidget(load)
        right.addWidget(QLabel('Tip: select a layer, then drag it on the canvas.'))
        right.addStretch()
        self.setStyleSheet('''QWidget{background:#1b222e;color:#d8e3e5;font-size:13px} QPushButton,QComboBox,QSpinBox,QListWidget{background:#2b3544;border:1px solid #445064;border-radius:6px;padding:7px} QPushButton:hover{background:#3c5260} QPushButton:pressed{background:#496d65} QListWidget::item:selected{background:#496d65} QLabel{border:none}''')
    def current_image(self):
        return self.preview_frames[self.preview_index] if self.preview_frames else composite(self.layers,self.size_px)
    def selected_layer(self):
        i=self.layer_list.currentRow();return self.layers[i] if 0<=i<len(self.layers) else None
    def redraw(self):self.canvas.update()
    def stop_preview(self):self.timer.stop();self.preview_frames=[];self.redraw()
    def change_size(self):
        text=self.canvas_sizes.currentText()
        if text=='Custom…':
            w,ok=QInputDialog.getInt(self,'Canvas width','Width',64,1,2048)
            if not ok:return
            h,ok=QInputDialog.getInt(self,'Canvas height','Height',64,1,2048)
            if not ok:return
            self.size_px=(w,h)
        else:
            n=int(text.split(' ')[0]);self.size_px=(n,n)
        self.stop_preview()
    def import_png(self):
        path,_=QFileDialog.getOpenFileName(self,'Import layer','','Images (*.png *.webp)')
        if path:
            try:
                with Image.open(path) as img: layer=Layer(Path(path).name,img.convert('RGBA').copy())
                self.layers.append(layer);self.layer_list.addItem(layer.name);self.layer_list.setCurrentRow(len(self.layers)-1);self.stop_preview()
            except Exception as e:QMessageBox.critical(self,'Import failed',str(e))
    def update_controls(self,*args):
        l=self.selected_layer()
        for spin,v in ((self.x_spin,l.x if l else 0),(self.y_spin,l.y if l else 0)):
            spin.blockSignals(True);spin.setValue(v);spin.blockSignals(False)
    def set_layer_position(self):
        l=self.selected_layer()
        if l:l.x=self.x_spin.value();l.y=self.y_spin.value();self.stop_preview()
    def move_layer(self,d):
        i=self.layer_list.currentRow();j=i+d
        if i<0 or not 0<=j<len(self.layers):return
        self.layers[i],self.layers[j]=self.layers[j],self.layers[i]
        item=self.layer_list.takeItem(i);self.layer_list.insertItem(j,item);self.layer_list.setCurrentRow(j);self.stop_preview()
    def remove_layer(self):
        i=self.layer_list.currentRow()
        if i>=0:self.layers.pop(i);self.layer_list.takeItem(i);self.stop_preview()
    def make_frames(self):return frames_for(self.layers,self.size_px,self.effect.currentText(),self.frames.value(),self.strength.value())
    def start_preview(self):
        self.preview_frames=self.make_frames();self.preview_index=0;self.timer.start(self.duration.value());self.redraw()
    def next_frame(self):
        if self.preview_frames:self.preview_index=(self.preview_index+1)%len(self.preview_frames);self.redraw()
    def save_apng(self):
        path,_=QFileDialog.getSaveFileName(self,'Save APNG','animation.apng','Animated PNG (*.apng)')
        if not path:return
        try:
            result=export_apng(self.make_frames(),path,self.duration.value());QMessageBox.information(self,'Export verified',f'APNG saved: {result}')
        except Exception as e:QMessageBox.warning(self,'Export failed',str(e))
    def save_png(self):
        path,_=QFileDialog.getSaveFileName(self,'Save PNG','sprite.png','PNG (*.png)')
        if path:composite(self.layers,self.size_px).save(path)
    def save_project(self):
        import base64,io
        path,_=QFileDialog.getSaveFileName(self,'Save project','sprite_project.json','JSON (*.json)')
        if not path:return
        layers=[]
        for l in self.layers:
            b=io.BytesIO();l.image.save(b,format='PNG');layers.append(dict(name=l.name,x=l.x,y=l.y,visible=l.visible,png=base64.b64encode(b.getvalue()).decode()))
        Path(path).write_text(json.dumps(dict(size=self.size_px,layers=layers),indent=2),encoding='utf-8')
    def load_project(self):
        import base64,io
        path,_=QFileDialog.getOpenFileName(self,'Open project','','JSON (*.json)')
        if not path:return
        try:
            obj=json.loads(Path(path).read_text(encoding='utf-8'))
            size=tuple(obj['size'])
            if len(size)!=2 or not all(isinstance(n,int) and 1<=n<=2048 for n in size):raise ValueError('Invalid canvas size')
            layers=[]
            for entry in obj['layers']:
                with Image.open(io.BytesIO(base64.b64decode(entry['png']))) as im:img=im.convert('RGBA').copy()
                layers.append(Layer(entry['name'],img,int(entry['x']),int(entry['y']),bool(entry['visible'])))
            self.size_px=size;self.layers=layers;self.layer_list.clear()
            for l in layers:self.layer_list.addItem(l.name)
            self.stop_preview()
        except Exception as e:QMessageBox.critical(self,'Load failed',str(e))


def main():
    app=QApplication([]);app.setApplicationName('Slime House Studios');app.setWindowIcon(QIcon(str(resource_path('assets/slime_mascot.png'))));win=MainWindow();win.show();app.exec()

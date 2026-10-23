"""Slime House Studios native Qt editor."""
import base64, io, json, sys, csv
from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QPushButton,QLabel,QListWidget,QFileDialog,QMessageBox,QComboBox,QSpinBox,QDoubleSpinBox,QFormLayout,QInputDialog,QTabWidget,QColorDialog,QLineEdit,QCheckBox,QScrollArea,QSlider,QTableWidget,QTableWidgetItem,QHeaderView,QDockWidget,QSizePolicy,QGroupBox)
from .history import UndoHistory, capture, decode, atomic_write
from .worksheet import NFTWorksheet
from .core import Layer,Region,EFFECTS,composite,transformed,paint_pixel,frames_for,compose_timeline_frames,export_apng,export_gif,export_sprite_sheet,generate_traits

def resource_path(p):return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))/p

def qimage(im):
    im=im.convert('RGBA');return QImage(im.tobytes(),im.width,im.height,QImage.Format.Format_RGBA8888).copy()

class Canvas(QWidget):
    def __init__(self,main):
        super().__init__();self.main=main;self.setMinimumSize(450,450);self.drag=None;self.setMouseTracking(True)
    def coord(self,pos):return round((pos.x()-self.ox)/self.zoom),round((pos.y()-self.oy)/self.zoom)
    def rect_screen(self,rect):
        x,y,w,h=rect;return QRect(round(self.ox+x*self.zoom),round(self.oy+y*self.zoom),max(1,round(w*self.zoom)),max(1,round(h*self.zoom)))
    def paintEvent(self,event):
        m=self.main;p=QPainter(self);p.fillRect(self.rect(),QColor('#151b24'));w,h=m.size_px
        self.zoom=max(.15,min((self.width()-36)/w,(self.height()-36)/h,20));self.ox=(self.width()-w*self.zoom)/2;self.oy=(self.height()-h*self.zoom)/2
        for y in range(0,h,8):
            for x in range(0,w,8):p.fillRect(self.rect_screen((x,y,min(8,w-x),min(8,h-y))),QColor('#2d3643' if (x//8+y//8)%2 else '#394452'))
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,False)
        p.drawImage(self.rect_screen((0,0,w,h)),qimage(m.current_image()))
        if m.onion_enabled.isChecked() and m.timeline_mode and m.frames.value()>1:
            previous=(m.frame_slider.value()-1)%m.frames.value()
            prev=m.timeline_frames()[previous]
            p.setOpacity(0.22)
            p.drawImage(self.rect_screen((0,0,w,h)),qimage(prev))
            p.setOpacity(1.0)
        p.setPen(QPen(QColor('#8fbba7'),1));p.drawRect(self.rect_screen((0,0,w,h)))
        l=m.selected_layer()
        if l and m.tool.currentText()=='Move / Transform':
            img=transformed(l);r=self.rect_screen((l.x,l.y,img.width,img.height));p.setPen(QPen(QColor('#b9e4c9'),2));p.drawRect(r)
            for pt in (r.topLeft(),r.topRight(),r.bottomLeft(),r.bottomRight()):p.fillRect(QRect(pt.x()-4,pt.y()-4,9,9),QColor('#d1f0db'))
            p.setPen(QPen(QColor('#edc7a2'),2));p.drawEllipse(r.center().x()-5,r.top()-22,10,10)
        if m.tool.currentText() in ('Animation Region','Mask Brush','Mask Eraser','Frame Pencil','Frame Eraser'):
            for i,reg in enumerate(m.regions):
                p.setPen(QPen(QColor('#d5bbef' if i==m.region_list.currentRow() else '#8b799c'),2));p.drawRect(self.rect_screen(reg.rect))
            if 0<=m.region_list.currentRow()<len(m.regions):
                reg=m.regions[m.region_list.currentRow()]
                p.setPen(QPen(QColor('#91e6bb'),1))
                for px,py in reg.mask:p.fillRect(self.rect_screen((px,py,1,1)),QColor(125,232,181,135))
            if self.drag and self.drag[0]=='region':
                a=self.drag[1];b=self.drag[2];p.setPen(QPen(QColor('#f3d3fc'),2));p.drawRect(self.rect_screen((min(a[0],b[0]),min(a[1],b[1]),abs(a[0]-b[0])+1,abs(a[1]-b[1])+1)))
    def mousePressEvent(self,e):
        if e.button()!=Qt.MouseButton.LeftButton:return
        m=self.main;x,y=self.coord(e.position());l=m.selected_layer();tool=m.tool.currentText()
        if tool in ('Frame Pencil','Frame Eraser'):
            m.checkpoint();self.drag=['framepaint'];self.frame_paint_at(x,y);return
        if tool=='Animation Region':m.checkpoint();self.drag=['region',(x,y),(x,y)];return
        if tool in ('Mask Brush','Mask Eraser','Frame Pencil','Frame Eraser'):
            m.checkpoint();self.drag=['mask'];self.mask_at(x,y);return
        if l is None:return
        if tool in ('Pencil','Eraser'):
            m.checkpoint();self.drag=['paint'];self.paint_at(x,y);return
        img=transformed(l);r=self.rect_screen((l.x,l.y,img.width,img.height));mx=e.position().x();my=e.position().y()
        if abs(mx-r.center().x())<14 and abs(my-(r.top()-17))<14:mode='rotate'
        elif abs(mx-r.right())<14 and abs(my-r.bottom())<14:mode='scale'
        else:mode='move'
        m.checkpoint();self.drag=[mode,x,y,l.x,l.y,l.scale,l.angle]
    def frame_paint_at(self,x,y):
        m=self.main
        if not 0<=x<m.size_px[0] or not 0<=y<m.size_px[1]:return
        index=m.frame_slider.value()
        strokes=m.frame_edits.setdefault(str(index),[])
        radius=m.brush.value()
        color=(0,0,0,0) if m.tool.currentText()=='Frame Eraser' else m.paint_color
        # Last edit wins, and strokes remain editable in the saved project.
        positions={(int(st[0]),int(st[1])):st for st in strokes}
        for yy in range(y-radius+1,y+radius):
            for xx in range(x-radius+1,x+radius):
                if 0<=xx<m.size_px[0] and 0<=yy<m.size_px[1]:
                    positions[(xx,yy)]=[xx,yy,*color]
        m.frame_edits[str(index)]=list(positions.values())
        m.timeline_mode=True;m.stop_preview();m.canvas.update()

    def mask_at(self,x,y):
        m=self.main;idx=m.region_list.currentRow()
        if not 0<=idx<len(m.regions):
            m.statusBar().showMessage('Select or create an animation region first',3000);return
        reg=m.regions[idx];pixels={tuple(p) for p in reg.mask}
        radius=max(1,m.mask_brush.value())
        for yy in range(y-radius+1,y+radius):
            for xx in range(x-radius+1,x+radius):
                if 0<=xx<m.size_px[0] and 0<=yy<m.size_px[1]:
                    if m.tool.currentText()=='Mask Eraser':pixels.discard((xx,yy))
                    else:pixels.add((xx,yy))
        reg.mask=[list(pt) for pt in sorted(pixels)]
        m.invalidate()
    def paint_at(self,x,y):
        m=self.main;l=m.selected_layer()
        if l is None:return
        if l.angle%360 or l.scale!=1:
            m.statusBar().showMessage('Pixel painting requires layer scale 100% and rotation 0°',3000);return
        paint_pixel(l,x-l.x,y-l.y,m.paint_color,m.brush.value(),m.tool.currentText()=='Eraser');m.invalidate()
    def mouseMoveEvent(self,e):
        if not self.drag:return
        m=self.main;x,y=self.coord(e.position());mode=self.drag[0]
        if mode=='region':self.drag[2]=(x,y);self.update();return
        if mode=='paint':self.paint_at(x,y);return
        if mode=='framepaint':self.frame_paint_at(x,y);return
        if mode=='mask':self.mask_at(x,y);return
        l=m.selected_layer()
        if l is None:return
        _,sx,sy,ox,oy,scale,angle=self.drag
        if mode=='move':l.x=ox+x-sx;l.y=oy+y-sy
        elif mode=='scale':l.scale=max(.1,min(16,scale*(1+(x-sx+y-sy)/max(1,l.image.width+l.image.height))))
        elif mode=='rotate':l.angle=(angle+(x-sx)*5)%360
        m.update_layer_controls();m.invalidate()
    def mouseReleaseEvent(self,e):
        if self.drag and self.drag[0]=='region':
            a,b=self.drag[1:];x,y=min(a[0],b[0]),min(a[1],b[1]);w,h=abs(a[0]-b[0])+1,abs(a[1]-b[1])+1
            self.main.add_region((x,y,w,h))
        self.drag=None;self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Slime House Studios — Pixel Art & Animation');self.setWindowIcon(QIcon(str(resource_path('assets/slime_mascot.png'))));self.resize(1450,860)
        self.worksheet=NFTWorksheet();self.worksheet_row=None;self.size_px=(64,64);self.layers=[];self.regions=[];self.traits={};self.preview=[];self.index=0;self.frame_edits={};self.timeline_mode=False;self.paint_color=(169,229,188,255)
        self.history=UndoHistory();self._restoring=False;self._dirty=False;self.project_path=None
        self.recovery_path=Path.home()/'.slime_house_studios'/'recovery.json'
        self.autosave_timer=QTimer(self);self.autosave_timer.setInterval(60000);self.autosave_timer.timeout.connect(self.write_recovery);self.autosave_timer.start()
        self.timer=QTimer(self);self.timer.timeout.connect(self.next_frame)
        root=QWidget();self.setCentralWidget(root);layout=QHBoxLayout(root)
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)
        left=QWidget();lv=QVBoxLayout(left);left.setMaximumWidth(285);layout.addWidget(left)
        lv.addWidget(QLabel('💚  SLIME HOUSE STUDIOS'))
        lv.addWidget(QLabel('Pixel Art • Animation • NFT Creation'))
        self.sizes=QComboBox();self.sizes.addItems(['32 × 32','64 × 64','128 × 128','256 × 256','512 × 512','Custom…']);self.sizes.setCurrentIndex(1);self.sizes.currentIndexChanged.connect(self.change_size);lv.addWidget(self.sizes)
        b=QPushButton('Import PNG layer');b.clicked.connect(self.import_png);lv.addWidget(b)
        b=QPushButton('New blank paint layer');b.clicked.connect(self.new_layer);lv.addWidget(b)
        self.layer_list=QListWidget();self.layer_list.currentRowChanged.connect(self.update_layer_controls);lv.addWidget(self.layer_list)
        bar=QHBoxLayout();lv.addLayout(bar)
        for text,fn in [('↑',lambda:self.move_layer(1)),('↓',lambda:self.move_layer(-1)),('Delete',self.remove_layer)]:
            b=QPushButton(text);b.clicked.connect(fn);bar.addWidget(b)
        self.tool=QComboBox();self.tool.addItems(['Move / Transform','Pencil','Eraser','Animation Region','Mask Brush','Mask Eraser','Frame Pencil','Frame Eraser']);lv.addWidget(self.tool)
        self.animator_button=QPushButton('✨ Open Junior Animator');self.animator_button.setToolTip('Quick effects for funny moving sprites and NFTs');lv.addWidget(self.animator_button)
        self.advanced_animator_button=QPushButton('🎞 Open Advanced Animator');self.advanced_animator_button.setToolTip('Frame-by-frame timeline for longer animations and GIFs');lv.addWidget(self.advanced_animator_button)
        color=QPushButton('Choose brush color');color.clicked.connect(self.choose_color);lv.addWidget(color)
        self.brush=QSpinBox();self.brush.setRange(1,32);self.brush.setValue(1)
        self.x=QSpinBox();self.y=QSpinBox();self.scale=QDoubleSpinBox();self.angle=QDoubleSpinBox()
        for s in (self.x,self.y):s.setRange(-4096,4096)
        self.scale.setRange(.1,16);self.scale.setSingleStep(.1);self.scale.setValue(1)
        self.angle.setRange(0,359);self.angle.setSingleStep(15)
        form=QFormLayout();lv.addLayout(form)
        for name,spin in [('Brush (px)',self.brush),('Layer X',self.x),('Layer Y',self.y),('Scale',self.scale),('Rotation °',self.angle)]:form.addRow(name,spin)
        for spin in (self.x,self.y,self.scale,self.angle):spin.valueChanged.connect(self.apply_layer_controls)
        self.canvas=Canvas(self);layout.addWidget(self.canvas,1)
        self.tabs=QTabWidget();self.tabs.setMinimumWidth(315);self.tabs.setMaximumWidth(395);layout.addWidget(self.tabs)
        self.animator_dock=QDockWidget('Junior Animator — Quick Effects',self)
        self.animator_dock.setObjectName('JuniorAnimatorDock')
        self.animator_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        self.animator_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        anim_scroll=QScrollArea();anim_scroll.setWidgetResizable(True);anim=QWidget();av=QVBoxLayout(anim);anim_scroll.setWidget(anim)
        self.animator_dock.setWidget(anim_scroll)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.animator_dock)
        self.animator_button.clicked.connect(self.toggle_animator)
        self.animator_dock.visibilityChanged.connect(self.animator_visibility_changed)
        self.tool.currentTextChanged.connect(self.open_animator_for_tool)
        self.advanced_animator_dock=QDockWidget('Advanced Animator — Timeline Studio',self)
        self.advanced_animator_dock.setObjectName('AdvancedAnimatorDock')
        self.advanced_animator_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        self.advanced_animator_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        advanced_scroll=QScrollArea();advanced_scroll.setWidgetResizable(True);advanced_panel=QWidget();self.advanced_layout=QVBoxLayout(advanced_panel);advanced_scroll.setWidget(advanced_panel)
        self.advanced_animator_dock.setWidget(advanced_scroll)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.advanced_animator_dock)
        self.advanced_animator_button.clicked.connect(self.toggle_advanced_animator)
        self.advanced_animator_dock.visibilityChanged.connect(self.advanced_animator_visibility_changed)
        av.addWidget(QLabel('Quick start: Highlight pixels → Pick a fun effect → Preview → Export.'))
        self.advanced_layout.addWidget(QLabel('Frame-by-frame editing for longer GIFs and animated sprites.'))
        self.advanced_layout.addWidget(QLabel('Both animators share the same artwork, regions, and animation frames.'))
        self.mask_brush=QSpinBox();self.mask_brush.setRange(1,32);self.mask_brush.setValue(1);av.addWidget(QLabel('Mask brush size'));av.addWidget(self.mask_brush)
        self.region_list=QListWidget();self.region_list.currentRowChanged.connect(self.update_region_controls);av.addWidget(self.region_list)
        self.effect=QComboBox();self.effect.addItems(EFFECTS);self.effect.currentIndexChanged.connect(self.apply_region_controls)
        self.strength=QSpinBox();self.strength.setRange(1,40);self.strength.setValue(2);self.strength.valueChanged.connect(self.apply_region_controls)
        self.laser_direction=QComboBox();self.laser_direction.addItems(['Right','Left','Up','Down','Radial']);self.laser_direction.currentIndexChanged.connect(self.apply_region_controls)
        self.laser_length=QSpinBox();self.laser_length.setRange(1,2048);self.laser_length.setValue(18);self.laser_length.valueChanged.connect(self.apply_region_controls)
        self.particles=QSpinBox();self.particles.setRange(1,250);self.particles.setValue(12);self.particles.valueChanged.connect(self.apply_region_controls)
        self.gush_speed=QSpinBox();self.gush_speed.setRange(1,20);self.gush_speed.setValue(2);self.gush_speed.valueChanged.connect(self.apply_region_controls)
        self.start_frame=QSpinBox();self.start_frame.setRange(0,119);self.start_frame.valueChanged.connect(self.apply_region_controls)
        self.active_frames=QSpinBox();self.active_frames.setRange(0,120);self.active_frames.setSpecialValueText('Whole timeline');self.active_frames.valueChanged.connect(self.apply_region_controls)
        self.cycle_frames=QSpinBox();self.cycle_frames.setRange(0,120);self.cycle_frames.setSpecialValueText('Timeline length');self.cycle_frames.valueChanged.connect(self.apply_region_controls)
        self.phase_offset=QSpinBox();self.phase_offset.setRange(0,119);self.phase_offset.valueChanged.connect(self.apply_region_controls)
        self.repeat_effect=QCheckBox('Repeat effect within its active window');self.repeat_effect.setChecked(True);self.repeat_effect.toggled.connect(self.apply_region_controls)
        av.addWidget(QLabel('Effect color (saved separately for each region)'))
        palette_row=QHBoxLayout()
        self.effect_color_presets=[('Slime Green','#77F5A0'),('Laser Red','#FF5555'),('Electric Blue','#52C7FF'),('Magic Purple','#BB83FF'),('Gold','#FFD65A'),('Hot Pink','#FF76C8')]
        self.effect_palette_buttons=[]
        for name,hex_color in self.effect_color_presets:
            btn=QPushButton('')
            btn.setFixedSize(28,28)
            btn.setToolTip(name)
            btn.setAccessibleName(name+' effect color')
            btn.setStyleSheet('QPushButton { background-color: '+hex_color+'; border: 2px solid #647284; border-radius: 5px; } QPushButton:hover { border: 2px solid white; }')
            btn.clicked.connect(lambda checked=False, value=hex_color: self.set_effect_preset_color(value))
            palette_row.addWidget(btn)
            self.effect_palette_buttons.append(btn)
        palette_row.addStretch()
        av.addLayout(palette_row)
        self.effect_color=QPushButton('Custom color…');self.effect_color.clicked.connect(self.choose_effect_color);self.effect_color.setToolTip('Pick any effect color, including transparency, for the selected region.');av.addWidget(self.effect_color)
        self.effect_color_preview=QLabel('Select a region to choose its color')
        av.addWidget(self.effect_color_preview)
        self.frames=QSpinBox();self.frames.setRange(2,120);self.frames.setValue(12)
        self.duration=QSpinBox();self.duration.setRange(20,2000);self.duration.setValue(100)
        f=QFormLayout();av.addLayout(f)
        for name,ctrl in [('Effect',self.effect),('Strength / travel',self.strength)]:f.addRow(name,ctrl)
        self.advanced_effects=QGroupBox('Advanced Effect Controls (optional)')
        self.advanced_effects.setCheckable(True);self.advanced_effects.setChecked(False)
        advanced_form=QFormLayout(self.advanced_effects)
        for name,ctrl in [('Laser / gush direction',self.laser_direction),('Beam / gush distance',self.laser_length),('Gush particles',self.particles),('Gush speed',self.gush_speed),('Start frame',self.start_frame),('Active frames (0 = all)',self.active_frames),('Cycle frames (0 = timeline)',self.cycle_frames),('Phase offset',self.phase_offset)]:advanced_form.addRow(name,ctrl)
        advanced_form.addRow(self.repeat_effect)
        av.addWidget(self.advanced_effects)
        av.addWidget(QLabel('Regions render together, in list order. Overlapping effects combine.'))
        self.export_settings=QGroupBox('Duration & Export Settings')
        self.export_settings.setCheckable(True);self.export_settings.setChecked(False)
        settings=QFormLayout(self.export_settings)
        self.speed_preset=QComboBox();self.speed_preset.addItems(['Custom','Slow (5 FPS)','Normal (10 FPS)','Smooth (15 FPS)','Fast (24 FPS)','Very fast (30 FPS)'])
        self.speed_preset.currentIndexChanged.connect(self.apply_speed_preset)
        self.fps_label=QLabel('10.0 FPS')
        self.total_duration_label=QLabel('1.20 seconds')
        self.loop_count=QSpinBox();self.loop_count.setRange(0,1000);self.loop_count.setSpecialValueText('Forever');self.loop_count.setValue(0)
        self.export_format=QComboBox();self.export_format.addItems(['Animated PNG (.apng)','Animated GIF (.gif)','Sprite sheet (.png)','Still PNG (.png)'])
        for label,control in [('Speed preset',self.speed_preset),('Frame count',self.frames),('Milliseconds / frame',self.duration),('Effective speed',self.fps_label),('Total duration',self.total_duration_label),('Animation loops',self.loop_count),('Export format',self.export_format)]:settings.addRow(label,control)
        self.frames.valueChanged.connect(self.update_duration_summary)
        self.duration.valueChanged.connect(self.update_duration_summary)
        self.update_duration_summary()
        self.advanced_layout.addWidget(self.export_settings)

        for text,fn in [('Add full-canvas region',lambda:self.add_region((0,0,*self.size_px))),('Delete selected region',self.delete_region),('Clear selected pixel mask',self.clear_mask),('Preview animation',self.start_preview),('Stop preview',self.stop_preview),('Export animation / image',self.export_selected_format)]:
            b=QPushButton(text);b.clicked.connect(fn);av.addWidget(b)
        self.advanced_layout.addWidget(QLabel('Frame-by-frame timeline'))
        self.frame_slider=QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setRange(0,self.frames.value()-1)
        self.frame_slider.valueChanged.connect(self.show_timeline_frame)
        self.advanced_layout.addWidget(self.frame_slider)
        self.frame_label=QLabel('Frame 1 / 12');self.advanced_layout.addWidget(self.frame_label)
        self.frames.valueChanged.connect(self.timeline_count_changed)
        self.onion_enabled=QCheckBox('Onion skin (previous frame)')
        self.onion_enabled.toggled.connect(self.canvas.update)
        self.advanced_layout.addWidget(self.onion_enabled)
        for text,fn in [('Edit selected frame',self.enable_timeline),('Duplicate previous frame edits',self.duplicate_frame),('Clear frame edits',self.clear_frame),('Previous frame',lambda:self.step_frame(-1)),('Next frame',lambda:self.step_frame(1))]:
            b=QPushButton(text);b.clicked.connect(fn);self.advanced_layout.addWidget(b)
        self.advanced_layout.addWidget(QLabel('Choose Frame Pencil or Frame Eraser to paint on the selected frame.'))
        self.advanced_layout.addStretch()
        av.addStretch()
        worksheet=QWidget();wv=QVBoxLayout(worksheet);self.tabs.addTab(worksheet,'NFT Worksheet')
        wv.addWidget(QLabel('Upload Excel or CSV, enter an NFT number, then edit its traits.'))
        upload=QPushButton('Open worksheet (.xlsx / .csv)');upload.clicked.connect(self.open_worksheet);wv.addWidget(upload)
        self.worksheet_info=QLabel('No worksheet loaded');self.worksheet_info.setWordWrap(True);wv.addWidget(self.worksheet_info)
        self.worksheet_id_col=QComboBox();self.worksheet_id_col.currentTextChanged.connect(self.change_worksheet_id_column)
        wv.addWidget(QLabel('Column containing NFT numbers'));wv.addWidget(self.worksheet_id_col)
        lookup_row=QHBoxLayout();wv.addLayout(lookup_row)
        self.nft_number=QLineEdit();self.nft_number.setPlaceholderText('e.g. 0059');self.nft_number.returnPressed.connect(self.lookup_worksheet_nft);lookup_row.addWidget(self.nft_number)
        find_btn=QPushButton('Load NFT');find_btn.clicked.connect(self.lookup_worksheet_nft);lookup_row.addWidget(find_btn)
        self.worksheet_table=QTableWidget(0,2);self.worksheet_table.setHorizontalHeaderLabels(['Worksheet column','Value (editable)']);self.worksheet_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch);wv.addWidget(self.worksheet_table)
        save_row=QHBoxLayout();wv.addLayout(save_row)
        save_edit=QPushButton('Save edits to session');save_edit.clicked.connect(self.save_worksheet_edits);save_row.addWidget(save_edit)
        export_btn=QPushButton('Export updated worksheet');export_btn.clicked.connect(self.export_worksheet);save_row.addWidget(export_btn)
        wv.addWidget(QLabel('Original worksheet is never overwritten automatically. Export saves a new file.'))
        wv.addStretch()
        nft=QWidget();nv=QVBoxLayout(nft);self.tabs.addTab(nft,'Trait Generator')
        nv.addWidget(QLabel('Weighted trait combinations (metadata CSV / JSON)'))
        self.trait_list=QListWidget();nv.addWidget(self.trait_list)
        for text,fn in [('Add trait',self.add_trait),('Remove selected trait',self.remove_trait),('Import trait JSON',self.import_traits),('Export trait JSON',self.export_traits)]:
            b=QPushButton(text);b.clicked.connect(fn);nv.addWidget(b)
        self.quantity=QSpinBox();self.quantity.setRange(1,10000);self.quantity.setValue(10);nv.addWidget(QLabel('NFT combinations'));nv.addWidget(self.quantity)
        b=QPushButton('Generate unique metadata CSV + JSON');b.clicked.connect(self.generate_nfts);nv.addWidget(b);nv.addStretch()
        proj=QWidget();pv=QVBoxLayout(proj);self.tabs.addTab(proj,'Project')
        for text,fn in [('Save editable project',self.save_project),('Open editable project',self.load_project)]:
            b=QPushButton(text);b.clicked.connect(fn);pv.addWidget(b)
        pv.addWidget(QLabel('Project files include layers, transforms, regions and traits.'));pv.addStretch()
        self.animator_dock.hide()
        self.advanced_animator_dock.hide()
        self.install_beginner_helpers()
        QTimer.singleShot(0,self.offer_recovery)
        self.statusBar().showMessage('Ready — import a PNG or create a layer. Choose Junior for quick effects or Advanced for timeline editing.')
        self.setStyleSheet('''QWidget{background:#1b222e;color:#d8e3e5;font-size:13px} QPushButton,QComboBox,QSpinBox,QDoubleSpinBox,QListWidget,QTabWidget::pane{background:#2b3544;border:1px solid #445064;border-radius:6px;padding:6px} QPushButton:hover{background:#3c5260} QListWidget::item:selected{background:#496d65} QTabBar::tab{background:#25303d;padding:10px} QTabBar::tab:selected{background:#426758}''')
    def install_beginner_helpers(self):
        """Keep the workspace simple while making every advanced tool discoverable."""
        hints={
            'Move / Transform':'Drag a layer to move it. Use corner handles to resize and the round handle to rotate.',
            'Pencil':'Draw on the selected layer. Create a blank paint layer if needed.',
            'Eraser':'Erase artwork pixels from the selected layer.',
            'Animation Region':'Drag a box around the part of your artwork you want to animate.',
            'Mask Brush':'Highlight exactly which pixels an effect should animate; this does not paint the artwork.',
            'Mask Eraser':'Remove highlighted animation pixels without changing the artwork.',
            'Frame Pencil':'Draw changes only on the currently selected animation frame.',
            'Frame Eraser':'Erase pixels only on the currently selected animation frame.'}
        for i in range(self.tool.count()):self.tool.setItemData(i,hints.get(self.tool.itemText(i),''),Qt.ItemDataRole.ToolTipRole)
        self.tool.currentTextChanged.connect(lambda tool:self.statusBar().showMessage(hints.get(tool,''),7000))
        tips=[(self.animator_button,'Quick effects: highlight pixels, choose a preset, preview, and export.'),
              (self.advanced_animator_button,'Open the separate frame-by-frame timeline. Closing it keeps your work.'),
              (self.effect,'Choose an effect; use Preview animation to see it in motion.'),
              (self.region_list,'Choose the region whose effect and highlighted pixels you want to edit.'),
              (self.mask_brush,'Brush size for highlighting animation pixels, not drawing on the sprite.'),
              (self.export_format,'Choose APNG for transparent animation, GIF for compatibility, or PNG for still images.'),
              (self.speed_preset,'Start with Normal. Open Custom only when you need exact timing.'),
              (self.worksheet_table,'Double-click a value to edit it, then save edits before exporting.'),
              (self.frame_slider,'Pick a frame to draw on. Frame Pencil and Frame Eraser edit only that frame.'),
              (self.advanced_effects,'Optional settings for lasers, gush, and independent effect timing.'),
              (self.export_settings,'Optional animation duration, looping, and output format controls.')]
        for widget,tip in tips:widget.setToolTip(tip)
        self.tool.setToolTip('Choose how the mouse interacts with the canvas.')
        self.layer_list.setToolTip('Select the artwork layer you want to edit.')
        self.setStatusTip('Tip: Import a PNG or create a blank layer to begin.')
        for keys,fn in [('Ctrl+Z',self.undo),('Ctrl+Shift+Z',self.redo),('Ctrl+Y',self.redo),('Ctrl+O',self.load_project),('Ctrl+S',self.save_project),('Ctrl+I',self.import_png),('Ctrl+E',self.export_selected_format)]:
            shortcut=QShortcut(QKeySequence(keys),self);shortcut.activated.connect(fn)
        self.statusBar().showMessage('Ready! Import a PNG or create a blank layer. Hover over a tool for help.',9000)

    def toggle_animator(self):
        self.animator_dock.setVisible(not self.animator_dock.isVisible())
        if self.animator_dock.isVisible():self.animator_dock.raise_()
    def animator_visibility_changed(self,visible):
        self.animator_button.setText('✨ Hide Junior Animator' if visible else '✨ Open Junior Animator')
    def toggle_advanced_animator(self):
        self.advanced_animator_dock.setVisible(not self.advanced_animator_dock.isVisible())
        if self.advanced_animator_dock.isVisible():self.advanced_animator_dock.raise_()
    def advanced_animator_visibility_changed(self,visible):
        self.advanced_animator_button.setText('🎞 Hide Advanced Animator' if visible else '🎞 Open Advanced Animator')
    def open_animator_for_tool(self,tool):
        if tool in ('Animation Region','Mask Brush','Mask Eraser'):
            self.animator_dock.show();self.animator_dock.raise_()
        elif tool in ('Frame Pencil','Frame Eraser'):
            self.advanced_animator_dock.show();self.advanced_animator_dock.raise_()
    def invalidate(self):self.stop_preview();self.canvas.update()
    def stop_preview(self):self.timer.stop();self.preview=[];self.canvas.update()
    def current_image(self):
        if self.preview:return self.preview[self.index]
        if self.timeline_mode:return self.timeline_frames()[self.frame_slider.value()]
        return composite(self.layers,self.size_px)
    def timeline_frames(self):
        return compose_timeline_frames(self.layers,self.size_px,self.regions,self.frames.value(),self.frame_edits)
    def show_timeline_frame(self,*args):
        self.stop_preview();self.timeline_mode=True
        self.frame_label.setText(f'Frame {self.frame_slider.value()+1} / {self.frames.value()}')
        self.canvas.update()
    def timeline_count_changed(self,*args):
        self.frame_slider.setMaximum(self.frames.value()-1)
        self.frame_label.setText(f'Frame {self.frame_slider.value()+1} / {self.frames.value()}')
        self.canvas.update()
    def enable_timeline(self):
        self.stop_preview();self.timeline_mode=True;self.canvas.update()
    def step_frame(self,step):
        self.frame_slider.setValue((self.frame_slider.value()+step)%self.frames.value())
    def duplicate_frame(self):
        i=self.frame_slider.value()
        if i==0:return
        self.checkpoint();self.frame_edits[str(i)]=[list(p) for p in self.frame_edits.get(str(i-1),[])]
        self.enable_timeline()
    def clear_frame(self):
        if str(self.frame_slider.value()) in self.frame_edits:
            if QMessageBox.question(self,'Clear frame edits?','Remove the hand-drawn changes on this frame?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.checkpoint();self.frame_edits.pop(str(self.frame_slider.value()),None)
        self.enable_timeline()
    def selected_layer(self):
        i=self.layer_list.currentRow();return self.layers[i] if 0<=i<len(self.layers) else None
    def update_layer_controls(self,*args):
        l=self.selected_layer()
        for spin,v in ((self.x,l.x if l else 0),(self.y,l.y if l else 0),(self.scale,l.scale if l else 1),(self.angle,l.angle if l else 0)):
            spin.blockSignals(True);spin.setValue(v);spin.blockSignals(False)
        self.canvas.update()
    def apply_layer_controls(self,*args):
        l=self.selected_layer()
        if l:self.checkpoint();l.x=self.x.value();l.y=self.y.value();l.scale=self.scale.value();l.angle=self.angle.value();self.invalidate()
    def change_size(self,*args):
        self.checkpoint()
        if self.sizes.currentText()=='Custom…':
            w,ok=QInputDialog.getInt(self,'Canvas width','Width',64,1,2048)
            if not ok:return
            h,ok=QInputDialog.getInt(self,'Canvas height','Height',64,1,2048)
            if not ok:return
            self.size_px=(w,h)
        else:
            n=int(self.sizes.currentText().split(' ')[0]);self.size_px=(n,n)
        self.invalidate()
    def import_png(self):
        path,_=QFileDialog.getOpenFileName(self,'Import PNG','','Images (*.png *.webp)')
        if path:
            try:
                with Image.open(path) as im:img=im.convert('RGBA').copy()
                self.add_layer(Layer(Path(path).name,img))
            except Exception as e:QMessageBox.critical(self,'Import error',str(e))
    def add_layer(self,l):self.checkpoint();self.layers.append(l);self.layer_list.addItem(l.name);self.layer_list.setCurrentRow(len(self.layers)-1);self.invalidate()
    def new_layer(self):self.add_layer(Layer('Paint layer',Image.new('RGBA',self.size_px)));self.tool.setCurrentText('Pencil')
    def choose_color(self):
        c=QColorDialog.getColor(QColor(*self.paint_color),self)
        if c.isValid():self.paint_color=(c.red(),c.green(),c.blue(),255)
    def move_layer(self,d):
        i=self.layer_list.currentRow();j=i+d
        if not 0<=i<len(self.layers) or not 0<=j<len(self.layers):return
        self.checkpoint();self.layers[i],self.layers[j]=self.layers[j],self.layers[i];item=self.layer_list.takeItem(i);self.layer_list.insertItem(j,item);self.layer_list.setCurrentRow(j);self.invalidate()
    def remove_layer(self):
        i=self.layer_list.currentRow()
        if i>=0:
            if QMessageBox.question(self,'Delete layer?','Remove the selected layer? You can undo this with Ctrl+Z.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            self.checkpoint();self.layers.pop(i);self.layer_list.takeItem(i);self.invalidate()
    def add_region(self,rect):
        self.checkpoint();r=Region(f'Region {len(self.regions)+1}',rect);self.regions.append(r);self.region_list.addItem(r.name);self.region_list.setCurrentRow(len(self.regions)-1);self.invalidate()
    def delete_region(self):
        i=self.region_list.currentRow()
        if i>=0:
            if QMessageBox.question(self,'Delete animation region?','Remove this animation region?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            self.checkpoint();self.regions.pop(i);self.region_list.takeItem(i);self.invalidate()
    def clear_mask(self):
        i=self.region_list.currentRow()
        if 0<=i<len(self.regions):
            if self.regions[i].mask and QMessageBox.question(self,'Clear highlights?','Remove all highlighted pixels from this region?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            self.checkpoint();self.regions[i].mask=[];self.invalidate()
    def set_effect_preset_color(self,hex_color):
        i=self.region_list.currentRow()
        if not 0<=i<len(self.regions):
            self.statusBar().showMessage('Add or select an animation region first.',4000)
            return
        c=QColor(hex_color)
        new_color=(c.red(),c.green(),c.blue(),255)
        if self.regions[i].color!=new_color:
            self.checkpoint();self.regions[i].color=new_color;self.invalidate()
        self.update_effect_color_preview()

    def update_effect_color_preview(self):
        i=self.region_list.currentRow()
        if not 0<=i<len(self.regions):
            self.effect_color_preview.setText('Select a region to choose its color')
            return
        rgba=self.regions[i].color
        self.effect_color_preview.setText('Selected region color: #'+''.join(f'{v:02X}' for v in rgba[:3])+f'  ·  {round(rgba[3]/255*100)}% opacity')

    def choose_effect_color(self):
        i=self.region_list.currentRow()
        if not 0<=i<len(self.regions):return
        c=QColorDialog.getColor(QColor(*self.regions[i].color),self,'Effect color',QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if c.isValid():
            self.checkpoint();self.regions[i].color=(c.red(),c.green(),c.blue(),c.alpha());self.invalidate();self.update_effect_color_preview()
    def update_region_controls(self,*args):
        i=self.region_list.currentRow()
        if 0<=i<len(self.regions):
            r=self.regions[i];self.effect.blockSignals(True);self.effect.setCurrentText(r.effect);self.effect.blockSignals(False);self.strength.blockSignals(True);self.strength.setValue(r.strength);self.strength.blockSignals(False);self.laser_direction.blockSignals(True);self.laser_direction.setCurrentText(r.direction);self.laser_direction.blockSignals(False);self.laser_length.blockSignals(True);self.laser_length.setValue(r.beam_length);self.laser_length.blockSignals(False);self.particles.blockSignals(True);self.particles.setValue(r.particle_count);self.particles.blockSignals(False);self.gush_speed.blockSignals(True);self.gush_speed.setValue(r.speed);self.gush_speed.blockSignals(False);
            for widget,value in [(self.start_frame,r.start_frame),(self.active_frames,r.active_frames),(self.cycle_frames,r.cycle_frames),(self.phase_offset,r.phase_offset)]:
                widget.blockSignals(True);widget.setValue(value);widget.blockSignals(False)
            self.repeat_effect.blockSignals(True);self.repeat_effect.setChecked(r.repeat);self.repeat_effect.blockSignals(False)
        self.update_effect_color_preview()
        self.canvas.update()
    def apply_region_controls(self,*args):
        i=self.region_list.currentRow()
        if 0<=i<len(self.regions):self.regions[i].effect=self.effect.currentText();self.regions[i].strength=self.strength.value();self.regions[i].direction=self.laser_direction.currentText();self.regions[i].beam_length=self.laser_length.value();self.regions[i].particle_count=self.particles.value();self.regions[i].speed=self.gush_speed.value();self.regions[i].start_frame=self.start_frame.value();self.regions[i].active_frames=self.active_frames.value();self.regions[i].cycle_frames=self.cycle_frames.value();self.regions[i].phase_offset=self.phase_offset.value();self.regions[i].repeat=self.repeat_effect.isChecked();self.invalidate()
    def make_frames(self):return self.timeline_frames()
    def start_preview(self):
        self.preview=self.make_frames();self.index=0;self.timer.start(self.duration.value());self.canvas.update()
    def next_frame(self):
        if self.preview:self.index=(self.index+1)%len(self.preview);self.canvas.update()
    def apply_speed_preset(self,index):
        values={1:200,2:100,3:67,4:42,5:33}
        if index in values:self.duration.setValue(values[index])
    def update_duration_summary(self,*args):
        ms=self.duration.value();count=self.frames.value()
        self.fps_label.setText(f'{1000/ms:.1f} FPS')
        self.total_duration_label.setText(f'{count*ms/1000:.2f} seconds ({count} frames)')
    def export_selected_format(self):
        selected=self.export_format.currentIndex()
        if selected==0:return self.save_apng()
        if selected==3:return self.save_png()
        frames=self.make_frames()
        if selected==1:
            path,_=QFileDialog.getSaveFileName(self,'Export animated GIF','animation.gif','GIF (*.gif)')
            if not path:return
            try:
                export_gif(frames,path,self.duration.value(),self.loop_count.value())
                QMessageBox.information(self,'GIF exported',f'Saved {path}\nNote: GIF has a limited color palette.')
            except Exception as e:QMessageBox.warning(self,'GIF export failed',str(e))
            return
        if selected==2:
            path,_=QFileDialog.getSaveFileName(self,'Export sprite sheet','sprite_sheet.png','PNG (*.png)')
            if not path:return
            try:
                export_sprite_sheet(frames,path)
                QMessageBox.information(self,'Sprite sheet exported',f'Saved {len(frames)} frames to {path}')
            except Exception as e:QMessageBox.warning(self,'Sprite sheet export failed',str(e))
    def save_apng(self):
        path,_=QFileDialog.getSaveFileName(self,'Export APNG','animation.apng','APNG (*.apng)')
        if path:
            try:export_apng(self.make_frames(),path,self.duration.value(),self.loop_count.value());QMessageBox.information(self,'Export verified',f'Saved {path}')
            except Exception as e:QMessageBox.warning(self,'Animation export',str(e))
    def save_png(self):
        path,_=QFileDialog.getSaveFileName(self,'Export PNG','sprite.png','PNG (*.png)')
        if path:composite(self.layers,self.size_px).save(path)
    def open_worksheet(self):
        path,_=QFileDialog.getOpenFileName(self,'Open NFT worksheet','','Worksheets (*.xlsx *.csv)')
        if not path:return
        try:
            count=self.worksheet.load(path)
            self.worksheet_row=None;self.worksheet_table.setRowCount(0)
            self.worksheet_id_col.blockSignals(True);self.worksheet_id_col.clear();self.worksheet_id_col.addItems(self.worksheet.headers);self.worksheet_id_col.setCurrentText(self.worksheet.number_column);self.worksheet_id_col.blockSignals(False)
            self.worksheet_info.setText(f'{Path(path).name} — {count} NFT rows loaded')
            self.statusBar().showMessage('Worksheet loaded. Enter an NFT number to find its traits.',5000)
        except Exception as e:QMessageBox.warning(self,'Worksheet import failed',str(e))
    def change_worksheet_id_column(self,name):
        if name in self.worksheet.headers:self.worksheet.number_column=name;self.worksheet_row=None;self.worksheet_table.setRowCount(0)
    def lookup_worksheet_nft(self):
        try:
            index,values=self.worksheet.lookup(self.nft_number.text())
            self.worksheet_row=index;self.worksheet_table.setRowCount(len(self.worksheet.headers))
            for i,key in enumerate(self.worksheet.headers):
                name=QTableWidgetItem(key);name.setFlags(name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.worksheet_table.setItem(i,0,name)
                self.worksheet_table.setItem(i,1,QTableWidgetItem(values[key]))
            self.statusBar().showMessage(f'Loaded NFT {self.nft_number.text().strip()} — edit values and click Save edits',5000)
        except Exception as e:QMessageBox.warning(self,'NFT lookup',str(e))
    def save_worksheet_edits(self):
        if self.worksheet_row is None:QMessageBox.information(self,'No NFT selected','Load an NFT number first.');return
        try:
            changes={self.worksheet.headers[i]:(self.worksheet_table.item(i,1).text() if self.worksheet_table.item(i,1) else '') for i in range(len(self.worksheet.headers))}
            self.worksheet.edit(self.worksheet_row,changes)
            self.statusBar().showMessage('Edits saved in memory. Export worksheet to save a file.',6000)
        except Exception as e:QMessageBox.warning(self,'Edit failed',str(e))
    def export_worksheet(self):
        if not self.worksheet.headers:QMessageBox.information(self,'No worksheet','Open a worksheet first.');return
        if self.worksheet_row is not None:self.save_worksheet_edits()
        path,_=QFileDialog.getSaveFileName(self,'Export corrected worksheet','updated_nft_traits.xlsx','Excel (*.xlsx);;CSV (*.csv)')
        if not path:return
        try:self.worksheet.export(path);QMessageBox.information(self,'Worksheet exported',f'Saved updated worksheet to:\n{path}')
        except Exception as e:QMessageBox.warning(self,'Export failed',str(e))
    def refresh_traits(self):
        self.trait_list.clear()
        for cat,opts in self.traits.items():
            for opt in opts:self.trait_list.addItem(f'{cat} | {opt["name"]} | weight {opt["weight"]}')
    def add_trait(self):
        cat,ok=QInputDialog.getText(self,'Trait category','Category (e.g. Fur)')
        if not ok or not cat.strip():return
        name,ok=QInputDialog.getText(self,'Trait value','Value (e.g. Ginger)')
        if not ok or not name.strip():return
        weight,ok=QInputDialog.getDouble(self,'Trait weight','Relative weight',10,0.01,100000,2)
        if ok:self.traits.setdefault(cat.strip(),[]).append(dict(name=name.strip(),weight=weight));self.refresh_traits()
    def remove_trait(self):
        i=self.trait_list.currentRow();entries=[(cat,j) for cat,opts in self.traits.items() for j,_ in enumerate(opts)]
        if 0<=i<len(entries):
            cat,j=entries[i];self.traits[cat].pop(j)
            if not self.traits[cat]:del self.traits[cat]
            self.refresh_traits()
    def import_traits(self):
        path,_=QFileDialog.getOpenFileName(self,'Import traits','','JSON (*.json)')
        if path:
            try:self.traits=json.loads(Path(path).read_text());self.refresh_traits()
            except Exception as e:QMessageBox.warning(self,'Import failed',str(e))
    def export_traits(self):
        path,_=QFileDialog.getSaveFileName(self,'Save traits','traits.json','JSON (*.json)')
        if path:Path(path).write_text(json.dumps(self.traits,indent=2),encoding='utf-8')
    def generate_nfts(self):
        if not self.traits:QMessageBox.warning(self,'No traits','Add trait categories and values first.');return
        path,_=QFileDialog.getSaveFileName(self,'Save NFT metadata','collection.json','JSON (*.json)')
        if not path:return
        try:
            combos=generate_traits(self.traits,self.quantity.value());entries=[{'name':f'Slime House #{i+1}','attributes':[{'trait_type':k,'value':v} for k,v in combo.items()]} for i,combo in enumerate(combos)]
            Path(path).write_text(json.dumps(entries,indent=2),encoding='utf-8')
            csvpath=Path(path).with_suffix('.csv')
            with csvpath.open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=['name',*self.traits.keys()]);writer.writeheader()
                for entry,combo in zip(entries,combos):writer.writerow({'name':entry['name'],**combo})
            QMessageBox.information(self,'Metadata created',f'Created {len(entries)} unique trait combinations.\n{path}\n{csvpath}\n\nNote: metadata only; artwork batch compositing is not implemented yet.')
        except Exception as e:QMessageBox.warning(self,'Generation failed',str(e))
    def snapshot(self):
        return capture(self.size_px,self.layers,self.regions,self.traits,self.frame_edits,
                       self.frames.value(),self.duration.value(),self.loop_count.value(),self.export_format.currentIndex())

    def checkpoint(self):
        if not self._restoring:
            self.history.record(self.snapshot())
            self._dirty=True

    def restore_snapshot(self,obj):
        size,layers,regions=decode(obj)
        self._restoring=True
        try:
            self.size_px=size;self.layers=layers;self.regions=regions
            self.traits=obj.get('traits',{});self.frame_edits=obj.get('frame_edits',{})
            self.frames.setValue(obj.get('frame_count',8));self.duration.setValue(obj.get('frame_duration',100))
            self.loop_count.setValue(obj.get('animation_loops',0));self.export_format.setCurrentIndex(obj.get('export_format',0))
            self.timeline_mode=bool(self.frame_edits)
            self.layer_list.clear();self.layer_list.addItems([l.name for l in layers])
            self.region_list.clear();self.region_list.addItems([r.name for r in regions])
            if layers:self.layer_list.setCurrentRow(len(layers)-1)
            if regions:self.region_list.setCurrentRow(0)
            self.refresh_traits();self.invalidate()
        finally:
            self._restoring=False

    def undo(self):
        state=self.history.undo(self.snapshot())
        if state is not None:
            self.restore_snapshot(state);self._dirty=True
            self.statusBar().showMessage('Undone — Ctrl+Shift+Z to redo',3000)

    def redo(self):
        state=self.history.redo(self.snapshot())
        if state is not None:
            self.restore_snapshot(state);self._dirty=True
            self.statusBar().showMessage('Redone',3000)

    def write_recovery(self):
        if not self._dirty:return
        try:
            atomic_write(self.recovery_path,self.snapshot())
            self.statusBar().showMessage('Recovery backup saved automatically',2500)
        except Exception as exc:
            self.statusBar().showMessage(f'Automatic recovery backup failed: {exc}',7000)

    def offer_recovery(self):
        if not self.recovery_path.exists():return
        choice=QMessageBox.question(self,'Recover unsaved artwork?',
            'An automatic recovery backup was found. Restore it?\n\nChoose No to discard the backup.',
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.Yes)
        if choice==QMessageBox.StandardButton.Yes:
            try:
                self.restore_snapshot(json.loads(self.recovery_path.read_text(encoding='utf-8')))
                self._dirty=True
            except Exception as exc:QMessageBox.warning(self,'Recovery failed',str(exc))
        else:
            self.recovery_path.unlink(missing_ok=True)

    def save_project(self):
        path,_=QFileDialog.getSaveFileName(self,'Save project',self.project_path or 'project.json','JSON (*.json)')
        if not path:return
        try:
            atomic_write(path,self.snapshot());self.project_path=path;self._dirty=False
            self.recovery_path.unlink(missing_ok=True)
            self.statusBar().showMessage('Project saved safely',4000)
        except Exception as exc:QMessageBox.warning(self,'Save failed',str(exc))

    def load_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Open project','','JSON (*.json)')
        if not path:return
        try:
            obj=json.loads(Path(path).read_text(encoding='utf-8'))
            self.checkpoint();self.restore_snapshot(obj)
            self.project_path=path;self._dirty=False
            self.recovery_path.unlink(missing_ok=True)
        except Exception as exc:QMessageBox.warning(self,'Load failed',str(exc))

    def closeEvent(self,event):
        if self._dirty:
            self.write_recovery()
            choice=QMessageBox.question(self,'Unsaved changes',
                'Your work has unsaved changes. Close with a recovery backup?\n\nChoose No to stay and save your project.',
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            if choice!=QMessageBox.StandardButton.Yes:
                event.ignore();return
        event.accept()

def main():
    app=QApplication(sys.argv);app.setApplicationName('Slime House Studios');app.setWindowIcon(QIcon(str(resource_path('assets/slime_mascot.png'))));win=MainWindow();win.show();sys.exit(app.exec())

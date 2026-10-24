"""Slime House Studios native Qt editor."""
import base64, io, json, sys, csv
from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt, QRect, QTimer, QSettings
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QIcon, QKeySequence, QShortcut, QFont, QCursor, QPixmap, QAction
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QPushButton,QLabel,QListWidget,QListWidgetItem,QFileDialog,QMessageBox,QComboBox,QSpinBox,QDoubleSpinBox,QFormLayout,QInputDialog,QTabWidget,QColorDialog,QLineEdit,QCheckBox,QScrollArea,QSlider,QTableWidget,QTableWidgetItem,QHeaderView,QDockWidget,QSizePolicy,QGroupBox,QDialog,QDialogButtonBox)
from .pet_sprite_wizard import ANIMATIONS, LIFE_ANIMATIONS, BATTLE_ANIMATIONS, POSE_TEMPLATES, generate as generate_pet_animations, export_package as export_pet_package, animation_guide, format_animation_guide, export_animation_guides, generate_rigged, validate_regions, RIG_PARTS
from .history import UndoHistory, capture, decode, atomic_write
from .worksheet import NFTWorksheet
from .core import Layer,Region,EFFECTS,composite,transformed,paint_pixel,frames_for,compose_timeline_frames,apply_motion_keyframes,paste_clip,compose_layer_motion_frames,interpolate_pose_anchors,export_apng,export_gif,export_sprite_sheet,generate_traits

def resource_path(p):return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))/p

def qimage(im):
    im=im.convert('RGBA');return QImage(im.tobytes(),im.width,im.height,QImage.Format.Format_RGBA8888).copy()

# Tiny high-contrast tool cursors, drawn locally so the EXE needs no extra assets.
# The small crosshair is the exact canvas interaction point (hotspot 3,3).
CURSOR_SYMBOLS={
    'Pencil':'✎','Eraser':'⌫','Mask Brush':'✦','Mask Eraser':'◇',
    'Frame Pencil':'✎','Frame Eraser':'⌫','Eyedropper':'◉','Animation Region':'▭','Pose Anchor':'⌖',
}
CURSOR_COLORS={
    'Pencil':'#ffe3a1','Eraser':'#ffb6b6','Mask Brush':'#91e6bb',
    'Mask Eraser':'#a7d3ff','Frame Pencil':'#f5cf9c',
    'Frame Eraser':'#ffb9bd','Eyedropper':'#c4b5fd','Animation Region':'#d5bbef','Pose Anchor':'#ffdc8b',
}

def cursor_for_tool(tool):
    if tool=='Move / Transform':
        return QCursor(Qt.CursorShape.OpenHandCursor)
    if tool not in CURSOR_SYMBOLS:
        return QCursor(Qt.CursorShape.CrossCursor)
    pix=QPixmap(36,36)
    pix.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing,False)
    color=QColor(CURSOR_COLORS[tool])
    # White/black crosshair remains readable on light or dark sprites.
    painter.setPen(QPen(QColor('#10151b'),3))
    painter.drawLine(3,0,3,7);painter.drawLine(0,3,7,3)
    painter.setPen(QPen(color,1))
    painter.drawLine(3,0,3,7);painter.drawLine(0,3,7,3)
    painter.setBrush(QColor('#19232c'))
    painter.setPen(QPen(color,2))
    painter.drawRoundedRect(10,9,24,24,5,5)
    painter.setFont(QFont('Segoe UI Symbol',15,QFont.Weight.Bold))
    painter.setPen(QPen(color,1))
    painter.drawText(QRect(11,10,22,22),Qt.AlignmentFlag.AlignCenter,CURSOR_SYMBOLS[tool])
    painter.end()
    return QCursor(pix,3,3)

class Canvas(QWidget):
    def __init__(self,main):
        super().__init__();self.main=main;self.setMinimumSize(450,450);self.drag=None;self.setMouseTracking(True);self.zoom_factor=1.0;self.zoom_focus=None
    def coord(self,pos):return round((pos.x()-self.ox)/self.zoom),round((pos.y()-self.oy)/self.zoom)
    def rect_screen(self,rect):
        x,y,w,h=rect;return QRect(round(self.ox+x*self.zoom),round(self.oy+y*self.zoom),max(1,round(w*self.zoom)),max(1,round(h*self.zoom)))
    def paintEvent(self,event):
        m=self.main;p=QPainter(self);p.fillRect(self.rect(),QColor('#151b24'));w,h=m.size_px
        fit=max(.15,min((self.width()-36)/w,(self.height()-36)/h,20))
        self.zoom=fit*self.zoom_factor
        self.ox=(self.width()-w*self.zoom)/2;self.oy=(self.height()-h*self.zoom)/2
        if self.zoom_focus is not None:
            # Pan offset is expressed in screen pixels and preserved between paints.
            self.ox+=self.zoom_focus[0];self.oy+=self.zoom_focus[1]
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
        if m.tool.currentText()=='Pose Anchor' or (hasattr(m,'show_pet_anchors') and m.show_pet_anchors.isChecked()):
            p.setRenderHint(QPainter.RenderHint.Antialiasing,False)
            for name,xy in m.pet_anchors.get(m.pet_pose.currentText(),{}).items():
                cx=int(self.ox+(xy[0]+.5)*self.zoom);cy=int(self.oy+(xy[1]+.5)*self.zoom)
                p.setPen(QPen(QColor('#15202b'),4));p.drawEllipse(cx-6,cy-6,12,12)
                p.setPen(QPen(QColor('#ffdc8b'),2));p.drawEllipse(cx-6,cy-6,12,12)
                p.drawLine(cx-9,cy,cx+9,cy);p.drawLine(cx,cy-9,cx,cy+9)
                p.setPen(QColor('#fff2c7'));p.drawText(cx+11,cy-9,name)

    def wheelEvent(self,e):
        # Wheel zooms about the mouse pointer, keeping the pixel under it stationary.
        steps=e.angleDelta().y()/120.0
        if not steps:
            e.ignore();return
        point=e.position()
        old_zoom=self.zoom
        old_x=(point.x()-self.ox)/old_zoom
        old_y=(point.y()-self.oy)/old_zoom
        self.zoom_factor=max(0.1,min(32.0,self.zoom_factor*(1.2**steps)))
        w,h=self.main.size_px
        fit=max(.15,min((self.width()-36)/w,(self.height()-36)/h,20))
        new_zoom=fit*self.zoom_factor
        centered_x=(self.width()-w*new_zoom)/2
        centered_y=(self.height()-h*new_zoom)/2
        self.zoom_focus=(point.x()-old_x*new_zoom-centered_x,point.y()-old_y*new_zoom-centered_y)
        self.update();e.accept()

    def reset_zoom(self):
        self.zoom_factor=1.0;self.zoom_focus=None;self.update()

    def mousePressEvent(self,e):
        if e.button()!=Qt.MouseButton.LeftButton:return
        m=self.main;x,y=self.coord(e.position());l=m.selected_layer();tool=m.tool.currentText()
        if tool=='Eyedropper':
            self.sample_color_at(x,y);return
        if tool=='Pose Anchor':
            m.checkpoint();self.drag=['anchor'];self.place_anchor(x,y);return
        if tool in ('Frame Pencil','Frame Eraser'):
            m.checkpoint();self.drag=['framepaint'];self.frame_paint_at(x,y);return
        if tool=='Animation Region':m.checkpoint();self.drag=['region',(x,y),(x,y)];return
        if tool in ('Mask Brush','Mask Eraser','Frame Pencil','Frame Eraser'):
            m.checkpoint();self.drag=['mask'];self.mask_at(x,y);return
        if tool in ('Pencil','Eraser'):
            if not (0 <= x < m.size_px[0] and 0 <= y < m.size_px[1]):return
            # A blank project should be drawable immediately; no hidden layer setup.
            if l is None:
                if tool=='Eraser':
                    m.statusBar().showMessage('Nothing to erase yet. Draw with Pencil first.',3500);return
                m.add_layer(Layer('Paint layer',Image.new('RGBA',m.size_px)))
                l=m.selected_layer()
            # The normal Pencil edits the base artwork, not a stale timeline preview.
            m.timeline_mode=False
            m.stop_preview()
            m.checkpoint();self.drag=['paint'];self.paint_at(x,y);return
        if tool!='Move / Transform':return
        img=transformed(l);r=self.rect_screen((l.x,l.y,img.width,img.height));mx=e.position().x();my=e.position().y()
        if abs(mx-r.center().x())<14 and abs(my-(r.top()-17))<14:mode='rotate'
        elif abs(mx-r.right())<14 and abs(my-r.bottom())<14:mode='scale'
        else:mode='move'
        m.checkpoint();self.drag=[mode,x,y,l.x,l.y,l.scale,l.angle]
    def sample_color_at(self,x,y):
        """Pick a visible, opaque pixel without altering artwork or undo history."""
        m=self.main
        if not (0 <= x < m.size_px[0] and 0 <= y < m.size_px[1]):return
        rgba=m.current_image().convert('RGBA').getpixel((x,y))
        if rgba[3]==0:
            m.statusBar().showMessage('Transparent pixel: brush color unchanged.',2500)
            return
        m.paint_color=tuple(rgba)
        m.statusBar().showMessage(f'Picked color #{rgba[0]:02X}{rgba[1]:02X}{rgba[2]:02X} (alpha {rgba[3]})',2500)
        # Restore the drawing tool after a one-click sample.
        previous=getattr(m,'eyedropper_previous_tool','Pencil')
        if previous=='Eyedropper':previous='Pencil'
        m.tool.setCurrentText(previous)
        self.update()

    def place_anchor(self,x,y):
        m=self.main
        if not (0<=x<m.size_px[0] and 0<=y<m.size_px[1]):return
        m.pet_anchor_x.setValue(x);m.pet_anchor_y.setValue(y)
        pose=m.pet_pose.currentText();name=m.pet_anchor_name.currentText().strip() or 'Accessory'
        m.pet_anchors.setdefault(pose,{})[name]=[x,y]
        m.refresh_pet_anchors();self.update()

    def frame_paint_at(self,x,y):
        m=self.main
        if not 0<=x<m.size_px[0] or not 0<=y<m.size_px[1]:return
        index=m.frame_slider.value()
        strokes=m.frame_tracks.setdefault(m.track_selector.currentText(),{}).setdefault(str(index),[])
        radius=m.brush.value()
        color=(0,0,0,0) if m.tool.currentText()=='Frame Eraser' else m.paint_color
        # Last edit wins, and strokes remain editable in the saved project.
        positions={(int(st[0]),int(st[1])):st for st in strokes}
        for yy in range(y-radius+1,y+radius):
            for xx in range(x-radius+1,x+radius):
                if 0<=xx<m.size_px[0] and 0<=yy<m.size_px[1]:
                    positions[(xx,yy)]=[xx,yy,*color]
        m.frame_tracks[m.track_selector.currentText()][str(index)]=list(positions.values())
        m.sync_frame_edits()
        m.timeline_mode=True;m.stop_preview();m.canvas.update()

    def mask_at(self,x,y):
        m=self.main;idx=m.region_list.currentRow()
        if not 0<=idx<len(m.regions):
            if m.tool.currentText()=='Mask Brush':
                m.add_region((0,0,*m.size_px))
                idx=m.region_list.currentRow()
            else:
                m.statusBar().showMessage('Highlight pixels first, then erase parts of that highlight.',3000);return
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
        if not (0 <= x < m.size_px[0] and 0 <= y < m.size_px[1]):return
        if l.angle%360 or l.scale!=1:
            m.statusBar().showMessage('Pixel painting requires layer scale 100% and rotation 0°',3000);return
        paint_pixel(l,x-l.x,y-l.y,m.paint_color,m.brush.value(),m.tool.currentText()=='Eraser');m.invalidate()
    def mouseMoveEvent(self,e):
        if not self.drag:return
        m=self.main;x,y=self.coord(e.position());mode=self.drag[0]
        if mode=='region':self.drag[2]=(x,y);self.update();return
        if mode=='anchor':self.place_anchor(x,y);return
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
        self.settings=QSettings('Slime House Studios','Studio');self.pet_anchors={};self.frame_tracks={'Ink':{}};self.motion_keys={};self.layer_motion_keys={};self.pose_transition=None;self.frame_clips={};self.worksheet=NFTWorksheet();self.worksheet_row=None;self.size_px=(64,64);self.layers=[];self.regions=[];self.traits={};self.preview=[];self.index=0;self.frame_edits={};self.timeline_mode=False;self.paint_color=(169,229,188,255)
        self.history=UndoHistory();self._restoring=False;self._dirty=False;self.project_path=None
        self.recovery_path=Path.home()/'.slime_house_studios'/'recovery.json'
        self.autosave_timer=QTimer(self);self.autosave_timer.setInterval(60000);self.autosave_timer.timeout.connect(self.write_recovery);self.autosave_timer.start()
        self.timer=QTimer(self);self.timer.timeout.connect(self.next_frame)
        root=QWidget();self.setCentralWidget(root);layout=QHBoxLayout(root)
        self.setDockOptions(QMainWindow.DockOption.AllowTabbedDocks | QMainWindow.DockOption.AnimatedDocks)
        self.setup_classic_menus()
        left=QWidget();lv=QVBoxLayout(left);left.setMaximumWidth(285);layout.addWidget(left)
        studio_title=QLabel('💚  SLIME HOUSE STUDIOS');studio_title.setObjectName('studioTitle');lv.addWidget(studio_title)
        studio_subtitle=QLabel('Draw little things. Make them move.');studio_subtitle.setObjectName('studioSubtitle');lv.addWidget(studio_subtitle)
        self.sizes=QComboBox();self.sizes.addItems(['32 × 32','64 × 64','128 × 128','256 × 256','512 × 512','Custom…']);self.sizes.setCurrentIndex(1);self.sizes.currentIndexChanged.connect(self.change_size);lv.addWidget(self.sizes)
        b=QPushButton('Import PNG layer');b.clicked.connect(self.import_png);lv.addWidget(b)
        b=QPushButton('New blank paint layer');b.clicked.connect(self.new_layer);lv.addWidget(b)
        self.layer_list=QListWidget();self.layer_list.currentRowChanged.connect(self.update_layer_controls);self.layer_list.currentRowChanged.connect(self.refresh_layer_motion);lv.addWidget(self.layer_list)
        bar=QHBoxLayout();lv.addLayout(bar)
        for text,fn in [('↑',lambda:self.move_layer(1)),('↓',lambda:self.move_layer(-1)),('Delete',self.remove_layer)]:
            b=QPushButton(text);b.clicked.connect(fn);bar.addWidget(b)
        lv.addWidget(QLabel('YOUR ACTIVE TOOL'))
        self.tool=QComboBox();self.tool.addItems(['Move / Transform','Pencil','Eraser','Eyedropper','Animation Region','Mask Brush','Mask Eraser','Frame Pencil','Frame Eraser','Pose Anchor']);lv.addWidget(self.tool)
        self.active_tool_banner=QLabel('↔  Move / Transform  ·  Drag artwork to move it')
        self.active_tool_banner.setObjectName('activeToolBanner')
        self.active_tool_banner.setWordWrap(True)
        lv.addWidget(self.active_tool_banner)
        self.animator_button=QPushButton('✨ Open Junior Animator');self.animator_button.setToolTip('Quick effects for funny moving sprites and NFTs');lv.addWidget(self.animator_button)
        self.advanced_animator_button=QPushButton('🎞 Open Intermediate Studio');self.advanced_animator_button.setToolTip('Frame-by-frame timeline for longer animations and GIFs');lv.addWidget(self.advanced_animator_button)
        self.pet_workshop_button=QPushButton('🐾 Open Desktop Pet Builder')
        lv.addWidget(self.pet_workshop_button)
        self.guided_toggle=QCheckBox('💡 Guided Mode — show beginner tips')
        self.guided_toggle.setChecked(self.settings.value('guided_mode',True,type=bool))
        self.guided_toggle.toggled.connect(self.update_guided_mode)
        lv.addWidget(self.guided_toggle)
        self.nft_manager_button=QPushButton('🐱 Open NFT Manager')
        self.nft_manager_button.setToolTip('Optional NFT worksheet and trait tools — hide this for a clean pixel-art workspace.')
        lv.addWidget(self.nft_manager_button)
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
        self._tool_sizes = {name: 1 for name in self.SIZABLE_TOOLS}
        self.brush.valueChanged.connect(self._remember_active_tool_size)
        self.tool.currentTextChanged.connect(self.activate_tool)
        self.advanced_animator_dock=QDockWidget('Intermediate Studio — Timeline Studio',self)
        self.advanced_animator_dock.setObjectName('AdvancedAnimatorDock')
        self.advanced_animator_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        self.advanced_animator_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        advanced_scroll=QScrollArea();advanced_scroll.setWidgetResizable(True);advanced_panel=QWidget();self.advanced_layout=QVBoxLayout(advanced_panel);advanced_scroll.setWidget(advanced_panel)
        self.advanced_animator_dock.setWidget(advanced_scroll)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.advanced_animator_dock)
        self.advanced_animator_button.clicked.connect(self.toggle_advanced_animator)
        self.advanced_animator_dock.visibilityChanged.connect(self.advanced_animator_visibility_changed)
        av.addWidget(QLabel('Quick start: 1. Highlight pixels  2. Pick an effect  3. Preview  4. Export'))
        junior_actions=QHBoxLayout()
        self.highlight_button=QPushButton('🖍 Highlight to animate')
        self.highlight_button.setToolTip('Draw directly over the pixels you want to move. A region is created automatically.')
        self.highlight_button.clicked.connect(self.begin_highlighting)
        junior_actions.addWidget(self.highlight_button)
        self.highlight_erase_button=QPushButton('Erase highlight')
        self.highlight_erase_button.clicked.connect(lambda:self.tool.setCurrentText('Mask Eraser'))
        junior_actions.addWidget(self.highlight_erase_button)
        av.addLayout(junior_actions)
        self.junior_preview_button=QPushButton('▶ Preview my animation')
        self.junior_preview_button.setToolTip('Play the selected animation on the main canvas.')
        self.junior_preview_button.clicked.connect(self.start_preview)
        av.addWidget(self.junior_preview_button)
        self.junior_stop_button=QPushButton('■ Stop preview')
        self.junior_stop_button.clicked.connect(self.stop_preview)
        av.addWidget(self.junior_stop_button)
        self.preview_hint=QLabel('Highlight a part of your sprite, then click Preview.')
        self.preview_hint.setWordWrap(True)
        av.addWidget(self.preview_hint)
        self.advanced_layout.addWidget(QLabel('Frame-by-frame editing for longer GIFs and animated sprites.'))
        self.advanced_layout.addWidget(QLabel('Both animators share the same artwork, regions, and animation frames.'))
        self.mask_brush=QSpinBox();self.mask_brush.setRange(1,32);self.mask_brush.setValue(1);av.addWidget(QLabel('Mask brush size'));av.addWidget(self.mask_brush)
        self.mask_brush.valueChanged.connect(self._remember_active_tool_size)
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
        self.export_format=QComboBox();self.export_format.addItems(['✨ Animated PNG / APNG (.png)','🎞 Animated GIF (.gif)','▦ Sprite sheet (.png) — frames side by side','🖼 Still image (.png) — NO ANIMATION'])
        for label,control in [('Speed preset',self.speed_preset),('Frame count',self.frames),('Milliseconds / frame',self.duration),('Effective speed',self.fps_label),('Total duration',self.total_duration_label),('Animation loops',self.loop_count),('Export format',self.export_format)]:settings.addRow(label,control)
        self.frames.valueChanged.connect(self.update_duration_summary)
        self.duration.valueChanged.connect(self.update_duration_summary)
        self.update_duration_summary()
        self.advanced_layout.addWidget(self.export_settings)
        self.export_tip=QLabel('✨ APNG keeps full-color transparency and MOVES. GIF is best for sharing. Still PNG does not animate.')
        self.export_tip.setWordWrap(True)
        av.addWidget(self.export_tip)
        self.export_format.currentIndexChanged.connect(self.update_export_tip)
        self.update_export_tip()
        self.quick_apng=QPushButton('✨ Export… Choose your formats')
        self.quick_apng.setToolTip('Export an animated PNG with all frames, regardless of the advanced export dropdown.')
        self.quick_apng.clicked.connect(self.export_choose_formats)
        av.addWidget(self.quick_apng)
        self.quick_gif=QPushButton('🎞 Quick Export GIF')
        self.quick_gif.clicked.connect(self.save_gif)
        av.addWidget(self.quick_gif)

        for text,fn in [('Add full-canvas region',lambda:self.add_region((0,0,*self.size_px))),('Delete selected region',self.delete_region),('Clear selected pixel mask',self.clear_mask),('Preview animation',self.start_preview),('Stop preview',self.stop_preview),('Export… Choose formats',self.export_choose_formats)]:
            b=QPushButton(text);b.clicked.connect(fn);av.addWidget(b)
        self.advanced_layout.addWidget(QLabel('Frame-by-frame timeline'))
        self.advanced_layout.addWidget(QLabel('EDITING TRACK — independent paint layers per frame'))
        self.track_selector=QComboBox();self.track_selector.addItems(['Ink'])
        self.track_selector.currentTextChanged.connect(self.switch_frame_track)
        self.advanced_layout.addWidget(self.track_selector)
        track_actions=QHBoxLayout()
        for title,callback in [('＋ Add track',self.add_frame_track),('− Remove track',self.remove_frame_track)]:
            button=QPushButton(title);button.clicked.connect(callback);track_actions.addWidget(button)
        self.advanced_layout.addLayout(track_actions)
        self.frame_slider=QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setRange(0,self.frames.value()-1)
        self.frame_slider.valueChanged.connect(self.show_timeline_frame)
        self.advanced_layout.addWidget(self.frame_slider)
        self.frame_label=QLabel('Frame 1 / 12');self.advanced_layout.addWidget(self.frame_label)
        self.frames.valueChanged.connect(self.timeline_count_changed)
        self.onion_enabled=QCheckBox('Onion skin (previous frame)')
        self.onion_enabled.toggled.connect(self.canvas.update)
        self.advanced_layout.addWidget(self.onion_enabled)
        for text,fn in [('Edit selected frame',self.enable_timeline),('Duplicate previous frame edits',self.duplicate_frame),('Clear frame edits',self.clear_frame),('Reset current frame',self.reset_current_frame),('Previous frame',lambda:self.step_frame(-1)),('Next frame',lambda:self.step_frame(1))]:
            b=QPushButton(text);b.clicked.connect(fn);self.advanced_layout.addWidget(b)
        motion_group=QGroupBox('↗ Movement keyframes — whole sprite')
        motion_layout=QVBoxLayout(motion_group)
        motion_layout.addWidget(QLabel('Set pixel offsets at two or more frames; movement fills in between.'))
        self.motion_x=QSpinBox();self.motion_y=QSpinBox()
        for control in (self.motion_x,self.motion_y):control.setRange(-512,512)
        movement=QFormLayout();movement.addRow('Horizontal (px)',self.motion_x);movement.addRow('Vertical (px)',self.motion_y)
        motion_layout.addLayout(movement)
        for title,fn in [('◆ Set movement keyframe',self.set_motion_keyframe),('⌫ Remove keyframe',self.remove_motion_keyframe),('↺ Clear all movement',self.clear_motion_keyframes)]:
            button=QPushButton(title);button.clicked.connect(fn);motion_layout.addWidget(button)
        self.motion_summary=QLabel('No movement keyframes yet')
        self.motion_summary.setWordWrap(True);motion_layout.addWidget(self.motion_summary)
        self.advanced_layout.addWidget(motion_group)
        layer_group=QGroupBox('◇ Selected layer movement — independent keyframes')
        layer_layout=QVBoxLayout(layer_group)
        layer_tip=QLabel('Choose an artwork layer in the left panel. Set movement at the current frame; other layers stay put.')
        layer_tip.setWordWrap(True);layer_layout.addWidget(layer_tip)
        self.layer_motion_x=QSpinBox();self.layer_motion_y=QSpinBox()
        for control in (self.layer_motion_x,self.layer_motion_y):control.setRange(-512,512)
        layer_form=QFormLayout();layer_form.addRow('Layer offset X',self.layer_motion_x);layer_form.addRow('Layer offset Y',self.layer_motion_y)
        layer_layout.addLayout(layer_form)
        for title,fn in [('◆ Set layer keyframe',self.set_layer_motion_keyframe),('⌫ Remove layer keyframe',self.remove_layer_motion_keyframe)]:
            b=QPushButton(title);b.clicked.connect(fn);layer_layout.addWidget(b)
        self.layer_motion_summary=QLabel('Select a layer to edit its movement')
        self.layer_motion_summary.setWordWrap(True);layer_layout.addWidget(self.layer_motion_summary)
        self.advanced_layout.addWidget(layer_group)
        self.timeline_markers=QLabel('◆ Keyframes appear here for the selected frame range')
        self.timeline_markers.setWordWrap(True);self.advanced_layout.addWidget(self.timeline_markers)

        clip_group=QGroupBox('▣ Reusable frame clips')
        clip_layout=QVBoxLayout(clip_group)
        clip_layout.addWidget(QLabel('Save a range of frames from the selected paint track. Paste into another frame or project.'))
        self.clip_start=QSpinBox();self.clip_end=QSpinBox()
        for spin in (self.clip_start,self.clip_end):spin.setRange(1,1000)
        self.clip_start.setValue(1);self.clip_end.setValue(3)
        range_form=QFormLayout();range_form.addRow('First frame',self.clip_start);range_form.addRow('Last frame',self.clip_end)
        clip_layout.addLayout(range_form)
        self.clip_selector=QComboBox();clip_layout.addWidget(self.clip_selector)
        for title,fn in [('＋ Save selected range as clip',self.save_frame_clip),('⇥ Paste clip at current frame',self.paste_frame_clip),('− Delete saved clip',self.delete_frame_clip)]:
            button=QPushButton(title);button.clicked.connect(fn);clip_layout.addWidget(button)
        self.advanced_layout.addWidget(clip_group)
        self.advanced_layout.addWidget(QLabel('Choose Frame Pencil or Frame Eraser to paint on the selected frame.'))
        self.advanced_layout.addStretch()
        av.addStretch()
        # Desktop Pet Builder: optional dock, using the existing sprite and animation engine.
        self.pet_workshop_dock=QDockWidget('Desktop Pet & Creature Studio',self)
        self.pet_workshop_dock.setObjectName('DesktopPetBuilderDock')
        self.pet_workshop_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.pet_workshop_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        pet_scroll=QScrollArea();pet_scroll.setWidgetResizable(True)
        pet_widget=QWidget();pet_layout=QVBoxLayout(pet_widget)
        pet_scroll.setWidget(pet_widget);self.pet_workshop_dock.setWidget(pet_scroll)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.pet_workshop_dock)
        self.pet_workshop_button.clicked.connect(self.toggle_pet_workshop)
        self.pet_workshop_dock.visibilityChanged.connect(self.pet_workshop_visibility_changed)
        wizard_group=QGroupBox('✨ Sprite Sheet Wizard — 3 easy steps')
        wizard_layout=QVBoxLayout(wizard_group)
        # Suggestions are independent of Guided Mode and never control the editing tools.
        self.pet_suggestions_toggle=QCheckBox('Show animation suggestions / recipes')
        self.pet_suggestions_toggle.setChecked(self.settings.value('pet_suggestions',True,type=bool))
        self.pet_suggestions_toggle.toggled.connect(self.update_pet_suggestions)
        wizard_layout.addWidget(self.pet_suggestions_toggle)
        self.pet_auto_toggle=QCheckBox('Enable automatic preset generation')
        self.pet_auto_toggle.setChecked(self.settings.value('pet_auto_generation',False,type=bool))
        self.pet_auto_toggle.toggled.connect(self.update_pet_auto_generation)
        wizard_layout.addWidget(self.pet_auto_toggle)
        wizard_layout.addWidget(QLabel('1. Upload a transparent creature PNG (or use the current canvas).'))
        self.pet_template_path=QLineEdit();self.pet_template_path.setPlaceholderText('Current canvas (default)')
        wizard_layout.addWidget(self.pet_template_path)
        pick_template=QPushButton('📁 Choose creature PNG')
        pick_template.clicked.connect(self.choose_pet_template)
        wizard_layout.addWidget(pick_template)
        wizard_layout.addWidget(QLabel('Creature body type (helps tailor your drawing plan):'))
        self.pet_body_type=QComboBox()
        self.pet_body_type.addItems(['General / unknown','Two-legged','Four-legged','Flying / winged','Floating / limbless','Crawling'])
        wizard_layout.addWidget(self.pet_body_type)
        rig_group=QGroupBox('✂ Optional body-part regions — pixel coordinates')
        rig_layout=QVBoxLayout(rig_group)
        rig_layout.addWidget(QLabel('Mark a rectangular part of your PNG. Leave empty for whole-body animation.\nRegions must not overlap. All values are source-image pixels.'))
        self.pet_regions={}
        self.pet_region_part=QComboBox();self.pet_region_part.addItems(RIG_PARTS)
        rig_layout.addWidget(self.pet_region_part)
        region_form=QFormLayout()
        self.pet_region_spins=[]
        for caption in ('X','Y','Width','Height'):
            spin=QSpinBox();spin.setRange(0 if caption in ('X','Y') else 1,1024)
            if caption in ('Width','Height'):spin.setValue(8)
            region_form.addRow(caption,spin);self.pet_region_spins.append(spin)
        rig_layout.addLayout(region_form)
        add_region=QPushButton('Save marked part');add_region.clicked.connect(self.save_pet_region)
        remove_region=QPushButton('Remove selected part');remove_region.clicked.connect(self.remove_pet_region)
        rig_layout.addWidget(add_region);rig_layout.addWidget(remove_region)
        self.pet_region_list=QListWidget();rig_layout.addWidget(self.pet_region_list)
        self.pet_region_list.itemClicked.connect(self.select_pet_region)
        wizard_layout.addWidget(rig_group)
        wizard_layout.addWidget(QLabel('2. Select starter animations (you can refine them later).'))
        self.pet_animation_checks={}
        life_group=QGroupBox('🐾 Everyday life — select any (31 recipes)')
        life_layout=QVBoxLayout(life_group)
        for animation in LIFE_ANIMATIONS:
            check=QCheckBox(animation)
            check.setChecked(animation in ('Idle breathing','Sleeping','Eating','Pooping','Happy bounce','Walking','Hopping'))
            self.pet_animation_checks[animation]=check
            life_layout.addWidget(check)
        wizard_layout.addWidget(life_group)
        extra_group=QGroupBox('Other / battle presets (optional)')
        extra_layout=QVBoxLayout(extra_group)
        for animation in ('Idle', 'Blink', 'Walk', 'Hop', 'Eat', 'Sleep', 'Poop')+BATTLE_ANIMATIONS:
            check=QCheckBox(animation)
            self.pet_animation_checks[animation]=check
            extra_layout.addWidget(check)
        wizard_layout.addWidget(extra_group)
        wizard_layout.addWidget(QLabel('Pose template parts (drawing guide, not required):'))
        self.pet_pose_template_hint=QLabel()
        self.pet_pose_template_hint.setWordWrap(True)
        wizard_layout.addWidget(self.pet_pose_template_hint)
        self.pet_body_type.currentTextChanged.connect(self.update_pet_pose_template_hint)
        self.update_pet_pose_template_hint()
        wizard_options=QFormLayout()
        self.pet_wizard_frames=QSpinBox();self.pet_wizard_frames.setRange(2,24);self.pet_wizard_frames.setValue(8)
        self.pet_wizard_fps=QSpinBox();self.pet_wizard_fps.setRange(1,30);self.pet_wizard_fps.setValue(8)
        wizard_options.addRow('Frames per animation',self.pet_wizard_frames)
        wizard_options.addRow('Playback FPS',self.pet_wizard_fps)
        wizard_layout.addLayout(wizard_options)
        guide_group=QGroupBox('📖 Animation Recipe — what should I draw?')
        guide_layout=QVBoxLayout(guide_group)
        self.pet_recipe_action=QComboBox();self.pet_recipe_action.addItems(ANIMATIONS)
        guide_layout.addWidget(self.pet_recipe_action)
        self.pet_recipe_text=QLabel();self.pet_recipe_text.setWordWrap(True)
        self.pet_recipe_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        guide_layout.addWidget(self.pet_recipe_text)
        for signal in (self.pet_recipe_action.currentTextChanged,self.pet_body_type.currentTextChanged):
            signal.connect(self.update_pet_animation_recipe)
        self.pet_wizard_frames.valueChanged.connect(self.update_pet_animation_recipe)
        wizard_layout.addWidget(guide_group)
        self.pet_recipe_group=guide_group
        self.pet_recipe_group.setVisible(self.pet_suggestions_toggle.isChecked())
        self.update_pet_animation_recipe()

        self.pet_export_frames=QCheckBox('Individual PNG frames');self.pet_export_frames.setChecked(True)
        self.pet_export_gif=QCheckBox('GIF previews');self.pet_export_gif.setChecked(True)
        self.pet_export_apng=QCheckBox('APNG previews (.png)');self.pet_export_apng.setChecked(True)
        for check in (self.pet_export_frames,self.pet_export_gif,self.pet_export_apng):wizard_layout.addWidget(check)
        wizard_layout.addWidget(QLabel('3. Generate a transparent sprite sheet + JSON.'))
        wizard_button=QPushButton('✨ Generate Sprite Sheet Package')
        wizard_button.clicked.connect(self.generate_pet_sprite_package)
        self.pet_generate_button=wizard_button
        self.pet_generate_button.setEnabled(self.pet_auto_toggle.isChecked())
        manual_button=QPushButton('🎨 Export current artwork as manual sprite sheet (no presets)')
        manual_button.clicked.connect(self.export_manual_pet_sprite)
        wizard_layout.addWidget(manual_button)
        wizard_layout.addWidget(wizard_button)
        warning=QLabel('Flattened PNGs use whole-body motion presets. Blinking and articulated limbs require editable layers/eye masks; no new anatomy is invented.')
        warning.setWordWrap(True);wizard_layout.addWidget(warning)
        pet_layout.addWidget(wizard_group)
        pet_layout.addWidget(QLabel('🐾 Set attachment anchors for reusable desktop-pet poses.'))
        self.pet_help=QLabel('Choose a pose, enter an anchor name and X/Y pixel coordinates, then save it in your project. Use anchors to align accessories between different poses.')
        self.pet_help.setWordWrap(True);pet_layout.addWidget(self.pet_help)
        self.pet_pose=QComboBox();self.pet_pose.addItems(['Idle','Walk','Run','Jump','Sleep','Crawl','Sit','Attack','Custom'])
        pet_layout.addWidget(QLabel('Pet pose'));pet_layout.addWidget(self.pet_pose)
        pose_transition_box=QGroupBox('↝ Pose transition preview')
        pose_transition_layout=QFormLayout(pose_transition_box)
        self.pose_start=QComboBox();self.pose_end=QComboBox()
        for selector in (self.pose_start,self.pose_end):selector.addItems(['Idle','Walk','Run','Jump','Sleep','Crawl','Sit','Attack','Custom'])
        self.pose_end.setCurrentText('Walk')
        pose_transition_layout.addRow('From pose',self.pose_start);pose_transition_layout.addRow('To pose',self.pose_end)
        self.pose_transition_preview=QLabel('Choose two poses to preview how shared anchors move.')
        self.pose_transition_preview.setWordWrap(True)
        button=QPushButton('↝ Preview anchor transition')
        button.clicked.connect(self.preview_pose_transition)
        pose_transition_layout.addRow(button);pose_transition_layout.addRow(self.pose_transition_preview)
        pet_layout.addWidget(pose_transition_box)
        self.pet_anchor_name=QComboBox();self.pet_anchor_name.setEditable(True)
        self.pet_anchor_name.addItems(['Head','Left Ear','Right Ear','Neck','Left Hand','Right Hand','Back','Feet','Tail','Accessory'])
        pet_layout.addWidget(QLabel('Attachment anchor'));pet_layout.addWidget(self.pet_anchor_name)
        self.pet_anchor_x=QSpinBox();self.pet_anchor_y=QSpinBox()
        for spin in (self.pet_anchor_x,self.pet_anchor_y):spin.setRange(0,2048)
        self.pet_anchor_x.setValue(32);self.pet_anchor_y.setValue(32)
        pet_coords=QFormLayout();pet_coords.addRow('Anchor X (px)',self.pet_anchor_x);pet_coords.addRow('Anchor Y (px)',self.pet_anchor_y)
        pet_layout.addLayout(pet_coords)
        save_anchor=QPushButton('📌 Save pose anchor');save_anchor.clicked.connect(self.save_pet_anchor);pet_layout.addWidget(save_anchor)
        remove_anchor=QPushButton('Remove selected anchor');remove_anchor.clicked.connect(self.remove_pet_anchor);pet_layout.addWidget(remove_anchor)
        self.pet_anchor_list=QListWidget();pet_layout.addWidget(self.pet_anchor_list)
        self.pet_anchor_list.itemClicked.connect(self.select_pet_anchor)
        self.pet_pose.currentTextChanged.connect(self.refresh_pet_anchors)
        self.show_pet_anchors=QCheckBox('Show pose anchors on canvas')
        self.show_pet_anchors.setChecked(True);self.show_pet_anchors.toggled.connect(self.canvas.update)
        pet_layout.addWidget(self.show_pet_anchors)
        place_anchor_button=QPushButton('⌖ Place anchor on canvas')
        place_anchor_button.clicked.connect(lambda:self.tool.setCurrentText('Pose Anchor'))
        pet_layout.addWidget(place_anchor_button)
        pet_layout.addWidget(QLabel('Anchors snap to whole sprite pixels and can be dragged with the Pose Anchor tool.'))
        clear_anchor=QPushButton('⌫ Erase selected pose anchor')
        clear_anchor.clicked.connect(self.remove_pet_anchor);pet_layout.addWidget(clear_anchor)
        reset_mesh=QPushButton('↺ Reset selected layer transform (mesh)')
        reset_mesh.setToolTip('Reset the selected layer to 100% scale and 0° rotation without deleting artwork.')
        reset_mesh.clicked.connect(self.reset_layer_mesh);pet_layout.addWidget(reset_mesh)
        pet_layout.addWidget(QLabel('Anchors are stored in editable project JSON and can be undone/redone.'))
        pet_layout.addStretch()
        # NFT tools live in an optional, independent dock rather than occupying
        # the main editor's permanent sidebar. Closing the dock preserves state.
        self.nft_manager_dock=QDockWidget('NFT Manager — Optional Tools',self)
        self.nft_manager_dock.setObjectName('NFTManagerDock')
        self.nft_manager_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea)
        self.nft_manager_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        nft_scroll=QScrollArea()
        nft_scroll.setWidgetResizable(True)
        self.nft_manager_tabs=QTabWidget()
        nft_scroll.setWidget(self.nft_manager_tabs)
        self.nft_manager_dock.setWidget(nft_scroll)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.nft_manager_dock)
        self.nft_manager_button.clicked.connect(self.toggle_nft_manager)
        self.nft_manager_dock.visibilityChanged.connect(self.nft_manager_visibility_changed)
        worksheet=QWidget();wv=QVBoxLayout(worksheet);self.nft_manager_tabs.addTab(worksheet,'NFT Worksheet')
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
        nft=QWidget();nv=QVBoxLayout(nft);self.nft_manager_tabs.addTab(nft,'Trait Generator')
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
        self.nft_manager_dock.hide()
        self.pet_workshop_dock.hide()
        self.install_beginner_helpers()
        self.update_guided_mode(self.guided_toggle.isChecked())
        self.activate_tool(self.tool.currentText())
        QTimer.singleShot(0,self.offer_recovery)
        self.statusBar().showMessage('Ready — import a PNG or create a layer. Choose Junior for quick effects or Intermediate for timeline editing.')
        self.setStyleSheet('''QWidget{background:#1b222e;color:#d8e3e5;font-family:"Segoe UI";font-size:13px}
        QPushButton,QComboBox,QSpinBox,QDoubleSpinBox,QListWidget,QTabWidget::pane{background:#2b3544;border:1px solid #445064;border-radius:7px;padding:6px}
        QPushButton:hover{background:#3c5260;border-color:#83d7b0}
        QPushButton:pressed{background:#467c6b}
        QComboBox:focus,QSpinBox:focus{border:2px solid #7bdbb2}
        QListWidget::item:selected{background:#496d65}
        QTabBar::tab{background:#25303d;padding:10px}
        QTabBar::tab:selected{background:#426758;color:#e1ffed}
        QLabel#activeToolBanner{background:#24473f;color:#b9f6d2;border:1px solid #63bfa0;border-radius:9px;padding:11px;font-size:14px;font-weight:700}
        QLabel#studioTitle{font-family:"Trebuchet MS","Segoe UI";font-size:20px;font-weight:800;color:#a8f3c6}
        QLabel#studioSubtitle{color:#a5b4c2;font-style:italic}
        QGroupBox{font-weight:700;border:1px solid #40566a;border-radius:8px;margin-top:10px;padding-top:12px}
        QGroupBox::title{color:#a8e7d0}
        QDockWidget::title{background:#29433f;color:#d3ffdf;font-weight:700;padding:8px}''')
    def install_beginner_helpers(self):
        """Keep the workspace simple while making every advanced tool discoverable."""
        hints={
            'Move / Transform':'Drag a layer to move it. Use corner handles to resize and the round handle to rotate.',
            'Pencil':'Draw on the selected layer. Create a blank paint layer if needed.',
            'Eraser':'Erase artwork pixels from the selected layer.',
            'Eyedropper':'Press I, then click a visible pixel to sample its color. Returns to your previous tool.',
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
        self.tool.setToolTip('Choose how the mouse interacts with the canvas. B: brush/pencil, E: eraser, I: eyedropper. B/E use the active drawing context.')
        self.layer_list.setToolTip('Select the artwork layer you want to edit.')
        self.setStatusTip('Tip: Import a PNG or create a blank layer to begin.')
        for keys,fn in [('Ctrl+Z',self.undo),('Ctrl+Shift+Z',self.redo),('Ctrl+Y',self.redo),('Ctrl+N',self.new_project),('I',self.activate_eyedropper),('B',self.activate_universal_brush),('E',self.activate_universal_eraser),('+',lambda:self.adjust_brush_size(1)),('=',lambda:self.adjust_brush_size(1)),('-',lambda:self.adjust_brush_size(-1)),('Ctrl+O',self.load_project),('Ctrl+S',self.save_project),('Ctrl+I',self.import_png),('Ctrl+E',self.export_choose_formats)]:
            shortcut=QShortcut(QKeySequence(keys),self);shortcut.activated.connect(fn)
        self.statusBar().showMessage('Ready! Import a PNG or create a blank layer. Hover over a tool for help.',9000)

    def setup_classic_menus(self):
        """Application-wide conventional File/Edit/View menus, independent of docks."""
        menu=self.menuBar()
        file_menu=menu.addMenu('&File')
        edit_menu=menu.addMenu('&Edit')
        view_menu=menu.addMenu('&View')
        def add(target,label,callback,shortcut=None):
            action=QAction(label,self)
            if shortcut:action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            target.addAction(action)
            return action
        # Existing shortcuts are kept for other commands; menu actions own these keys.
        add(file_menu,'&New Project',self.new_project,'Ctrl+N')
        add(file_menu,'&Open Project…',self.load_project)
        add(file_menu,'&Save Project…',self.save_project)
        file_menu.addSeparator()
        add(file_menu,'Import PNG Layer…',self.import_png)
        add(file_menu,'Export Animation…',self.export_choose_formats)
        add(edit_menu,'&Undo',self.undo)
        add(edit_menu,'&Redo',self.redo)
        add(view_menu,'Reset Canvas Zoom',lambda:self.canvas.reset_zoom() if hasattr(self,'canvas') else None,'Ctrl+0')
        add(view_menu,'Zoom In',lambda:self.adjust_canvas_zoom(1),'Ctrl++')
        add(view_menu,'Zoom Out',lambda:self.adjust_canvas_zoom(-1),'Ctrl+-')

    def adjust_canvas_zoom(self,direction):
        if not hasattr(self,'canvas'):return
        c=self.canvas;c.zoom_factor=max(0.1,min(32.0,c.zoom_factor*(1.2**direction)))
        c.update()

    def _drawing_context(self):
        """Choose the appropriate brush/eraser pair for the current editor.

        Preserve the current context when switching between B and E; otherwise
        use the selected animation editor's active drawing tool.
        """
        tool=self.tool.currentText()
        if tool in ('Frame Pencil','Frame Eraser'):
            return 'frame'
        if tool in ('Mask Brush','Mask Eraser'):
            return 'mask'
        if tool in ('Pencil','Eraser'):
            return 'base'
        return getattr(self,'last_drawing_context','base')

    def activate_universal_brush(self):
        context=self._drawing_context()
        self.last_drawing_context=context
        self.tool.setCurrentText({'base':'Pencil','frame':'Frame Pencil','mask':'Mask Brush'}[context])

    def activate_universal_eraser(self):
        context=self._drawing_context()
        self.last_drawing_context=context
        self.tool.setCurrentText({'base':'Eraser','frame':'Frame Eraser','mask':'Mask Eraser'}[context])

    def activate_eyedropper(self):
        current=self.tool.currentText()
        if current!='Eyedropper':self.eyedropper_previous_tool=current
        self.tool.setCurrentText('Eyedropper')
        self.statusBar().showMessage('Eyedropper: click a visible pixel to pick its color.',3000)

    # Each adjustable drawing tool has its own size. The two spinboxes remain
    # the source of truth for painting, while these values restore per-tool sizes.
    SIZABLE_TOOLS = ('Pencil', 'Eraser', 'Frame Pencil', 'Frame Eraser',
                     'Mask Brush', 'Mask Eraser')

    def _size_control(self, tool):
        if tool in ('Mask Brush', 'Mask Eraser'):
            return self.mask_brush
        if tool in ('Pencil', 'Eraser', 'Frame Pencil', 'Frame Eraser'):
            return self.brush
        return None

    def _remember_active_tool_size(self, value):
        tool = self.tool.currentText()
        if tool in self.SIZABLE_TOOLS:
            self._tool_sizes[tool] = int(value)

    def _restore_active_tool_size(self, tool):
        control = self._size_control(tool)
        if control is None:
            return
        control.blockSignals(True)
        control.setValue(self._tool_sizes.get(tool, 1))
        control.blockSignals(False)

    def adjust_brush_size(self, direction):
        tool = self.tool.currentText()
        control = self._size_control(tool)
        if control is None:
            self.statusBar().showMessage(f'{tool} has no adjustable brush size.', 1800)
            return
        value = max(control.minimum(), min(control.maximum(), control.value() + direction))
        control.setValue(value)
        self._tool_sizes[tool] = value
        self.statusBar().showMessage(f'{tool} size: {value} px', 1800)

    def new_project(self):
        if self._dirty:
            response=QMessageBox.question(self,'Start a new project?',
                'Unsaved changes will be lost. Save your current project before starting a new one?',
                QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save)
            if response==QMessageBox.StandardButton.Cancel:return
            if response==QMessageBox.StandardButton.Save:
                self.save_project()
                if self._dirty:return  # User cancelled Save As or save failed.
        # Reset the full editor document, including animation tracks and creature rigging.
        fresh=capture((64,64),[],[],{}, {},8,100,0,0)
        fresh.update(pet_anchors={},pet_regions={},frame_tracks={'Ink':{}},motion_keys={},
                     layer_motion_keys={},frame_clips={})
        self.restore_snapshot(fresh)
        self.history=UndoHistory()
        self.project_path=None;self._dirty=False
        self.recovery_path.unlink(missing_ok=True)
        self.sizes.blockSignals(True);self.sizes.setCurrentIndex(1);self.sizes.blockSignals(False)
        self.canvas.reset_zoom()
        self.statusBar().showMessage('New blank project ready',3500)

    def update_pet_suggestions(self, enabled):
        self.settings.setValue('pet_suggestions',bool(enabled))
        if hasattr(self,'pet_recipe_group'):
            self.pet_recipe_group.setVisible(bool(enabled))

    def update_pet_auto_generation(self, enabled):
        self.settings.setValue('pet_auto_generation',bool(enabled))
        if hasattr(self,'pet_generate_button'):
            self.pet_generate_button.setEnabled(bool(enabled))

    def export_manual_pet_sprite(self):
        # Export one editable starting frame without imposing a body type or preset.
        try:
            path=self.pet_template_path.text().strip()
            if path:
                with Image.open(path) as loaded: source=loaded.convert('RGBA')
            else:
                source=self.current_image().convert('RGBA')
            folder=QFileDialog.getExistingDirectory(self,'Choose manual sprite sheet folder')
            if not folder:return
            name,ok=QInputDialog.getText(self,'Creature name','Export file prefix:',text='my_pet')
            if not ok:return
            export_pet_package({'Custom':[source]},folder,name,self.pet_wizard_fps.value(),
                self.pet_export_frames.isChecked(),False,False,getattr(self,'pet_anchors',{}))
            QMessageBox.information(self,'Manual sprite sheet ready',f'Exported an editable single-frame custom sprite sheet and JSON to:\n{folder}')
        except Exception as exc:
            QMessageBox.critical(self,'Manual sprite sheet export failed',str(exc))

    def update_guided_mode(self,enabled):
        self.settings.setValue('guided_mode',bool(enabled))
        self.active_tool_banner.setVisible(enabled)
        self.pet_help.setVisible(enabled)
        self.statusBar().showMessage('Guided Mode on — tool tips are visible' if enabled else 'Guided Mode off — compact workspace',3500)

    def toggle_pet_workshop(self):
        if self.pet_workshop_dock.isVisible():self.pet_workshop_dock.hide()
        else:self.pet_workshop_dock.show();self.pet_workshop_dock.raise_()

    def choose_pet_template(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose pet template','','PNG Images (*.png)')
        if path:self.pet_template_path.setText(path)

    def update_pet_pose_template_hint(self, *args):
        body_type=self.pet_body_type.currentText()
        self.pet_pose_template_hint.setText('Suggested editable layers: '+', '.join(POSE_TEMPLATES.get(body_type, ())))

    def update_pet_animation_recipe(self, *args):
        try:
            guide=animation_guide(self.pet_recipe_action.currentText(),
                self.pet_wizard_frames.value(),self.pet_body_type.currentText())
            self.pet_recipe_text.setText(format_animation_guide(guide))
        except Exception as exc:
            self.pet_recipe_text.setText(str(exc))

    def save_pet_region(self):
        name=self.pet_region_part.currentText()
        rect=[spin.value() for spin in self.pet_region_spins]
        try:
            path=self.pet_template_path.text().strip()
            if path:
                with Image.open(path) as im:size=im.size
            else:size=self.current_image().size
            updated={**self.pet_regions,name:rect}
            self.pet_regions=validate_regions(updated,size)
            self.refresh_pet_regions()
        except Exception as exc:
            QMessageBox.warning(self,'Invalid body region',str(exc))

    def remove_pet_region(self):
        name=self.pet_region_part.currentText()
        self.pet_regions.pop(name,None)
        self.refresh_pet_regions()

    def select_pet_region(self,item):
        name=item.data(Qt.ItemDataRole.UserRole)
        self.pet_region_part.setCurrentText(name)
        for spin,value in zip(self.pet_region_spins,self.pet_regions[name]):spin.setValue(value)

    def refresh_pet_regions(self):
        self.pet_region_list.clear()
        for name,rect in sorted(self.pet_regions.items()):
            item=QListWidgetItem(f'{name}: {rect}')
            item.setData(Qt.ItemDataRole.UserRole,name)
            self.pet_region_list.addItem(item)

    def generate_pet_sprite_package(self):
        try:
            path=self.pet_template_path.text().strip()
            if path:
                with Image.open(path) as loaded: source=loaded.convert('RGBA')
            else:
                source=self.current_image().convert('RGBA')
            actions=[name for name,check in self.pet_animation_checks.items() if check.isChecked()]
            if not actions:
                QMessageBox.warning(self,'No animations','Select at least one animation preset.')
                return
            folder=QFileDialog.getExistingDirectory(self,'Choose sprite sheet export folder')
            if not folder:return
            name,ok=QInputDialog.getText(self,'Creature name','Export file prefix:',text='my_pet')
            if not ok:return
            animations=generate_rigged(source,actions,self.pet_regions,self.pet_wizard_frames.value())
            export_pet_package(animations,folder,name,self.pet_wizard_fps.value(),
                self.pet_export_frames.isChecked(),self.pet_export_gif.isChecked(),self.pet_export_apng.isChecked(),
                {'pose_anchors':getattr(self,'pet_anchors',{}),'body_regions':validate_regions(self.pet_regions,source.size)})
            if self.pet_suggestions_toggle.isChecked():
                export_animation_guides(actions,folder,name,self.pet_wizard_frames.value(),self.pet_body_type.currentText())
            QMessageBox.information(self,'Sprite sheet ready',f'Created {len(actions)} animations in:\n{folder}\n\nPNG sprite sheet + JSON metadata included.')
        except Exception as exc:
            QMessageBox.critical(self,'Sprite sheet export failed',str(exc))

    def pet_workshop_visibility_changed(self,visible):
        self.pet_workshop_button.setText('🐾 Hide Desktop Pet Builder' if visible else '🐾 Open Desktop Pet Builder')

    def reset_layer_mesh(self):
        layer=self.selected_layer()
        if layer is None:
            QMessageBox.information(self,'Select a layer','Choose an artwork layer to reset.');return
        self.checkpoint()
        layer.scale=1.0;layer.angle=0
        self.update_layer_controls();self.invalidate()
        self.statusBar().showMessage('Layer transform reset — artwork pixels preserved.',4000)

    def save_pet_anchor(self):
        name=self.pet_anchor_name.currentText().strip()
        if not name:
            QMessageBox.warning(self,'Missing anchor name','Enter an anchor name.');return
        self.checkpoint()
        pose=self.pet_pose.currentText()
        self.pet_anchors.setdefault(pose,{})[name]=[self.pet_anchor_x.value(),self.pet_anchor_y.value()]
        self.refresh_pet_anchors()

    def remove_pet_anchor(self):
        item=self.pet_anchor_list.currentItem()
        if item is None:return
        pose=self.pet_pose.currentText();name=item.data(Qt.ItemDataRole.UserRole)
        if name in self.pet_anchors.get(pose,{}):
            self.checkpoint();del self.pet_anchors[pose][name];self.refresh_pet_anchors()

    def refresh_pet_anchors(self,*args):
        self.pet_anchor_list.clear()
        for name,xy in sorted(self.pet_anchors.get(self.pet_pose.currentText(),{}).items()):
            from PySide6.QtWidgets import QListWidgetItem
            item=QListWidgetItem(f'{name}: ({xy[0]}, {xy[1]})')
            item.setData(Qt.ItemDataRole.UserRole,name)
            self.pet_anchor_list.addItem(item)

    def select_pet_anchor(self,item):
        name=item.data(Qt.ItemDataRole.UserRole)
        xy=self.pet_anchors.get(self.pet_pose.currentText(),{}).get(name)
        if xy:
            self.pet_anchor_name.setCurrentText(name)
            self.pet_anchor_x.setValue(xy[0]);self.pet_anchor_y.setValue(xy[1])

    def toggle_nft_manager(self):
        if self.nft_manager_dock.isVisible():
            self.nft_manager_dock.hide()
        else:
            self.nft_manager_dock.show()
            self.nft_manager_dock.raise_()

    def nft_manager_visibility_changed(self,visible):
        self.nft_manager_button.setText('🐱 Hide NFT Manager' if visible else '🐱 Open NFT Manager')

    def toggle_animator(self):
        self.animator_dock.setVisible(not self.animator_dock.isVisible())
        if self.animator_dock.isVisible():self.animator_dock.raise_()
    def animator_visibility_changed(self,visible):
        self.animator_button.setText('✨ Hide Junior Animator' if visible else '✨ Open Junior Animator')
    def toggle_advanced_animator(self):
        self.advanced_animator_dock.setVisible(not self.advanced_animator_dock.isVisible())
        if self.advanced_animator_dock.isVisible():self.advanced_animator_dock.raise_()
    def advanced_animator_visibility_changed(self,visible):
        self.advanced_animator_button.setText('🎞 Hide Intermediate Studio' if visible else '🎞 Open Intermediate Studio')
    def activate_tool(self,tool):
        self._restore_active_tool_size(tool)
        # Changing tools must visibly activate the canvas mode; it should not
        # silently deselect the art and leave the user wondering what happened.
        labels={
            'Move / Transform':('↔','Drag artwork to move, resize or rotate','#b9e4c9'),
            'Pencil':('✏','Draw on your selected layer','#ffe3a1'),
            'Eyedropper':('◉','Click a visible pixel to sample its color (I)','#c4b5fd'),
            'Eraser':('⌫','Erase artwork on your selected layer','#ffb6b6'),
            'Animation Region':('▭','Drag a rectangle (Advanced / legacy)','#d5bbef'),
            'Mask Brush':('🖍','Paint highlights over pixels to animate','#91e6bb'),
            'Mask Eraser':('◌','Brush away highlights; art stays safe','#a7d3ff'),
            'Frame Pencil':('✎','Draw on the selected animation frame','#f5cf9c'),
            'Frame Eraser':('⌫','Erase on the selected animation frame','#ffb9bd'),
            'Pose Anchor':('⌖','Click to place or drag an attachment anchor','#ffdc8b'),
        }
        symbol,tip,color=labels.get(tool,('•','Click on the canvas','#b9e4c9'))
        self.active_tool_banner.setText(f'{symbol}  {tool}\\n{tip}')
        self.active_tool_banner.setStyleSheet(f'QLabel#activeToolBanner {{ border-color:{color}; }}')
        if tool in ('Pencil','Eraser','Move / Transform') and self.layers and self.layer_list.currentRow()<0:
            self.layer_list.setCurrentRow(len(self.layers)-1)
        if tool in ('Pencil','Eraser') and not self.layers:
            self.statusBar().showMessage('Pencil is ready: click the canvas to create a paint layer and draw.',7000)
        else:
            self.statusBar().showMessage(f'Active tool: {tool} — {tip}',5000)
        self.canvas.setCursor(cursor_for_tool(tool))
        self.open_animator_for_tool(tool)
        self.canvas.update()

    def open_animator_for_tool(self,tool):
        if tool in ('Animation Region','Mask Brush','Mask Eraser'):
            self.animator_dock.show();self.animator_dock.raise_()
        elif tool in ('Frame Pencil','Frame Eraser'):
            self.advanced_animator_dock.show();self.advanced_animator_dock.raise_()
    def invalidate(self):self.stop_preview();self.canvas.update()
    def stop_preview(self):
        self.timer.stop();self.preview=[]
        if hasattr(self,'preview_hint'):self.preview_hint.setText('Preview stopped. Highlight pixels or choose another effect.')
        self.canvas.update()
    def current_image(self):
        if self.preview:return self.preview[self.index]
        if self.timeline_mode:return self.timeline_frames()[self.frame_slider.value()]
        return composite(self.layers,self.size_px)
    def sync_frame_edits(self):
        # Existing renderer consumes flattened edits; separate editable tracks
        # remain in frame_tracks, in visible track order (last track wins).
        merged={}
        for track in self.frame_tracks.values():
            for frame,strokes in track.items():
                pixels=merged.setdefault(str(frame),{})
                for stroke in strokes:pixels[(int(stroke[0]),int(stroke[1]))]=list(stroke)
        self.frame_edits={frame:list(pixels.values()) for frame,pixels in merged.items()}

    def switch_frame_track(self,*args):
        self.canvas.update()

    def add_frame_track(self):
        name,ok=QInputDialog.getText(self,'Add animation track','Track name:')
        name=name.strip()
        if not ok or not name:return
        if name in self.frame_tracks:
            QMessageBox.information(self,'Track exists','Choose a different track name.');return
        self.checkpoint();self.frame_tracks[name]={};self.track_selector.addItem(name)
        self.track_selector.setCurrentText(name)

    def remove_frame_track(self):
        name=self.track_selector.currentText()
        if len(self.frame_tracks)<=1:
            QMessageBox.information(self,'Keep one track','At least one frame track is required.');return
        if QMessageBox.question(self,'Remove track?',f'Remove track "{name}" and its frame edits?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.checkpoint();del self.frame_tracks[name];self.track_selector.removeItem(self.track_selector.currentIndex())
        self.sync_frame_edits();self.invalidate()

    def reset_current_frame(self):
        frame=str(self.frame_slider.value())
        if not any(frame in track for track in self.frame_tracks.values()):return
        if QMessageBox.question(self,'Reset frame?', 'Remove edits on this frame from ALL tracks?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.checkpoint()
        for track in self.frame_tracks.values():track.pop(frame,None)
        self.sync_frame_edits();self.enable_timeline()

    def set_motion_keyframe(self):
        self.checkpoint();self.motion_keys[str(self.frame_slider.value())]=[self.motion_x.value(),self.motion_y.value()]
        self.refresh_motion_summary();self.refresh_timeline_markers();self.enable_timeline()

    def remove_motion_keyframe(self):
        key=str(self.frame_slider.value())
        if key not in self.motion_keys:return
        self.checkpoint();del self.motion_keys[key];self.refresh_motion_summary();self.enable_timeline()

    def clear_motion_keyframes(self):
        if not self.motion_keys:return
        self.checkpoint();self.motion_keys={};self.refresh_motion_summary();self.enable_timeline()

    def refresh_motion_summary(self):
        keys=sorted(self.motion_keys,key=lambda k:int(k))
        self.motion_summary.setText('Keyframes: '+(', '.join(str(int(k)+1) for k in keys) if keys else 'none'))
        self.refresh_timeline_markers()
        key=self.motion_keys.get(str(self.frame_slider.value()),[0,0])
        self.motion_x.blockSignals(True);self.motion_y.blockSignals(True)
        self.motion_x.setValue(int(key[0]));self.motion_y.setValue(int(key[1]))
        self.motion_x.blockSignals(False);self.motion_y.blockSignals(False)

    def save_frame_clip(self):
        start=self.clip_start.value()-1;end=self.clip_end.value()-1
        if end<start or end>=self.frames.value():
            QMessageBox.warning(self,'Invalid range','Choose frames within the timeline, with the first before the last.');return
        name,ok=QInputDialog.getText(self,'Save reusable clip','Clip name:')
        if not ok or not name.strip():return
        name=name.strip()
        if name in self.frame_clips:
            QMessageBox.warning(self,'Name in use','Choose a new clip name.');return
        track=self.frame_tracks[self.track_selector.currentText()]
        data={str(i-start):json.loads(json.dumps(track.get(str(i),[]))) for i in range(start,end+1)}
        self.checkpoint();self.frame_clips[name]=data;self.clip_selector.addItem(name)
        self.clip_selector.setCurrentText(name)
        self.statusBar().showMessage(f'Clip saved: {name} ({end-start+1} frames)',4000)

    def paste_frame_clip(self):
        name=self.clip_selector.currentText()
        if name not in self.frame_clips:return
        self.checkpoint();track_name=self.track_selector.currentText()
        self.frame_tracks[track_name]=paste_clip(self.frame_tracks[track_name],self.frame_clips[name],self.frame_slider.value(),self.frames.value())
        self.sync_frame_edits();self.enable_timeline()

    def delete_frame_clip(self):
        name=self.clip_selector.currentText()
        if name not in self.frame_clips:return
        self.checkpoint();del self.frame_clips[name];self.clip_selector.removeItem(self.clip_selector.currentIndex())

    def set_layer_motion_keyframe(self):
        index=self.layer_list.currentRow()
        if index<0 or index>=len(self.layers):
            QMessageBox.information(self,'Choose a layer','Select an artwork layer first.');return
        self.checkpoint()
        self.layer_motion_keys.setdefault(str(index),{})[str(self.frame_slider.value())]=[self.layer_motion_x.value(),self.layer_motion_y.value()]
        self.refresh_layer_motion();self.enable_timeline()

    def remove_layer_motion_keyframe(self):
        index=str(self.layer_list.currentRow());frame=str(self.frame_slider.value())
        if frame not in self.layer_motion_keys.get(index,{}):return
        self.checkpoint();self.layer_motion_keys[index].pop(frame)
        self.refresh_layer_motion();self.enable_timeline()

    def refresh_layer_motion(self,*args):
        if not hasattr(self,'layer_motion_summary'):return
        index=self.layer_list.currentRow();keys=self.layer_motion_keys.get(str(index),{})
        self.layer_motion_summary.setText('Layer keyframes: '+(', '.join(str(int(k)+1) for k in sorted(keys,key=int)) if keys else 'none'))
        value=keys.get(str(self.frame_slider.value()),[0,0])
        for spin,n in ((self.layer_motion_x,0),(self.layer_motion_y,1)):
            spin.blockSignals(True);spin.setValue(int(value[n]));spin.blockSignals(False)
        self.refresh_timeline_markers()

    def refresh_timeline_markers(self):
        if not hasattr(self,'timeline_markers'):return
        global_keys=set(map(int,self.motion_keys))
        local_keys=set(map(int,self.layer_motion_keys.get(str(self.layer_list.currentRow()),{})))
        total=self.frames.value()
        # Compact keyframe strip, with ◆ for the selected layer, ● for whole sprite.
        symbols=['◆' if i in local_keys else '●' if i in global_keys else '·' for i in range(total)]
        self.timeline_markers.setText('Frame markers (◆ layer, ● whole sprite):\n'+' '.join(symbols))

    def preview_pose_transition(self):
        start=self.pose_start.currentText();end=self.pose_end.currentText()
        sequence=interpolate_pose_anchors(self.pet_anchors,start,end,self.frames.value())
        self.pose_transition={'start':start,'end':end,'anchors':sequence}
        self.pose_transition_preview.setText(f'{start} → {end}: {len(sequence)} interpolated anchor frames.\n'
            +' | '.join(f'{name}: {pos}' for name,pos in list(sequence[-1].items())[:4])
            +'\nAnchor motion preview only; artwork pose morphing is not implied.')
        self.canvas.update()

    def timeline_frames(self):
        return compose_layer_motion_frames(self.layers,self.size_px,self.regions,self.frames.value(),self.frame_edits,self.layer_motion_keys,self.motion_keys)
    def show_timeline_frame(self,*args):
        self.stop_preview();self.timeline_mode=True
        self.frame_label.setText(f'Frame {self.frame_slider.value()+1} / {self.frames.value()}')
        self.refresh_motion_summary();self.refresh_layer_motion();self.canvas.update()
    def timeline_count_changed(self,*args):
        self.frame_slider.setMaximum(self.frames.value()-1)
        self.frame_label.setText(f'Frame {self.frame_slider.value()+1} / {self.frames.value()}')
        self.refresh_timeline_markers();self.canvas.update()
    def enable_timeline(self):
        self.stop_preview();self.timeline_mode=True;self.canvas.update()
    def step_frame(self,step):
        self.frame_slider.setValue((self.frame_slider.value()+step)%self.frames.value())
    def duplicate_frame(self):
        i=self.frame_slider.value()
        if i==0:return
        self.checkpoint();track=self.frame_tracks[self.track_selector.currentText()]
        track[str(i)]=[list(p) for p in track.get(str(i-1),[])]
        self.sync_frame_edits()
        self.enable_timeline()
    def clear_frame(self):
        if str(self.frame_slider.value()) in self.frame_tracks[self.track_selector.currentText()]:
            if QMessageBox.question(self,'Clear frame edits?','Remove the hand-drawn changes on this frame?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.checkpoint();self.frame_tracks[self.track_selector.currentText()].pop(str(self.frame_slider.value()),None);self.sync_frame_edits()
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
        self.checkpoint();self.layers[i],self.layers[j]=self.layers[j],self.layers[i]
        keys_i=self.layer_motion_keys.pop(str(i),None);keys_j=self.layer_motion_keys.pop(str(j),None)
        if keys_i is not None:self.layer_motion_keys[str(j)]=keys_i
        if keys_j is not None:self.layer_motion_keys[str(i)]=keys_j
        item=self.layer_list.takeItem(i);self.layer_list.insertItem(j,item);self.layer_list.setCurrentRow(j);self.invalidate()
    def remove_layer(self):
        i=self.layer_list.currentRow()
        if i>=0:
            if QMessageBox.question(self,'Delete layer?','Remove the selected layer? You can undo this with Ctrl+Z.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            self.checkpoint();self.layers.pop(i)
            self.layer_motion_keys={str(int(k)-(int(k)>i)):v for k,v in self.layer_motion_keys.items() if int(k)!=i}
            self.layer_list.takeItem(i);self.invalidate()
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
    def begin_highlighting(self):
        if not self.regions:
            self.add_region((0,0,*self.size_px))
        elif self.region_list.currentRow()<0:
            self.region_list.setCurrentRow(0)
        self.timeline_mode=False
        self.tool.setCurrentText('Mask Brush')
        self.animator_dock.show()
        self.statusBar().showMessage('Paint green highlights on the sprite, choose an effect, then press Preview.',8000)

    def start_preview(self):
        if not self.layers:
            self.preview_hint.setText('Import a PNG or create a paint layer before previewing.')
            self.statusBar().showMessage('Import artwork first to preview an animation.',5000)
            return
        if not self.regions:
            self.preview_hint.setText('Click Highlight to animate, paint on the sprite, then preview.')
            self.statusBar().showMessage('Choose the pixels to animate first.',5000)
            return
        if not any(r.mask for r in self.regions):
            self.preview_hint.setText('No pixels highlighted yet! Click Highlight to animate and paint on your sprite.')
            self.statusBar().showMessage('Paint highlights over the part you want moving.',6000)
            return
        self.timer.stop()
        self.preview=self.make_frames()
        if len(self.preview)<2:
            self.preview_hint.setText('Not enough frames to play. Increase the frame count.')
            return
        self.timeline_mode=False
        self.index=0
        self.preview_hint.setText('▶ Playing on the main canvas — press Stop to edit.')
        self.timer.start(self.duration.value())
        self.canvas.update()
    def next_frame(self):
        if self.preview:self.index=(self.index+1)%len(self.preview);self.canvas.update()
    def apply_speed_preset(self,index):
        values={1:200,2:100,3:67,4:42,5:33}
        if index in values:self.duration.setValue(values[index])
    def update_duration_summary(self,*args):
        ms=self.duration.value();count=self.frames.value()
        self.fps_label.setText(f'{1000/ms:.1f} FPS')
        self.total_duration_label.setText(f'{count*ms/1000:.2f} seconds ({count} frames)')
    def update_export_tip(self,*args):
        descriptions=[
            '✨ APNG: full-color moving sprite with transparency. Open in a browser or animation-capable viewer.',
            '🎞 GIF: moving sprite for easy sharing; 256-color limit and 10 ms timing steps.',
            '▦ Sprite sheet: one wide PNG containing every frame. It will NOT play by itself.',
            '🖼 Still PNG: saves ONE frame only. It will NOT animate.',
        ]
        if hasattr(self,'export_tip'):
            self.export_tip.setText(descriptions[self.export_format.currentIndex()])

    def export_choose_formats(self):
        """One export action with independently selectable APNG, GIF, and still PNG."""
        dialog=QDialog(self)
        dialog.setWindowTitle('Export your sprite ✨')
        layout=QVBoxLayout(dialog)
        intro=QLabel('Choose one, two, or all three formats. Animated files use the same preview frames.')
        intro.setWordWrap(True)
        layout.addWidget(intro)
        apng=QCheckBox('✨ Animated PNG (APNG) — full-color, transparent, moving')
        gif=QCheckBox('🎞 Animated GIF — moving, easy to share')
        still=QCheckBox('🖼 Still PNG — one frame, does not move')
        for check in (apng,gif,still):
            check.setChecked(True)
            layout.addWidget(check)
        note=QLabel('All three are selected by default. Uncheck anything you do not want.')
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Export selected formats')
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        selected=[apng.isChecked(),gif.isChecked(),still.isChecked()]
        if not any(selected):
            QMessageBox.information(self,'Nothing selected','Select at least one export format.')
            return
        folder=QFileDialog.getExistingDirectory(self,'Choose a folder for your exported sprite')
        if not folder:return
        name,ok=QInputDialog.getText(self,'Sprite filename','Base filename (without extension):',text='my_sprite')
        if not ok:return
        name=name.strip()
        if not name or name in ('.','..') or any(c in name for c in '/\\\\:*?"<>|'):
            QMessageBox.warning(self,'Invalid filename','Please enter a simple filename without slashes or special characters.')
            return
        output=Path(folder)
        paths=[output/(name+suffix) for chosen,suffix in zip(selected,('_animated.png','_animated.gif','_still.png')) if chosen]
        if any(path.exists() for path in paths):
            answer=QMessageBox.question(self,'Replace existing files?',
                'One or more selected files already exist. Replace them?',
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer!=QMessageBox.StandardButton.Yes:return
        frames=self.make_frames() if selected[0] or selected[1] else []
        saved=[]
        errors=[]
        operations=[
            (selected[0],output/(name+'_animated.png'),lambda path:export_apng(frames,path,self.duration.value(),self.loop_count.value())),
            (selected[1],output/(name+'_animated.gif'),lambda path:export_gif(frames,path,self.duration.value(),self.loop_count.value())),
            (selected[2],output/(name+'_still.png'),lambda path:composite(self.layers,self.size_px).save(path)),
        ]
        for enabled,path,write in operations:
            if not enabled:continue
            try:
                write(path)
                if path.name.endswith('_animated.gif') or path.name.endswith('_animated.png'):
                    with Image.open(path) as check:
                        if getattr(check,'n_frames',1)<2:
                            raise RuntimeError('File contains only one frame; choose an effect that changes over time.')
                saved.append(path.name)
            except Exception as exc:
                errors.append(f'{path.name}: {exc}')
        if errors:
            QMessageBox.warning(self,'Export needs attention',
                ('Saved: '+', '.join(saved)+'\\n\\n' if saved else '')+'\\n'.join(errors))
        else:
            QMessageBox.information(self,'Your sprite is exported! 🎉',
                'Saved to '+str(output)+'\\n\\n'+'\\n'.join(saved))

    def save_gif(self):
        path,_=QFileDialog.getSaveFileName(self,'Export moving GIF','animation.gif','Animated GIF (*.gif)')
        if not path:return
        try:
            export_gif(self.make_frames(),path,self.duration.value(),self.loop_count.value())
            with Image.open(path) as check:
                if getattr(check,'n_frames',1)<2:raise RuntimeError('GIF contains only one frame')
            QMessageBox.information(self,'Moving GIF exported',f'Animated GIF saved to {path}\nOpen in a browser to see it move.')
        except Exception as e:QMessageBox.warning(self,'GIF export failed',str(e))

    def export_selected_format(self):
        selected=self.export_format.currentIndex()
        if selected==0:return self.save_apng()
        if selected==3:return self.save_png()
        frames=self.make_frames()
        if selected==1:return self.save_gif()
        if selected==2:
            path,_=QFileDialog.getSaveFileName(self,'Export sprite sheet','sprite_sheet.png','PNG (*.png)')
            if not path:return
            try:
                export_sprite_sheet(frames,path)
                QMessageBox.information(self,'Sprite sheet exported',f'Saved {len(frames)} frames to {path}')
            except Exception as e:QMessageBox.warning(self,'Sprite sheet export failed',str(e))
    def save_apng(self):
        path,_=QFileDialog.getSaveFileName(self,'Export moving APNG','animation.png','Animated PNG (*.png *.apng)')
        if path:
            try:export_apng(self.make_frames(),path,self.duration.value(),self.loop_count.value());QMessageBox.information(self,'Moving APNG exported',f'Animated PNG saved to {path}\nThis is an animated PNG (APNG), even if the filename ends in .png. Open in a browser to see it move.')
            except Exception as e:QMessageBox.warning(self,'Animation export',str(e))
    def save_png(self):
        path,_=QFileDialog.getSaveFileName(self,'Export STILL image (no animation)','sprite_still.png','Still PNG (*.png)')
        if path:
            if QMessageBox.question(self,'Export a still image?',
                'A still PNG will NOT move. For animation, use Export MOVING Sprite (APNG) or Export MOVING GIF.\n\nSave one still frame anyway?',
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            composite(self.layers,self.size_px).save(path)
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
        obj=capture(self.size_px,self.layers,self.regions,self.traits,self.frame_edits,
                    self.frames.value(),self.duration.value(),self.loop_count.value(),self.export_format.currentIndex())
        obj['pet_anchors']=json.loads(json.dumps(self.pet_anchors))
        obj['pet_regions']=json.loads(json.dumps(self.pet_regions))
        obj['frame_tracks']=json.loads(json.dumps(self.frame_tracks))
        obj['motion_keys']=json.loads(json.dumps(self.motion_keys))
        obj['layer_motion_keys']=json.loads(json.dumps(self.layer_motion_keys))
        obj['frame_clips']=json.loads(json.dumps(self.frame_clips))
        return obj

    def checkpoint(self):
        if not self._restoring:
            self.history.record(self.snapshot())
            self._dirty=True

    def restore_snapshot(self,obj):
        size,layers,regions=decode(obj)
        self._restoring=True
        try:
            self.size_px=size;self.layers=layers;self.regions=regions
            self.traits=obj.get('traits',{});self.frame_edits=obj.get('frame_edits',{});self.pet_anchors=obj.get('pet_anchors',{});self.pet_regions=obj.get('pet_regions',{})
            self.frame_tracks=obj.get('frame_tracks') or {'Ink':json.loads(json.dumps(self.frame_edits))}
            self.motion_keys=obj.get('motion_keys',{})
            self.layer_motion_keys=obj.get('layer_motion_keys',{})
            self.frame_clips=obj.get('frame_clips',{})
            self.clip_selector.clear();self.clip_selector.addItems(list(self.frame_clips))
            self.track_selector.blockSignals(True);self.track_selector.clear();self.track_selector.addItems(list(self.frame_tracks));self.track_selector.blockSignals(False)
            self.sync_frame_edits();self.refresh_motion_summary();self.refresh_layer_motion()
            self.frames.setValue(obj.get('frame_count',8));self.duration.setValue(obj.get('frame_duration',100))
            self.loop_count.setValue(obj.get('animation_loops',0));self.export_format.setCurrentIndex(obj.get('export_format',0))
            self.timeline_mode=bool(self.frame_edits)
            self.layer_list.clear();self.layer_list.addItems([l.name for l in layers])
            self.region_list.clear();self.region_list.addItems([r.name for r in regions])
            if layers:self.layer_list.setCurrentRow(len(layers)-1)
            if regions:self.region_list.setCurrentRow(0)
            self.refresh_traits();self.refresh_pet_anchors();self.refresh_pet_regions();self.invalidate()
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

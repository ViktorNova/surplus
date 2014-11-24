#!/usr/bin/env python
'''
SHORTCUTS:
    arrow keys navigate in/out of directories
    space + enter trigger playback
    TODO:
        tab to switch between plugins/files
        slash to search
        settings dialog ctrl+P

TODO:
    use qt signals instead of setting fields
    checkbox to disable/enable playback
    show waveform
    settings dialogue
        default location
        plugin paths
    make favorites
    selection box resizes with window
    remove outline from selection box
    figure out how to get information from plugins
    don't use play?

BUGS:
    select box behavior resets if you unfocus&refocus window

possible features:
    smart sample searching (probably not)
    touch interaction (probably)

'''
import sys, os, subprocess
from PyQt4 import QtGui, QtCore

line_height= 25

exts = ['wav','mp3','ogg','flac','m4a']

def play(a_file):
    subprocess.Popen(['play', a_file], close_fds=True)

class listItem(QtGui.QGraphicsRectItem):
    def __init__(self, text, isFile=True):
        QtGui.QGraphicsRectItem.__init__(self, 0, 0, 425, line_height)
        clearpen = QtGui.QPen(QtGui.QColor(0,0,0,0))
        self.setPen(clearpen)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        if not isFile:
            self.label = QtGui.QGraphicsSimpleTextItem(text+'/', parent=self)
        else:
            self.label = QtGui.QGraphicsSimpleTextItem(text, parent=self)
        self.label.setPos(10, 5)
        self.label.setBrush(QtCore.Qt.white)
        self.isFile = isFile
        if not isFile:
            font = QtGui.QFont()
            font.setBold(True)
            self.label.setFont(font)

    def playSample(self):
        play(self.label.text())

    def setSelected(self, selected):
        QtGui.QGraphicsRectItem.setSelected(self, selected)
        if selected:
            self.scene().views()[0].ensureVisible(self, xMargin=-50)
            self.setBrush(QtGui.QColor(50,102,150))

            if self.isFile:
                self.playSample()
                #play(self.label.text())
        else:
            self.setBrush(QtGui.QColor(50,50,50))

    def mousePressEvent(self, event):
        #QtGui.QPushButton.mousePressEvent(self, event)
        if not self.isSelected():
            for item in self.scene().selectedItems():
                item.setSelected(False)
            self.setSelected(True)
        else:
            self.playSample()
    
    def mouseMoveEvent(self, event):
        if self.isFile:
            mimeData = QtCore.QMimeData()
            path = os.path.abspath(str(self.label.text()))
            mimeData.setUrls([QtCore.QUrl.fromLocalFile(os.path.abspath(str(self.label.text())))])

            #view = self.scene().views()[0]
            #sceneP = self.mapToScene(self.boundingRect().bottomRight())
            #viewP = view.mapFromScene(sceneP)
            #wpos = view.viewport().mapToGlobal(viewP)

            #wpos = self.pos().toPoint()
            #wrect = self.boundingRect().toRect()
            #wrect.moveBottomLeft(wpos)
            #pixmap = QtGui.QPixmap.grabWidget(event.widget(), wrect)

            #painter = QtGui.QPainter(pixmap)
            #painter.setCompositionMode(painter.CompositionMode_DestinationIn)
            #painter.fillRect(pixmap.rect(), QtGui.QColor(0,0,0,127))
            #painter.end()

            drag = QtGui.QDrag(event.widget())
            drag.setMimeData(mimeData)
            #drag.setPixmap(pixmap)
            #drag.setHotSpot(event.widget().pos())
            drag.exec_(QtCore.Qt.CopyAction)


    def mouseReleaseEvent(self, event):
        if not self.isFile:
            self.scene().change_dir(self.label.text())

class fileList(QtGui.QGraphicsScene):
    def __init__(self, path, widget, parent=None):
        QtGui.QGraphicsScene.__init__(self, parent)
        self.parent = parent
        self.setBackgroundBrush(QtGui.QColor(50, 50, 50))

        self.items = []
        self.prev_dir = None
        self.show_path = widget
        self.change_dir(path)

    def keyPressEvent(self, event):
        QtGui.QGraphicsScene.keyPressEvent(self, event)
        if type(event) == QtGui.QKeyEvent:

            if event.key() == QtCore.Qt.Key_Up: 
                if not self.selectedItems() or 0==self.items.index(self.selectedItems()[0]):
                    self.items[0].setSelected(True)
                else:
                    cursel = self.items.index(self.selectedItems()[0])
                    self.items[cursel].setSelected(False)
                    self.items[cursel-1].setSelected(True)

            elif event.key() == QtCore.Qt.Key_Down: 
                if not self.selectedItems():
                    self.items[0].setSelected(True)
                elif len(self.items)-1==self.items.index(self.selectedItems()[0]):
                    pass
                else:
                    cursel = self.items.index(self.selectedItems()[0])
                    self.items[cursel].setSelected(False)
                    self.items[cursel+1].setSelected(True)

            #TODO ensure_visible prev_dir but it has to be searched by label
            elif event.key() == QtCore.Qt.Key_Left: 
                self.prev_dir = self.cwd
                self.change_dir('..')
            elif event.key() == QtCore.Qt.Key_Right: 
                if not self.selectedItems()[0].isFile:
                    self.prev_dir = self.selectedItems()[0].label.text()
                    self.change_dir(self.selectedItems()[0].label.text())
            elif event.key() == QtCore.Qt.Key_Return:
                if not self.selectedItems()[0].isFile:
                    self.change_dir(self.selectedItems()[0].label.text())
                else:
                    self.selectedItems()[0].playSample()
                    #play(self.selectedItems()[0].label.text())
            elif event.key() == QtCore.Qt.Key_Space:
                if self.selectedItems()[0].isFile:
                    self.selectedItems()[0].playSample()


    def clean(self):
        #self.clear()
        if self.items:
            for item in self.items:
                self.removeItem(item)

    def change_dir(self, path):
        self.clean()
        os.chdir(path)
        self.cwd = path
        self.cwd_folders, self.cwd_files = self.get_contents()
        self.draw_contents()
        self.show_path.setEditText(os.getcwd())

    def draw_contents(self):
        view = self.views()
        c = 0
        self.items = []
        for entry in self.cwd_folders:
            entry_rect = listItem(entry, False)
            entry_rect.setPos(0, line_height+c*line_height)
            self.addItem(entry_rect)
            self.items.append(entry_rect)
            if self.prev_dir:
                if entry==self.prev_dir:
                    view[0].ensureVisible(entry_rect, xMargin=-50)
                    entry_rect.setSelected(True)
            c += 1
        for entry in self.cwd_files:
            entry_rect = listItem(entry, True)
            entry_rect.setPos(0, line_height+c*line_height)
            self.addItem(entry_rect)
            self.items.append(entry_rect)
            c += 1

        if view:
            rect = self.itemsBoundingRect() 
            view[0].setSceneRect(rect)


    def is_audio(self, a_file):
        if os.path.splitext(a_file)[1].lower()[1:] in exts:
            return True
        return False

    def get_contents(self):
        entries = os.listdir(os.getcwd())
        entries = [i for i in entries if not i.startswith('.')]
        dir_list = ['..']
        file_list = []
        for entry in entries:
            if os.path.isdir(entry):
                dir_list.append(entry)
            elif os.path.isfile(entry):
                if self.is_audio(entry):
                    file_list.append(entry)
        dir_list.sort(key=str.lower)
        file_list.sort(key=str.lower)

        return dir_list, file_list

class fileBrowser(QtGui.QGraphicsView):
    '''the file browser'''
    def __init__(self, widget, path=os.path.expanduser("~")):
        QtGui.QGraphicsView.__init__(self)
        self.scene = fileList(path, widget, self)
        self.setScene(self.scene)
        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

class pathLister(QtGui.QComboBox):
    def __init__(self):
       QtGui.QLineEdit.__init__(self)
       self.setEditable(True)
       self.browser = None

    def keyPressEvent(self, event):
        QtGui.QComboBox.keyPressEvent(self, event)
        if event.key() == QtCore.Qt.Key_Return:
            if self.browser:
                print 'lookin up', self.currentText()
                if os.path.isdir(self.currentText()):
                        self.browser.scene.change_dir(self.currentText())

    def setBrowser(self, widget):
        self.browser = widget

class mainWindow(QtGui.QTabWidget):
    def __init__(self):
        QtGui.QTabWidget.__init__(self) 
        #self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents)
        #self.setStyleSheet("background-color: rgb(100,100,100); margin:0px; padding: 0px; border: 1px solid rgb(30,30,30); color: rgb(200,200,200);")
        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setMinimumHeight(1000)

        tab1 = QtGui.QWidget()       
        filePath = pathLister()
        filePath.setFrame(QtGui.QFrame.NoFrame)
        #filePath.setText('/home/duke/audio/sounds')
        files = fileBrowser(filePath, '/home/duke/audio/sounds')
        files.setFrameShape(QtGui.QFrame.NoFrame)

        #files.setPathDisplay(filePath)
        filePath.setBrowser(files)

        vBoxlayout = QtGui.QVBoxLayout()
        vBoxlayout.addWidget(filePath)
        vBoxlayout.addWidget(files)
        tab1.setLayout(vBoxlayout)   

        tab2 = QtGui.QWidget()
        pluginSearch = QtGui.QLineEdit()
        pluginSearch.setText('search...')
        
        
        self.addTab(tab1,"browser")
        self.addTab(tab2,"plugins")
        self.setTabPosition(QtGui.QTabWidget.West)
        self.setTabIcon(0,QtGui.QIcon.fromTheme("edit-undo"))
        self.setIconSize(QtCore.QSize(35,35))
        
        self.setWindowTitle('SAMPLFVKR')
        files.setFocus()

    def keyPressEvent(self, event):
        QtGui.QTabWidget.keyPressEvent(self, event)
        print 'n'
        if event.key() == QtCore.Qt.Key_Tab:
            print 'tab pressed'
    #def touchEvent(self, event):
    #    if event == QtGui.QTouchEvent.TouchScreen:
    #        print 'ok'

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    style_file = '/home/duke/projects/samplefucker/style.qss'
    with open(style_file, 'r') as content_file:
        content = content_file.read()
    stylesheet = QtCore.QLatin1String(content)
    app.setStyleSheet(stylesheet)
   
    tabs = mainWindow()

    tabs.show()
    sys.exit(app.exec_())
    subprocess.call(['pkill','play'])

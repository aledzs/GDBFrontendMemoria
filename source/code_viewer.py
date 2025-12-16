from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QAction
from PyQt5.QtGui import QColor, QPainter, QBrush
from PyQt5.QtCore import QSize, QRect, QPoint, pyqtSignal, pyqtSlot

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

    def mousePressEvent(self, event):
        block = self.code_editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.code_editor.blockBoundingGeometry(block).translated(self.code_editor.contentOffset()).top()
        bottom = top + self.code_editor.blockBoundingRect(block).height()

        while block.isValid() and top <= event.pos().y():
            if block.isVisible() and bottom >= event.pos().y():
                self.code_editor.toggle_breakpoint(block_number)
                break
            block = block.next()
            top = bottom
            bottom = top + self.code_editor.blockBoundingRect(block).height()
            block_number += 1

        self.update()

class CodeViewer(QPlainTextEdit):
    breakpoint_toggle = pyqtSignal(int, bool, str)
    print_var_toggle = pyqtSignal(str)
    watch_var_toggle = pyqtSignal(str)
    def __init__(self, file_path=None):
        super().__init__()
        self._file_path = None
        self.loaded_path = None
        self.setReadOnly(True)

        if file_path:
            self.file_path = file_path

        self.line_number_area = LineNumberArea(self)
        self.breakpoints = set()
        self.current_line = None

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    @property
    def file_path(self):
        return self._file_path
    
    @file_path.setter
    def file_path(self, new_path):
        self._file_path = new_path
        self.load_file()

    def load_file(self):
        with open(self.file_path, 'r') as f:
            self.setPlainText(f.read())
        self.loaded_path = self.file_path
            
    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 8 + self.fontMetrics().horizontalAdvance('9') * digits
        bp_space = 16
        current_line_space = 16
        return space + bp_space + current_line_space

    def update_line_number_area_width(self, _=0):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def toggle_breakpoint(self, block_number):
        line_number = block_number + 1
        if tuple((line_number, self.file_path)) in self.breakpoints:
            self.breakpoints.remove(tuple((line_number, self.file_path)))
            self.breakpoint_toggle.emit(line_number, True, self.file_path)
        else:
            self.breakpoint_toggle.emit(line_number, False, self.file_path)
        self.line_number_area.update()

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        fm = self.fontMetrics()
        bp_radius = 5
        bp_margin = 6

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.save()

                # Breakpoint circle
                if tuple((block_number + 1, self.file_path)) in self.breakpoints:
                    center_x = bp_margin + bp_radius
                    center_y = int(top + fm.height() / 2)
                    painter.setBrush(QBrush(QColor("red")))
                    painter.drawEllipse(QPoint(center_x, center_y), bp_radius, bp_radius)

                # Green arrow for current line
                if self.current_line == block_number + 1 and self.loaded_path == self.file_path:
                    center_x = 2 * bp_margin + 2 * bp_radius + 2
                    center_y = int(top + fm.height() / 2)
                    size = 6
                    triangle = [
                        QPoint(center_x, center_y - size),
                        QPoint(center_x, center_y + size),
                        QPoint(center_x + size, center_y),
                    ]
                    painter.setBrush(QColor("green"))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPolygon(*triangle)

                # Line number text
                number_x = 2 * bp_margin + 2 * bp_radius
                painter.restore()
                painter.drawText(number_x, int(top), self.line_number_area.width() - number_x - 2, fm.height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
            
    def show_context_menu(self, point):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        
        print_var_action = QAction("Print Value", self)
        watch_var_action = QAction("Watch Value", self)
        print_var_action.triggered.connect(self.on_print_var_action_triggered)
        watch_var_action.triggered.connect(self.on_watch_var_action_triggered)
        menu.addAction(print_var_action)
        menu.addAction(watch_var_action)
        menu.exec_(self.mapToGlobal(point))
        
    def on_print_var_action_triggered(self):
        print(self.textCursor().selectedText())
        print("Show var")
        self.print_var_toggle.emit(self.textCursor().selectedText())
        
    def on_watch_var_action_triggered(self):
        print(self.textCursor().selectedText())
        print("Watch var")
        self.watch_var_toggle.emit(self.textCursor().selectedText())
    
    @pyqtSlot(str)
    def set_current_line(self, line_number):
        self.current_line = int(line_number)
        def scroll_to_line():
            block = self.document().findBlockByNumber(self.current_line - 1)
            if block.isValid():
                cursor = self.textCursor()
                cursor.setPosition(block.position())
                self.setTextCursor(cursor)
                self.centerCursor()
                self.ensureCursorVisible()
            self.update()

        QTimer.singleShot(0, scroll_to_line)
        
    @pyqtSlot(str)
    def add_breakpoint(self, line, path):
        self.breakpoints.add(tuple((int(line), path)))
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QObject, QEvent
from PyQt5.QtWidgets import QApplication, QScroller, QScrollerProperties
from PyQt5.QtGui import QTouchEvent


class TouchSupport(QObject):
    tap_detected = pyqtSignal(QPoint)
    long_press_detected = pyqtSignal(QPoint)
    swipe_detected = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._touch_start_pos = None
        self._touch_start_time = None
        self._is_touching = False
        self._long_press_timer = QTimer()
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)
        self._swipe_threshold = 50
        self._long_press_duration = 800
    
    def install_on_widget(self, widget):
        widget.setAttribute(Qt.WA_AcceptTouchEvents, True)
        widget.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        event_type = event.type()
        
        if event_type == QEvent.TouchBegin:
            return self._handle_touch_begin(event)
        elif event_type == QEvent.TouchUpdate:
            return self._handle_touch_update(event)
        elif event_type == QEvent.TouchEnd:
            return self._handle_touch_end(event)
        
        return super().eventFilter(obj, event)
    
    def _handle_touch_begin(self, event):
        touch_points = event.touchPoints()
        if touch_points:
            point = touch_points[0]
            self._touch_start_pos = point.pos().toPoint()
            self._touch_start_time = QTimer().currentTime()
            self._is_touching = True
            self._long_press_timer.start(self._long_press_duration)
        return False
    
    def _handle_touch_update(self, event):
        if not self._is_touching:
            return False
        
        touch_points = event.touchPoints()
        if touch_points and self._touch_start_pos:
            current_pos = touch_points[0].pos().toPoint()
            delta = current_pos - self._touch_start_pos
            
            if abs(delta.x()) > 10 or abs(delta.y()) > 10:
                self._long_press_timer.stop()
        
        return False
    
    def _handle_touch_end(self, event):
        self._long_press_timer.stop()
        
        if not self._is_touching:
            return False
        
        touch_points = event.touchPoints()
        if touch_points and self._touch_start_pos:
            end_pos = touch_points[0].pos().toPoint()
            delta = end_pos - self._touch_start_pos
            
            if abs(delta.x()) < self._swipe_threshold and abs(delta.y()) < self._swipe_threshold:
                self.tap_detected.emit(end_pos)
            else:
                if abs(delta.x()) > abs(delta.y()):
                    if delta.x() > 0:
                        self.swipe_detected.emit("right", delta.x())
                    else:
                        self.swipe_detected.emit("left", -delta.x())
                else:
                    if delta.y() > 0:
                        self.swipe_detected.emit("down", delta.y())
                    else:
                        self.swipe_detected.emit("up", -delta.y())
        
        self._is_touching = False
        self._touch_start_pos = None
        return False
    
    def _on_long_press(self):
        if self._is_touching and self._touch_start_pos:
            self.long_press_detected.emit(self._touch_start_pos)


def enable_kinetic_scroll(widget):
    QScroller.grabGesture(widget, QScroller.LeftMouseButtonGesture)
    
    props = QScroller.scroller(widget).scrollerProperties()
    
    props.setScrollMetric(QScrollerProperties.DragVelocitySmoothingFactor, 0.6)
    props.setScrollMetric(QScrollerProperties.MinimumVelocity, 0.0)
    props.setScrollMetric(QScrollerProperties.MaximumVelocity, 0.5)
    props.setScrollMetric(QScrollerProperties.AcceleratingFlickMaximumTime, 0.4)
    props.setScrollMetric(QScrollerProperties.AcceleratingFlickSpeedupFactor, 1.2)
    props.setScrollMetric(QScrollerProperties.SnapPositionRatio, 0.2)
    props.setScrollMetric(QScrollerProperties.MaximumClickThroughVelocity, 0.0015)
    props.setScrollMetric(QScrollerProperties.DragStartDistance, 0.001)
    props.setScrollMetric(QScrollerProperties.AxisLockThreshold, 0.0)
    
    QScroller.scroller(widget).setScrollerProperties(props)


def apply_touch_friendly_style(app):
    style = """
    QPushButton, QAbstractButton {
        min-height: 40px;
        min-width: 80px;
        padding: 10px;
    }
    
    QComboBox, QSpinBox, QLineEdit {
        min-height: 40px;
        padding: 5px 10px;
    }
    
    QCheckBox, QRadioButton {
        spacing: 15px;
        min-height: 35px;
    }
    
    QScrollBar:vertical {
        width: 20px;
    }
    
    QScrollBar:horizontal {
        height: 20px;
    }
    
    QHeaderView::section {
        min-height: 35px;
        padding: 5px;
    }
    
    QTreeWidget, QTableWidget, QListWidget {
        font-size: 14px;
    }
    
    QMenu {
        font-size: 14px;
        padding: 5px;
    }
    
    QMenu::item {
        padding: 8px 25px;
        min-height: 30px;
    }
    
    QTabBar::tab {
        min-height: 40px;
        min-width: 100px;
        padding: 8px 16px;
    }
    """
    app.setStyleSheet(app.styleSheet() + style)


def enable_touch_support_for_window(window):
    window.setAttribute(Qt.WA_AcceptTouchEvents, True)
    
    from PyQt5.QtWidgets import QScrollArea, QListView, QTreeView, QTableView, QTextEdit, QGraphicsView
    
    scroll_widgets = window.findChildren(QScrollArea)
    for widget in scroll_widgets:
        enable_kinetic_scroll(widget.viewport())
    
    list_views = window.findChildren(QListView)
    for widget in list_views:
        enable_kinetic_scroll(widget.viewport())
    
    tree_views = window.findChildren(QTreeView)
    for widget in tree_views:
        enable_kinetic_scroll(widget.viewport())
    
    table_views = window.findChildren(QTableView)
    for widget in table_views:
        enable_kinetic_scroll(widget.viewport())
    
    text_edits = window.findChildren(QTextEdit)
    for widget in text_edits:
        enable_kinetic_scroll(widget.viewport())
    
    graphics_views = window.findChildren(QGraphicsView)
    for widget in graphics_views:
        enable_kinetic_scroll(widget.viewport())
    
    return TouchSupport(window)

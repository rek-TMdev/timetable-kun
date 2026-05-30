from PySide6.QtWidgets import QApplication, QMessageBox, QWidget, QListWidget, QPushButton, QCheckBox, QComboBox
from PySide6.QtCore import QPoint, QPropertyAnimation, QEasingCurve, QRect, Signal, QObject, Qt, QEvent, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFontMetrics, QCursor, QIcon
import dataclasses
import re
import os
import darkdetect

@dataclasses.dataclass
class TutorialStep:
    message: str
    target_widget_name: str = None
    highlight_target_name: str = None
    action: str = None
    expected_value: any = None
    subject_name: str = None
    year_label: str = None

class TutorialManager(QObject):
    tutorial_finished = Signal()

    def __init__(self, parent_app, ui_elements, base_path=None):
        super().__init__()
        self.parent_app = parent_app
        self.ui_elements = ui_elements
        self.base_path = base_path
        self.steps = []
        self.current_step_index = -1
        self.overlay = None
        self.highlight_animation = None
        self.msg_box = None
        self.enable_check_timer = None
        self.last_action_args = None
        self.is_advancing = False # State-lock flag

    def set_steps(self, steps):
        self.steps = steps

    def start_tutorial(self):
        self.current_step_index = -1
        self.is_advancing = False
        self.next_step()

    def next_step(self):
        if self.is_advancing:
            return
        self.is_advancing = True

        self.cleanup_step()
        self.current_step_index += 1
        if self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
            self.show_tutorial_message(step)
        else:
            self.end_tutorial()

    def show_tutorial_message(self, step):
        if not step.message:
            # This is a sync step, don't show a message.
            target_for_action = self.get_target_widget(step)
            if target_for_action:
                self.connect_action(target_for_action, step)
            else:
                self.next_step() # Failsafe
            QTimer.singleShot(0, lambda: setattr(self, 'is_advancing', False))
            return
        
        message = step.message
        if self.last_action_args and isinstance(message, str) and re.search(r'\{[0-9]*\}', message):
            try:
                message = message.format(*self.last_action_args)
            except (IndexError, TypeError) as e:
                print(f"Warning: Failed to format tutorial message: '{message}' with args {self.last_action_args}. Error: {e}")
        self.last_action_args = None

        parent_window = QApplication.activeWindow() or self.parent_app

        if step.action == "last_step":
            self.msg_box = QMessageBox()
        else:
            self.msg_box = QMessageBox(parent_window)
        self.msg_box.setWindowTitle("チュートリアル")
        self.msg_box.setText(message)

        if self.base_path:
            icon_path = os.path.join(self.base_path, "時間割くんアイコン.ico")
            if os.path.exists(icon_path):
                self.msg_box.setWindowIcon(QIcon(icon_path))

        # Dynamic Style Calculation
        is_dark = darkdetect.isDark()
        if is_dark:
            current_style = "QMessageBox { border: 2px solid white; border-radius: 5px; background-color: #333; color: white; }"
        else:
            current_style = "QMessageBox { border: 2px solid black; border-radius: 5px; background-color: #f9f9f9; color: black; }"

        if not step.action:
            buttons = QMessageBox.Ok
            self.msg_box.setModal(True)
        elif step.action == "last_step":
            buttons = QMessageBox.Ok
            self.msg_box.setModal(True)
        elif step.action == "info_next_button":
            buttons = QMessageBox.Ok
            self.msg_box.setWindowModality(Qt.NonModal)
            self.msg_box.setWindowFlags(self.msg_box.windowFlags() | Qt.FramelessWindowHint)
            self.msg_box.setStyleSheet(current_style)
        else:
            buttons = QMessageBox.NoButton
            self.msg_box.setWindowModality(Qt.NonModal)
            self.msg_box.setWindowFlags(self.msg_box.windowFlags() | Qt.FramelessWindowHint)
            self.msg_box.setStyleSheet(current_style)

        self.msg_box.setStandardButtons(buttons)

        ok_button = self.msg_box.button(QMessageBox.Ok)
        if ok_button:
            if step.action == "last_step":
                ok_button.setText("OK")
            else:
                ok_button.setText("次へ")
        
        cancel_button = self.msg_box.button(QMessageBox.Cancel)
        if cancel_button:
            cancel_button.setText("チュートリアルを終了")

        self.msg_box.finished.connect(self.on_msg_box_closed)
        
        if step.target_widget_name:
            action_target = self.get_target_widget(step)
            if action_target or step.action == 'wait_for_enable':
                self.connect_action(action_target, step)
            else:
                print(f"Warning: Target widget '{step.target_widget_name}' not found for action.")

        highlight_name = step.highlight_target_name or step.target_widget_name
        if highlight_name:
            temp_step = dataclasses.replace(step, target_widget_name=highlight_name)
            highlight_target = self.get_target_widget(temp_step)
            item_rect = None
            if isinstance(highlight_target, QListWidget) and step.expected_value is not None and 0 <= step.expected_value < highlight_target.count():
                item = highlight_target.item(step.expected_value)
                if item:
                    item_rect = highlight_target.visualItemRect(item)
                    if item_rect.isValid():
                        fm = QFontMetrics(highlight_target.font())
                        text_width = fm.horizontalAdvance(item.text())
                        item_rect.setWidth(text_width + 20)
                        item_rect.moveLeft(highlight_target.visualItemRect(item).left() + 5)
            if highlight_name == "setting_window" and hasattr(highlight_target, 'findChildren'):
                buttons = highlight_target.findChildren(QPushButton)
                for button in buttons:
                    if button.text() == "閉じる":
                        highlight_target = button
                        break
            if isinstance(highlight_target, QWidget):
                self.highlight_widget(highlight_target, step, item_rect)
            elif highlight_target:
                print(f"Warning: Highlight target '{highlight_name}' is not a QWidget.")
            else:
                print(f"Warning: Highlight target '{highlight_name}' not found.")

        self.msg_box.setWindowFlags(self.msg_box.windowFlags() | Qt.WindowStaysOnTopHint)

        try:
            self.msg_box.adjustSize()
            msg_box_size = self.msg_box.size()
            anchor_window = QApplication.activeWindow() or self.parent_app
            screen = anchor_window.screen()
            if not screen: screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            anchor_rect = anchor_window.geometry()
            margin = 15

            if not screen_rect.intersects(anchor_rect):
                center_point = screen_rect.center()
                top_left = QPoint(center_point.x() - msg_box_size.width() / 2, center_point.y() - msg_box_size.height() / 2)
                self.msg_box.move(top_left)
            else:
                pos1_point = QPoint(anchor_rect.right() + margin, anchor_rect.top() + (anchor_rect.height() - msg_box_size.height()) / 2)
                pos1_rect = QRect(pos1_point, msg_box_size)
                pos2_point = QPoint(anchor_rect.left() - msg_box_size.width() - margin, anchor_rect.top() + (anchor_rect.height() - msg_box_size.height()) / 2)
                pos2_rect = QRect(pos2_point, msg_box_size)

                if screen_rect.contains(pos1_rect):
                    self.msg_box.move(pos1_point)
                elif screen_rect.contains(pos2_rect):
                    self.msg_box.move(pos2_point)
                else:
                    pos3_point = QPoint(anchor_rect.right() - msg_box_size.width() - margin, anchor_rect.bottom() - msg_box_size.height() - margin)
                    self.msg_box.move(pos3_point)
        except Exception as e:
            print(f"Error positioning tutorial message box: {e}")

        QTimer.singleShot(10, self.msg_box.show)
        QTimer.singleShot(0, lambda: setattr(self, 'is_advancing', False))

    def get_target_widget(self, step):
        if not step.target_widget_name: return None
        target_getter = self.ui_elements.get(step.target_widget_name)
        if isinstance(target_getter, Signal): return target_getter
        if callable(target_getter):
            if step.target_widget_name in ("get_subject_cb", "get_important_cb"):
                return target_getter(step.subject_name, step.year_label)
            elif step.target_widget_name == "get_timetable_slot_by_subject":
                return target_getter(step.subject_name)
            elif step.target_widget_name in ("get_submit_btn", "get_filter_button"):
                return target_getter(step.year_label)
            else:
                return target_getter()
        return target_getter

    def connect_action(self, widget, step):
        if not step.action: return
        try:
            if step.action == "click":
                if isinstance(widget, QPushButton): widget.clicked.connect(self.on_action_completed)
                elif isinstance(widget, QListWidget): widget.itemClicked.connect(self.on_action_completed)
            elif step.action == "tab_change":
                if isinstance(widget, QListWidget): widget.currentRowChanged.connect(self.on_action_completed)
            elif step.action == "check":
                if isinstance(widget, QCheckBox): widget.toggled.connect(self.on_action_completed)
            elif step.action == "selection_change":
                if isinstance(widget, QComboBox): widget.currentIndexChanged.connect(self.on_action_completed)
            elif step.action == "custom_signal":
                if isinstance(widget, Signal):
                    widget.connect(self.on_action_completed)
                elif isinstance(widget, QWidget) and hasattr(widget, 'clicked'):
                    widget.clicked.connect(self.on_action_completed)
                else:
                    print(f"Warning: Don't know how to connect 'custom_signal' for widget {widget}")
            elif step.action == "window_close":
                if isinstance(widget, QWidget): widget.installEventFilter(self)
            elif step.action == "wait_for_enable":
                self.enable_check_timer = QTimer(self)
                self.enable_check_timer.timeout.connect(lambda: self.check_if_enabled(step))
                self.enable_check_timer.start(100)
        except Exception as e:
            print(f"Error connecting signal for {step.target_widget_name}: {e}")

    def check_if_enabled(self, step):
        actual_widget = self.get_target_widget(step)
        if actual_widget and actual_widget.isEnabled():
            if self.enable_check_timer:
                self.enable_check_timer.stop()
                self.enable_check_timer.deleteLater()
                self.enable_check_timer = None
            QTimer.singleShot(0, self.on_action_completed)

    def on_action_completed(self, *args):
        self.last_action_args = args
        if self.current_step_index < 0 or self.current_step_index >= len(self.steps): return

        step = self.steps[self.current_step_index]

        if step.action == "custom_signal" and step.expected_value:
            if step.expected_value == {'action': 'subject_added'}:
                pass
            else:
                if not args or not isinstance(args[0], dict):
                    return
                match = True
                for key, value in step.expected_value.items():
                    if key not in args[0] or args[0][key] != value:
                        match = False
                        break
                if not match:
                    return

        target_widget = self.get_target_widget(step)
        
        if not target_widget and step.action != "wait_for_enable": return
        if step.action == "tab_change":
            if args[0] != step.expected_value: return
        elif step.action == "check":
            if not args[0]: return
        elif step.action == "selection_change":
            if args and args[0] == 0: return

        self.disconnect_action(target_widget, step)
        
        if step.action in ["click", "custom_signal"]:
            QTimer.singleShot(100, self.next_step)
        else:
            self.next_step()

    def disconnect_action(self, widget, step):
        if not step.action: return
        try:
            if step.action == "click":
                if isinstance(widget, QPushButton): widget.clicked.disconnect(self.on_action_completed)
                elif isinstance(widget, QListWidget): widget.itemClicked.disconnect(self.on_action_completed)
            elif step.action == "tab_change":
                if isinstance(widget, QListWidget): widget.currentRowChanged.disconnect(self.on_action_completed)
            elif step.action == "check":
                if isinstance(widget, QCheckBox): widget.toggled.disconnect(self.on_action_completed)
            elif step.action == "selection_change":
                if isinstance(widget, QComboBox): widget.currentIndexChanged.disconnect(self.on_action_completed)
            elif step.action == "custom_signal":
                if isinstance(widget, Signal):
                    widget.disconnect(self.on_action_completed)
                elif isinstance(widget, QWidget) and hasattr(widget, 'clicked'):
                     widget.clicked.disconnect(self.on_action_completed)
            elif step.action == "window_close":
                if isinstance(widget, QWidget): widget.removeEventFilter(self)
            elif step.action == "wait_for_enable":
                if self.enable_check_timer:
                    self.enable_check_timer.stop()
                    self.enable_check_timer.deleteLater()
                    self.enable_check_timer = None
        except (TypeError, RuntimeError):
            pass

    def on_msg_box_closed(self, result):
        if not self.msg_box: return
        if self.current_step_index < 0 or self.current_step_index >= len(self.steps):
            return
        step = self.steps[self.current_step_index]
        
        if result == QMessageBox.Ok:
            if not step.action or step.action == "info_next_button":
                self.next_step()
            elif step.action == "last_step":
                self.end_tutorial()
            else:
                pass
        elif result == QMessageBox.Cancel:
            self.end_tutorial()

    def highlight_widget(self, widget, step, item_rect=None):
        if self.overlay:
            try:
                self.overlay.deleteLater()
            except RuntimeError: pass
            self.overlay = None
        if widget and isinstance(widget, QWidget):
            self.overlay = HighlightOverlay(widget, item_rect)
            self.overlay.show()

    def cleanup_step(self):
        if self.msg_box:
            try:
                self.msg_box.deleteLater()
            except RuntimeError: pass
            self.msg_box = None
        if self.overlay:
            try:
                self.overlay.deleteLater()
            except RuntimeError: pass
            self.overlay = None
        if self.highlight_animation:
            try:
                self.highlight_animation.stop()
            except RuntimeError: pass
            self.highlight_animation = None
        
        if self.current_step_index != -1 and self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
            target_widget = self.get_target_widget(step)
            if target_widget or step.action == 'wait_for_enable':
                self.disconnect_action(target_widget, step)

    def end_tutorial(self):
        self.cleanup_step()
        self.tutorial_finished.emit()
        self.is_advancing = False

    def get_current_step(self):
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def eventFilter(self, watched, event):
        if self.current_step_index < 0 or self.current_step_index >= len(self.steps): return False
        step = self.steps[self.current_step_index]
        if step.action == "window_close" and watched == self.get_target_widget(step) and event.type() == QEvent.Close:
            self.on_action_completed()
            return True
        return False

class HighlightOverlay(QWidget):
    def __init__(self, target_widget, item_rect=None):
        super().__init__()
        self.target_widget = target_widget
        self.item_rect = item_rect
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        QTimer.singleShot(0, self.update_geometry)

        try:
            if self.target_widget and self.target_widget.window():
                self.target_widget.window().installEventFilter(self)
            else:
                self.deleteLater()
        except RuntimeError:
            self.deleteLater()

    def update_geometry(self):
        try:
            if not self.target_widget or not self.target_widget.window():
                self.deleteLater()
                return
            if self.item_rect and self.item_rect.isValid():
                global_pos = self.target_widget.mapToGlobal(self.item_rect.topLeft())
                self.setGeometry(global_pos.x(), global_pos.y(), self.item_rect.width(), self.item_rect.height())
            else:
                global_pos = self.target_widget.mapToGlobal(self.target_widget.rect().topLeft())
                self.setGeometry(global_pos.x(), global_pos.y(), self.target_widget.width(), self.target_widget.height())
            self.raise_()
        except RuntimeError:
            self.deleteLater()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 255, 0, 200)); pen.setWidth(5)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(-2, -2, 2, 2), 5, 5)

    def eventFilter(self, obj, event):
        try:
            if self.target_widget and obj == self.target_widget.window() and (event.type() == QEvent.Move or event.type() == QEvent.Resize):
                self.update_geometry()
        except RuntimeError:
            self.deleteLater()
        return super().eventFilter(obj, event)
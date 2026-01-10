import re
import functools
import threading
from PyQt6.QtCore import Qt, QObject, QThread, QMetaObject, QCoreApplication, pyqtSlot, pyqtSignal, QEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QRadioButton, QButtonGroup, QVBoxLayout, QCheckBox, QScrollArea, QLabel, QApplication
from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel, LineEdit, PushButton, ProgressBar

from Scripts.datasets import os_data

_default_gui_handler = None

def set_default_gui_handler(handler):
    global _default_gui_handler
    _default_gui_handler = handler

class MainThreadRunner(QObject):
    """用于在主线程执行函数的辅助类"""
    run_signal = pyqtSignal(object, object, object)
    
    def __init__(self):
        super().__init__()
        self.moveToThread(QApplication.instance().thread())
        self.run_signal.connect(self._on_run)
        
    @pyqtSlot(object, object, object)
    def _on_run(self, func, args, kwargs):
        try:
            result = func(*args, **kwargs)
            # 这里我们无法直接返回结果给调用者，因为这是异步信号
            # 但对于 ensure_main_thread 的 BlockingQueuedConnection 需求，
            # 我们需要一种同步机制。
            # 下面的 ThreadRunner 实现更适合同步调用。
            pass 
        except Exception:
            pass

# 重新实现 ThreadRunner 以支持跨线程同步调用并返回结果
class ThreadRunner(QObject):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.exception = None

    @pyqtSlot()
    def run(self):
        try:
            self.result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.exception = e

def ensure_main_thread(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 检查当前是否为主线程
        if QThread.currentThread() == QCoreApplication.instance().thread():
            return func(*args, **kwargs)
        
        # 如果不是主线程，使用 invokeMethod 将调用调度到主线程
        runner = ThreadRunner(func, *args, **kwargs)
        runner.moveToThread(QCoreApplication.instance().thread())
        
        # 关键修复：确保传递的是字符串 "run"
        # 这种方式在 PyQt6 中通常是有效的，只要 runner 是 QObject 且 run 是 pyqtSlot
        # 报错 'argument 2 has unexpected type function' 说明之前可能传了函数对象
        # 这里的代码看起来是 "run" 字符串，是正确的。
        # 可能是之前代码版本的问题，或者是 PyQt6 版本的怪癖。
        # 无论如何，这个版本保持 "run" 字符串。
        
        ret = QMetaObject.invokeMethod(
            runner, 
            "run", 
            Qt.ConnectionType.BlockingQueuedConnection
        )
        
        if not ret:
            # 只有在方法调用失败时（如找不到 slot）才会返回 False
            # 但 invokeMethod 在 BlockingQueuedConnection 下如果是 void 返回值通常返回 True
            # 如果 runner.run 抛出异常，这里捕获不到，必须通过 runner.exception
            pass

        if runner.exception:
            raise runner.exception
        return runner.result
    return wrapper

class CustomMessageDialog(MessageBoxBase):
    def __init__(self, title, content):
        super().__init__(_default_gui_handler)
        
        self.titleLabel = SubtitleLabel(title, self.widget)
        self.contentLabel = BodyLabel(content, self.widget)
        self.contentLabel.setWordWrap(True)
        
        is_html = bool(re.search(r"<[^>]+>", content))
        
        if is_html:
            self.contentLabel.setTextFormat(Qt.TextFormat.RichText)
            self.contentLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            self.contentLabel.setOpenExternalLinks(True)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentLabel)
        
        self.widget.setMinimumWidth(600)
        
        self.custom_widget = None
        self.input_field = None
        self.button_group = None
        
    def add_input(self, placeholder: str = "", default_value: str = ""):
        self.input_field = LineEdit(self.widget)
        if placeholder:
            self.input_field.setPlaceholderText(placeholder)
        if default_value:
            self.input_field.setText(str(default_value))
        
        self.viewLayout.addWidget(self.input_field)
        self.input_field.setFocus()
        return self.input_field

    def add_custom_widget(self, widget: QWidget):
        self.custom_widget = widget
        self.viewLayout.addWidget(widget)

    def add_radio_options(self, options, default_index=0):
        self.button_group = QButtonGroup(self)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        
        for i, option_text in enumerate(options):
            is_html = bool(re.search(r"<[^>]+>", option_text))
            
            if is_html:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)
                
                radio = QRadioButton()
                label = BodyLabel(option_text)
                label.setTextFormat(Qt.TextFormat.RichText)
                label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                label.setOpenExternalLinks(True)
                label.setWordWrap(True)
                
                row_layout.addWidget(radio)
                row_layout.addWidget(label, 1)
                
                layout.addWidget(row_widget)
            else:
                radio = QRadioButton(option_text)
                layout.addWidget(radio)
            
            self.button_group.addButton(radio, i)
            
            if i == default_index:
                radio.setChecked(True)
                
        self.viewLayout.addWidget(container)
        return self.button_group
    
    def add_checklist(self, items, checked_indices=None):
        if checked_indices is None:
            checked_indices = []
            
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(400)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        checkboxes = []
        current_category = None
        
        for i, item in enumerate(items):
            label_text = item
            category = None
            supported = True
            
            if isinstance(item, dict):
                label_text = item.get("label", "")
                category = item.get("category")
                supported = item.get("supported", True)
            
            if category and category != current_category:
                current_category = category
                
                if i > 0:
                    layout.addSpacing(10)
                    
                header = QLabel("类别: {}".format(category))
                header.setStyleSheet("font-weight: bold; color: #0078D4; padding-top: 5px; padding-bottom: 5px; border-bottom: 1px solid #E1DFDD;")
                layout.addWidget(header)
                
            cb = QCheckBox(label_text)
            if i in checked_indices:
                cb.setChecked(True)
                
            if not supported:
                cb.setStyleSheet("color: #A19F9D;")
                
            layout.addWidget(cb)
            checkboxes.append(cb)
            
        layout.addStretch()
        scroll.setWidget(container)
        self.viewLayout.addWidget(scroll)
        return checkboxes

    def configure_buttons(self, yes_text: str = "确定", no_text: str = "取消", show_cancel: bool = True):
        self.yesButton.setText(yes_text)
        self.cancelButton.setText(no_text)
        self.cancelButton.setVisible(show_cancel)

@ensure_main_thread
def show_info(title: str, content: str) -> None:
    dialog = CustomMessageDialog(title, content)
    dialog.configure_buttons(yes_text="确定", show_cancel=False)
    dialog.exec()

@ensure_main_thread
def show_confirmation(title: str, content: str, yes_text="是", no_text="否") -> bool:
    dialog = CustomMessageDialog(title, content)
    dialog.configure_buttons(yes_text=yes_text, no_text=no_text, show_cancel=True)
    return dialog.exec()

@ensure_main_thread
def show_options_dialog(title, content, options, default_index=0):
    dialog = CustomMessageDialog(title, content)
    dialog.add_radio_options(options, default_index)
    dialog.configure_buttons(yes_text="确定", show_cancel=True)
    
    if dialog.exec():
        return dialog.button_group.checkedId()
    return None

@ensure_main_thread
def show_checklist_dialog(title, content, items, checked_indices=None):
    dialog = CustomMessageDialog(title, content)
    checkboxes = dialog.add_checklist(items, checked_indices)
    dialog.configure_buttons(yes_text="确定", show_cancel=True)
    
    if dialog.exec():
        return [i for i, cb in enumerate(checkboxes) if cb.isChecked()]
    return None

@ensure_main_thread
def ask_network_count(total_networks):
    content = (
        "在此设备上发现了 {} 个 WiFi 网络。<br><br>"
        "您想处理多少个网络？<br>"
        "<ul>"
        "<li>输入数字 (1-{})</li>"
        "<li>或选择“处理所有网络”</li>"
        "</ul>"
    ).format(total_networks, total_networks)
    
    dialog = CustomMessageDialog("WiFi 网络检索", content)
    dialog.input_field = dialog.add_input(placeholder="1-{} (默认: 5)".format(total_networks), default_value="5")
    
    button_layout = QHBoxLayout()
    all_btn = PushButton("处理所有网络", dialog.widget)
    button_layout.addWidget(all_btn)
    button_layout.addStretch()
    dialog.viewLayout.addLayout(button_layout)
    
    result = {"value": 5}
    
    def on_all_clicked():
        result["value"] = "a"
        dialog.accept()
        
    all_btn.clicked.connect(on_all_clicked)
    
    def on_accept():
        if result["value"] == "a":
            return
        
        text = dialog.input_field.text().strip()
        if not text:
            result["value"] = 5
        elif text.lower() == "a":
            result["value"] = "a"
        else:
            try:
                val = int(text)
                result["value"] = min(max(1, val), total_networks)
            except ValueError:
                result["value"] = 5
    
    original_accept = dialog.accept
    def custom_accept():
        on_accept()
        original_accept()
        
    dialog.accept = custom_accept
    
    if dialog.exec():
        return result["value"]

    return 5

def show_smbios_selection_dialog(title, content, items, current_selection, default_selection):
    dialog = CustomMessageDialog(title, content)
    
    top_container = QWidget()
    top_layout = QHBoxLayout(top_container)
    top_layout.setContentsMargins(0, 0, 0, 0)
    
    show_all_cb = QCheckBox("显示所有型号")
    restore_btn = PushButton("恢复默认 ({})".format(default_selection))
    
    top_layout.addWidget(show_all_cb)
    top_layout.addStretch()
    top_layout.addWidget(restore_btn)
    
    dialog.viewLayout.addWidget(top_container)
    
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFixedHeight(400)
    
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setSpacing(5)
    
    button_group = QButtonGroup(dialog)
    
    item_widgets = []
    current_category = None
    
    for i, item in enumerate(items):
        category = item.get("category")
        category_label = None
        if category != current_category:
            current_category = category
            category_label = QLabel("类别: {}".format(category))
            category_label.setStyleSheet("font-weight: bold; color: #0078D4; margin-top: 10px; border-bottom: 1px solid #E1DFDD;")
            layout.addWidget(category_label)
            
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(20, 0, 0, 0) 
        
        radio = QRadioButton(item.get("label"))
        if not item.get("is_supported"):
            radio.setStyleSheet("color: #A19F9D;")
            
        row_layout.addWidget(radio)
        layout.addWidget(row_widget)
        
        button_group.addButton(radio, i)
        
        if item.get("name") == current_selection:
            radio.setChecked(True)
            
        widget_data = {
            "row": row_widget,
            "category_label": category_label,
            "item": item,
            "radio": radio
        }
        item_widgets.append(widget_data)
    layout.addStretch()
    scroll.setWidget(container)
    dialog.viewLayout.addWidget(scroll)
    
    def update_visibility():
        show_all = show_all_cb.isChecked()
        visible_categories = set()
        
        for w in item_widgets:
            item = w["item"]
            is_current_or_default = item.get("name") in (current_selection, default_selection)
            is_compatible = item.get("is_compatible")
            
            should_show = is_current_or_default or show_all or is_compatible
            
            w["row"].setVisible(should_show)
            if should_show:
                visible_categories.add(item.get("category"))
                
        for w in item_widgets:
            if w["category_label"]:
                w["category_label"].setVisible(w["item"].get("category") in visible_categories)

    show_all_cb.stateChanged.connect(update_visibility)
    
    def restore_default():
        for i, item in enumerate(items):
            if item.get("name") == default_selection:
                button_group.button(i).setChecked(True)
                break
    
    restore_btn.clicked.connect(restore_default)
    
    update_visibility()
    
    dialog.configure_buttons(yes_text="确定", show_cancel=True)
    
    if dialog.exec():
        selected_id = button_group.checkedId()
        if selected_id >= 0:
            return items[selected_id].get("name")
            
    return None

def show_macos_version_dialog(native_macos_version, ocl_patched_macos_version, suggested_macos_version):
    content = ""
    
    if native_macos_version[1][:2] != suggested_macos_version[:2]:
        suggested_macos_name = os_data.get_macos_name_by_darwin(suggested_macos_version)
        content += "<b style=\"color: #1565C0\">建议的 macOS 版本：</b> 为了更好的兼容性和稳定性，建议您仅使用 <b>{}</b> 或更旧版本。<br><br>".format(suggested_macos_name)

    content += "请选择您想要使用的 macOS 版本："
    
    options = []
    version_values = []
    default_index = None
    
    native_min = int(native_macos_version[0][:2])
    native_max = int(native_macos_version[-1][:2])
    oclp_min = int(ocl_patched_macos_version[-1][:2]) if ocl_patched_macos_version else 99
    oclp_max = int(ocl_patched_macos_version[0][:2]) if ocl_patched_macos_version else 0
    min_version = min(native_min, oclp_min)
    max_version = max(native_max, oclp_max)

    for darwin_version in range(min_version, max_version + 1):
        if not (native_min <= darwin_version <= native_max or oclp_min <= darwin_version <= oclp_max):
            continue

        name = os_data.get_macos_name_by_darwin(str(darwin_version))
        
        label = ""
        if oclp_min <= darwin_version <= oclp_max:
            label = " <i style=\"color: #FF8C00\">(需要 OCLP 补丁)</i>"
        
        options.append("<span>{}{}</span>".format(name, label))
        version_values.append(darwin_version)
        
        if darwin_version == int(suggested_macos_version[:2]):
            default_index = len(options) - 1
    
    result = show_options_dialog("选择 macOS 版本", content, options, default_index)
    
    if result is not None:
        return "{}.99.99".format(version_values[result])

    return None

class UpdateDialog(MessageBoxBase):
    progress_updated = pyqtSignal(int, str)
    
    def __init__(self, title="更新", initial_status="正在检查更新..."):
        super().__init__(_default_gui_handler)
        
        self.titleLabel = SubtitleLabel(title, self.widget)
        self.statusLabel = BodyLabel(initial_status, self.widget)
        self.statusLabel.setWordWrap(True)
        
        self.progressBar = ProgressBar(self.widget)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.statusLabel)
        self.viewLayout.addWidget(self.progressBar)
        
        self.widget.setMinimumWidth(600)
        
        self.cancelButton.setVisible(False)
        self.yesButton.setVisible(False)
        
        self.progress_updated.connect(self._update_progress_safe)
    
    @pyqtSlot(int, str)
    def _update_progress_safe(self, value, status_text):
        self.progressBar.setValue(value)
        if status_text:
            self.statusLabel.setText(status_text)
        QCoreApplication.processEvents()
    
    def update_progress(self, value, status_text=""):
        self.progress_updated.emit(value, status_text)
    
    def set_status(self, status_text):
        self.update_progress(self.progressBar.value(), status_text)
    
    def show_buttons(self, show_ok=False, show_cancel=False):
        self.yesButton.setVisible(show_ok)
        self.cancelButton.setVisible(show_cancel)
    
    def configure_buttons(self, ok_text="确定", cancel_text="取消"):
        self.yesButton.setText(ok_text)
        self.cancelButton.setText(cancel_text)

def show_update_dialog(title="更新", initial_status="正在检查更新..."):
    dialog = UpdateDialog(title, initial_status)
    return dialog
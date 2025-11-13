import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QLabel, QToolBar, QPlainTextEdit, QLineEdit, QListWidget, QListView
from pygdbmi.gdbcontroller import GdbController
from source.code_viewer import CodeViewer

class MainWindow(QWidget):
    def __init__(self, program_path):
        super().__init__()
        self.setWindowTitle("GDB GUI")
        self.resize(1280, 720)
        
        self.program_path = program_path
        self.source_path = ""
        
        self.sources = []
        self.sources2 = {}
        
        self.gdb = GdbController()
        
        self.start = self.gdb.write(f"-file-exec-and-symbols {program_path}")
        
        # Toolbar section
        toolbar = QToolBar("Toolbar")
        toolbar.setMovable(False)
        
        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self.run_program)
        toolbar.addWidget(run_btn)

        next_btn = QPushButton("Next")
        next_btn.clicked.connect(self.next_line)
        toolbar.addWidget(next_btn)

        step_btn = QPushButton("Step In")
        step_btn.clicked.connect(self.step_in)
        toolbar.addWidget(step_btn)

        continue_btn = QPushButton("Continue")
        continue_btn.clicked.connect(self.on_continue)
        toolbar.addWidget(continue_btn)

        finish_btn = QPushButton("Finish")
        finish_btn.clicked.connect(self.on_finish_click)
        toolbar.addWidget(finish_btn)
        
        until_btn = QPushButton("Until")
        until_btn.clicked.connect(self.on_until_click)
        toolbar.addWidget(until_btn)

        left_vertical_splitter = QSplitter(Qt.Orientation.Vertical)

        # File explorer
        file_browser_layout = QVBoxLayout()
        file_browser_layout.addWidget(QLabel("<b>Files</b>"))
        self.file_browser = QListWidget()
        self.file_browser.itemClicked.connect(self.file_browser_item_clicked)
        file_browser_layout.addWidget(self.file_browser)
        file_browser_widget = QWidget()
        file_browser_widget.setLayout(file_browser_layout)
        left_vertical_splitter.addWidget(file_browser_widget)
        
        # Backtrace
        backtrace_layout = QVBoxLayout()
        backtrace_layout.addWidget(QLabel("<b>Backtrace</b>"))
        self.backtrace_window = QListWidget()
        self.backtrace_window.itemClicked.connect(self.backtrace_window_on_item_click)
        backtrace_layout.addWidget(self.backtrace_window)
        backtrace_widget = QWidget()
        backtrace_widget.setLayout(backtrace_layout)
        left_vertical_splitter.addWidget(backtrace_widget)
        
        middle_vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Code viewer
        code_viewer_layout = QVBoxLayout()
        code_viewer_layout.addWidget(QLabel("<b>Source code</b>"))
        self.get_source_file()
        self.code_viewer = CodeViewer(self.source_path)
        self.code_viewer.breakpoint_toggle.connect(self.on_breakpoint_toggle)
        self.code_viewer.print_var_toggle.connect(self.get_variable_value)
        self.code_viewer.watch_var_toggle.connect(self.add_var_to_watchlist)
        code_viewer_layout.addWidget(self.code_viewer)
        code_viewer_widget = QWidget()
        code_viewer_widget.setLayout(code_viewer_layout)
        middle_vertical_splitter.addWidget(code_viewer_widget)
        
        # Local variables
        local_variables_layout = QVBoxLayout()
        local_variables_layout.addWidget(QLabel("<b>Variables</b>"))
        self.local_variables = QListWidget()
        local_variables_layout.addWidget(self.local_variables)
        local_variables_widget = QWidget()
        local_variables_widget.setLayout(local_variables_layout)
        middle_vertical_splitter.addWidget(local_variables_widget)
        
        self.watched_variables = []
        
        right_vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Console
        console_layout = QVBoxLayout()
        console_layout.addWidget(QLabel("<b>Program Output</b>"))
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        console_layout.addWidget(self.console_output)
        console_widget = QWidget()
        console_widget.setLayout(console_layout)
        right_vertical_splitter.addWidget(console_widget)

        # GDB Console
        debug_layout = QVBoxLayout()
        debug_layout.addWidget(QLabel("<b>GDB Debug Output</b>"))
        self.debug_output = QPlainTextEdit()
        self.debug_output.setReadOnly(True)
        debug_layout.addWidget(self.debug_output)
        # GDB Console Command Line
        self.command_line = QLineEdit()
        debug_layout.addWidget(self.command_line)
        self.command_line.returnPressed.connect(self.send_command)

        debug_widget = QWidget()
        debug_widget.setLayout(debug_layout)
        right_vertical_splitter.addWidget(debug_widget)

        # === Main Horizontal Splitter ===
        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(left_vertical_splitter)
        horizontal_splitter.addWidget(middle_vertical_splitter)
        horizontal_splitter.addWidget(right_vertical_splitter)
        horizontal_splitter.setSizes([200, 540, 540])

        main_layout = QVBoxLayout()
        main_layout.addWidget(toolbar)
        main_layout.addWidget(horizontal_splitter)
        self.setLayout(main_layout)
        
        self.print_message_console(self.start)
        self.get_source_files()

    # Toolbar button functions
    def run_program(self):
        result = self.gdb.write("-exec-run")
        message = result[-1]
        frame = message.get("payload", {}).get("frame", {})
        if frame and "line" in frame:
            # print(frame["line"])
            self.code_viewer.set_current_line(frame["line"])
            
        if frame and "fullname" in frame:
            self.code_viewer.file_path = frame["fullname"]
            self.code_viewer.loaded_path = frame["fullname"]
        
        self.print_message_console(result)
        self.print_watched_variables()
        self.backtrace_refresh()
        self.get_local_variables()

    def next_line(self):
        result = self.gdb.write("-exec-next")
        message = result[-1]
        frame = message.get("payload", {}).get("frame", {})
        
        if frame and "line" in frame:
            # print(frame["line"])
            self.code_viewer.set_current_line(frame["line"])
            
        if frame and "fullname" in frame:
            self.code_viewer.file_path = frame["fullname"]
            self.code_viewer.loaded_path = frame["fullname"]
            # print(frame["fullname"])
            # print(self.source_path)
            # print(self.code_viewer.file_path)
            
        self.print_message_console(result)
        self.print_watched_variables()
        self.backtrace_refresh()
        self.get_local_variables()

    def step_in(self):
        result = self.gdb.write("-exec-step")
        message = result[-1]
        frame = message.get("payload", {}).get("frame", {})
        
        if frame and "line" in frame:
            # print(frame["line"])
            self.code_viewer.set_current_line(frame["line"])
            
        if frame and "fullname" in frame:
            self.code_viewer.file_path = frame["fullname"]
            self.code_viewer.loaded_path = frame["fullname"]
            # print(frame["fullname"])
            # print(self.source_path)
            # print(self.code_viewer.file_path)
            
        self.print_message_console(result)
        self.print_watched_variables()
        self.backtrace_refresh()
        self.get_local_variables()

    def on_continue(self):
        result = self.gdb.write("-exec-continue")
        message = result[-1]
        frame = message.get("payload", {}).get("frame", {})
        
        if frame and "line" in frame:
            self.code_viewer.set_current_line(frame["line"])
            
        if frame and "fullname" in frame:
            self.code_viewer.file_path = frame["fullname"]
            self.code_viewer.loaded_path = frame["fullname"]
            
        self.print_message_console(result)
        self.print_watched_variables()
        self.backtrace_refresh()
        self.get_local_variables()
        
    def on_finish_click(self):
        result = self.gdb.write("-exec-finish")
        message = result[-1]
        frame = message.get("payload", {}).get("frame", {})
        
        if frame and "line" in frame:
            self.code_viewer.set_current_line(frame["line"])
            
        if frame and "fullname" in frame:
            self.code_viewer.file_path = frame["fullname"]
            self.code_viewer.loaded_path = frame["fullname"]

        self.print_message_console(result)
        self.print_watched_variables()
        self.backtrace_refresh()
        self.get_local_variables()
        
    def on_until_click(self):
        result = self.gdb.write("-exec-until")
        self.print_message_console(result)
        self.print_watched_variables()
        self.backtrace_refresh()
        self.get_local_variables()
        
    # Backtrace window functions
    def backtrace_refresh(self):
        self.backtrace_window.clear()
        result = self.gdb.write("-stack-list-frames")
        # print(result)
        
        if result[0]["message"] == 'error':
            self.backtrace_window.addItem(f'Error: {result[0]["payload"]["msg"]}')
        else:
            for element in result[0]["payload"]["stack"]:
                file = element.get("file", {})
                line = element.get("line", {})
                self.backtrace_window.addItem(f'#{element["level"]} {element["func"]} () at {file}:{line}')
        
        # self.print_message_console(result)
        
    def backtrace_window_on_item_click(self, item):
        result = self.gdb.write(f"-stack-select-frame {item.text()[1]}")
        # print(result)
        result2 = self.gdb.write("-stack-info-frame")
        # print(result2)
        self.code_viewer.file_path = result2[0]["payload"]["frame"]["fullname"]
        self.code_viewer.set_current_line(result2[0]["payload"]["frame"]["line"])
        self.get_frame_variables(result2[0]["payload"]["frame"]["level"])
        self.print_message_console(result)
        self.print_message_console(result2)
    
    def on_breakpoint_toggle(self, line, is_set, file):
        if is_set:
            # print(f"Breakpoint toggled off in line {line}")
            result = self.gdb.write(f"clear {file}:{line}")
            self.print_message_console(result)
        else:
            # print(f"Breakpoint toggled on in line {line}")
            result = self.gdb.write(f"-break-insert --source {self.code_viewer.file_path} --line {line}")
            for message in result:
                bkpt = message.get("payload", {}).get("bkpt")
                if bkpt and "line" in bkpt:
                    # print(bkpt["line"])
                    self.code_viewer.add_breakpoint(bkpt["line"], self.code_viewer.file_path)
                    # self.code_viewer.set_current_line(bkpt["line"])
            self.print_message_console(result)
            
    def get_variable_value(self, var):
        result = self.gdb.write(f'-data-evaluate-expression "{var}"')
        self.print_var(result, var)
        
    def print_var(self, result, var):
        # print(result)
        # print(var + " = " + result[-1]["payload"]["value"])
        if result[-1]["message"] == "done":
            self.debug_output.appendPlainText(var + " = " + result[-1]["payload"]["value"])
        
    # Context menu functions
    def add_var_to_watchlist(self, var):
        self.watched_variables.append(var)
        
    def print_watched_variables(self):
        for var in self.watched_variables:
            self.get_variable_value(var)

    # Command line function
    def send_command(self):
        command = self.command_line.text().strip()
        result = self.gdb.write(command)
        self.command_line.clear()
        # print(result)
        if command.startswith("-"):
            self.debug_output.appendPlainText(command)
        self.print_message_console(result)
    
    def get_source_file(self):
        result = self.gdb.write("-file-list-exec-source-file")
        # print(result)
        self.source_path = result[0]["payload"]["fullname"]
        
    # Source files explorer functions
    def get_source_files(self):
        result = self.gdb.write("-file-list-exec-source-files")
        # print(result)
        
        self.code_viewer.file_path = result[0]["payload"]["files"][0]["fullname"]
        self.code_viewer.loaded_path = result[0]["payload"]["files"][0]["fullname"]
        
        for file in result[0]["payload"]["files"]:
            # print(file)
            if file["fullname"].startswith(("/usr/include", "/usr/lib", "usr/local/include", "/lib", "opt")):
                continue
            
            self.file_browser.addItem(file["fullname"])
            # self.file_browser.addItem(file["fullname"].split("/")[-1])
            # self.sources.append(file)
            # self.sources2[file["fullname"]] = file["fullname"].split("/")[-1]
            
    def file_browser_item_clicked(self, item):
        file_path = ""
        for file in self.sources:
            if file["fullname"] == item.text():
                file_path = file["fullname"]
        # for key in self.sources2:
        #     if self.sources2[key] == item.text():
        #         file_path = key
        # self.code_viewer.file_path = file_path
        
    def get_local_variables(self):
        result = self.gdb.write("-stack-list-variables --all-values")
        self.local_variables.clear()
        # print(result)
        if result[0]["message"] == "error":
            print(result)
        else:
            for var in result[0]["payload"]["variables"]:
                # print(var)
                name = var["name"]
                value = var["value"]
                self.local_variables.addItem(f"{name} = {value}")
            
    def get_frame_variables(self, frame):
        result = self.gdb.write(f"-stack-list-variables --thread 1 --frame {frame} --all-values")
        self.local_variables.clear()
        # print(result)
        for var in result[0]["payload"]["variables"]:
            name = var["name"]
            value = var["value"]
            self.local_variables.addItem(f"{name} = {value}")
        
    def print_message_console(self, result):
        for element in result:
            message = str(element["message"]) if element["message"] is not None else ""
            payload = str(element["payload"]) if element["payload"] is not None else ""
            line = (message + " " if message else "") + (payload if payload else "") + "\n"

            if element["type"] == "output":
                self.console_output.appendPlainText(line)
            else:
                self.debug_output.appendPlainText(line)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <binary>")
        sys.exit(1)

    app = QApplication(sys.argv)
    win = MainWindow(sys.argv[1])
    win.show()
    sys.exit(app.exec_())

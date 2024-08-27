# -*- coding: utf-8 -*-


import os
import sys
from functools import partial

lib_path = "\\\\192.168.10.190\\substorage2\\MTHD_core\\inhouse\\maya\\site-packages"
if not lib_path in sys.path:
    sys.path.append(lib_path)
import qdarktheme
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *


class ReferenceChanger(QMainWindow):
    def __init__(self):
        super(ReferenceChanger, self).__init__()

        self.load_thread_running = False
        self.load_thread_canceled = False
        self.ref_data = {}
        
        self.setup_ui()
        self.set_widget()
        self.set_layout()
        self.connections()
        
    def setup_ui(self):
        self.setWindowTitle("Reference Changer")
        self.setMinimumSize(1100, 600)
        self.setWindowIcon(QIcon("./icon.png"))
        self.font = QFont("Segoe UI", 10)
        QApplication.setFont(self.font)
        qdarktheme.setup_theme()
        
    def set_widget(self):
        # Load
        self.main_widget = QWidget()
        self.ma_file_lb = QLabel("File")
        self.ma_file_le = QLineEdit()
        self.ma_file_browse_btn = QPushButton("Load")
        self.ma_file_browse_btn.setFixedSize(80, 30)
        
        # Reference
        self.table_widget = QTableWidget()
        
        # Buttons
        self.hspacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedSize(80, 30)
        self.start_btn = QPushButton("Start")
        self.start_btn. setFixedSize(80, 30)
    
    def set_layout(self):
        main_layout = QVBoxLayout()
        
        # Load
        ma_layout = QHBoxLayout()
        ma_layout.addWidget(self.ma_file_lb)
        ma_layout.addWidget(self.ma_file_le)
        ma_layout.addWidget(self.ma_file_browse_btn)
        main_layout.addLayout(ma_layout)
        
        # Reference
        main_layout.addWidget(self.table_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addItem(self.hspacer)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.start_btn)
        main_layout.addLayout(btn_layout)
        
        # Set Main Layout
        self.main_widget.setLayout(main_layout)
        self.setCentralWidget(self.main_widget)
    
    def connections(self):
        self.ma_file_browse_btn.clicked.connect(self.browse_file)
        self.reset_btn.clicked.connect(self.reset)
        self.start_btn.clicked.connect(self.update_reference)
        
    def reset(self):
        """
        Reset the data and clear the table widget
        """
        self.ma_file_le.clear()
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        self.ref_data = {}
        
    def browse_file(self):
        """
        Browse the file and set the file path to the line edit
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "V:/", "Maya ASCII Files (*.ma)")
        file_path = file_path.replace("/", os.sep)
        self.ma_file_le.setText(file_path)
        self.load_file()
    
    def load_file(self):
        """
        Load the file and get the references
        """
        if not self.ma_file_le.text():
            QMessageBox.critical(self, "Error", "Please select a file")
            self.reset()
            return
        
        ma_file = self.ma_file_le.text()
        if not os.path.exists(ma_file):
            QMessageBox.critical(self, "Error", "File does not exist")
            self.reset()
            return
        
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        
        self.load_thread_canceled = False
        self.load_thread = FileLoadThread(ma_file)
        self.load_thread.start()
        self.load_thread_running = True
        self.load_thread.error_occurred.connect(lambda x: QMessageBox.critical(self, "Error", x))
        self.load_thread.ref_found.connect(self.load_finished)
        
        self.load_progress = QProgressDialog("Loading...", "Cancel", 0, 0, self)
        self.load_progress.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.load_progress.setWindowTitle("Load File")
        self.load_progress.resize(200, 100)
        self.load_progress.canceled.connect(self.load_canceled)
        self.load_progress.exec_()
        
    def load_canceled(self):
        """
        If the load canceled, cancel the thread and show information message
        """
        self.load_thread_canceled = True
        self.load_thread.cancel()
        self.load_thread_running = False
        QMessageBox.information(self, "Canceled", "File loading canceled")
        
    def load_finished(self, found_list: list, found_list2: list):
        """
        If the references found, parse the data and set the data to the table widget

        Args:
            found_list (list): List of found references
            found_list2 (list): List of found reference depth info
        """
        if not len(found_list):
            self.load_progress.canceled.disconnect()
            self.load_progress.close()
            QMessageBox.warning(self, "Warning", "No reference found")
            return
        else:
            if not self.load_thread_canceled:
                self.load_progress.canceled.disconnect()
                self.load_progress.close()
                self.load_thread_running = False
                self.parse_data(found_list, found_list2)

    def parse_data(self, found_list: list, found_list2: list):
        """
        Parse the found list and set the data to the table widget

        Args:
            found_list (list): List of found references
            found_list2 (list): List of found reference depth info
        """
        combined_list = list(zip(found_list, found_list2)) ###
        
        # for idx, (ref, line_cnt) in enumerate(found_list):
        for idx, ((ref_r, line_cnt_r), (ref_rdi, line_cnt_rdi)) in enumerate(combined_list):
            
            namespace = ref_r.split("-ns")[-1].split('"')[1] if "-ns" in ref_r else "None"
            ref_node = ref_r.split("-rfn")[-1].split()[0].replace('"', '') if "-rfn" in ref_r else "None"
            ref_type = ref_r.split("-typ")[-1].split()[0].replace('"', '') if "-typ" in ref_r else "None"
            ref_path_r = ref_r.split("-typ")[-1].split()[1].replace(';', '') if "-typ" in ref_r else "None"
            ref_path_rdi = ref_rdi.split("-typ")[-1].split()[1].replace(';', '') if "-typ" in ref_rdi else "None"
            
            
            self.ref_data[idx] = {
                "found_line_r": line_cnt_r,
                "found_line_rdi": line_cnt_rdi,
                "namespace": namespace,
                "ref_node": ref_node,
                "ref_type": ref_type,
                "ref_path_r": ref_path_r.replace('"', ''),
                "ref_path_rdi": ref_path_rdi
            }
            
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(
            ["Found Line", "Namespace", "Reference Node", "Reference Type", "Reference Path", "Update Path"]
            )
        self.table_widget.setRowCount(len(self.ref_data))
        
        for idx, data in self.ref_data.items():
            self.table_widget.setItem(idx, 0, QTableWidgetItem(str(data["found_line_r"])))
            self.table_widget.setItem(idx, 1, QTableWidgetItem(data["namespace"]))
            self.table_widget.setItem(idx, 2, QTableWidgetItem(data["ref_node"]))
            self.table_widget.setItem(idx, 3, QTableWidgetItem(data["ref_type"]))
            self.table_widget.setItem(idx, 4, QTableWidgetItem(data["ref_path_r"]))
            self.table_widget.setRowHeight(idx, 30)
            
            # Create and add a button to the 4th column
            update_btn = QPushButton("Browse")
            update_btn.clicked.connect(partial(self.browse_file_for_row, idx))
            self.table_widget.setCellWidget(idx, 5, update_btn)

        self.table_widget.resizeColumnsToContents()
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_widget.hideColumn(0)
        
        # if right click, shot context menu
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, pos):
        """
        Show context menu for the table widget

        Args:
            pos (QPoint): Position of the mouse
        """
        context_menu = QMenu()
        update_action = context_menu.addAction("Update Reference")
        action = context_menu.exec_(self.table_widget.mapToGlobal(pos))
        selected = self.table_widget.selectedItems()
        selected_rows = list(set([item.row() for item in selected]))
        if not len(selected_rows):
            return
        
        if action == update_action:
            start_path = os.path.dirname(self.table_widget.item(selected_rows[0], 4).text()).replace("/", os.sep).replace('"', '')
            print(start_path)
            file, _ = QFileDialog.getOpenFileName(
                self, 
                "Open File", 
                start_path,
                "Maya Scene Files (*.ma *mb);; Maya ASCII Files (*.ma);; Maya Binary Files (*.mb)"
            )
            if file:
                for row in selected_rows:
                    self.table_widget.setItem(row, 4, QTableWidgetItem(file))
                    self.table_widget.item(row, 4).setTextColor(QColor(0, 220, 0))
                    if file.endswith(".ma"):
                        self.table_widget.item(row, 3).setText("mayaAscii")
                        self.table_widget.item(row, 3).setTextColor(QColor(0, 220, 0))
                    elif file.endswith(".mb"):
                        self.table_widget.item(row, 3).setText("mayaBinary")
                        self.table_widget.item(row, 3).setTextColor(QColor(0, 220, 0))
                    
    def browse_file_for_row(self, row: int):
        """
        Browse file for the selected row

        Args:
            row (int): Selected row
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open File", 
            os.path.dirname(self.table_widget.item(row, 4).text()),
            "Maya Binary Files (*.mb)"
            )
        file_path = file_path.replace("/", os.sep)
        
        if not file_path:
            return
        
        self.table_widget.setItem(row, 4, QTableWidgetItem(file_path))
        self.table_widget.item(row, 4).setTextColor(QColor(0, 220, 0))
        if file_path.endswith(".ma"):
            self.table_widget.item(row, 3).setText("mayaAscii")
            self.table_widget.item(row, 3).setTextColor(QColor(0, 220, 0))
        elif file_path.endswith(".mb"):
            self.table_widget.item(row, 3).setText("mayaBinary")
            self.table_widget.item(row, 3).setTextColor(QColor(0, 220, 0))
    
    def update_reference(self):
        """
        Set the data to the reference path and update the reference path
        """
        change_data_r = {}
        change_data_rdi = {}
        message = ""
        
        for idx in range(self.table_widget.rowCount()):
            original_r = self.ref_data[idx]["ref_path_r"]
            new_r = self.table_widget.item(idx, 4).text()
            original_rdi = self.ref_data[idx]["ref_path_rdi"]
            new_rdi = self.table_widget.item(idx, 4).text()
            
            if original_r != new_r:
                line_number_r = self.ref_data[idx]["found_line_r"]
                change_data_r[line_number_r] = (original_r.replace(os.sep, "/"), new_r.replace(os.sep, "/"))
                line_number_rdi = self.ref_data[idx]["found_line_rdi"]
                change_data_rdi[line_number_rdi] = (original_rdi.replace(os.sep, "/"), new_rdi.replace(os.sep, "/"))
                message += f"{idx + 1}. {os.path.basename(original_r)} -> {os.path.basename(new_r)}\n"


        if not self.ma_file_le.text():
            QMessageBox.warning(self, "Error", "Please select a file")
            return
        
        if not change_data_r and not change_data_rdi:
            QMessageBox.warning(self, "Error", "Nothing to change")
            return
        
        confirm = QMessageBox.question(
            self, 
            "Change Reference", 
            f"""
    Are you sure you want to change the reference path?
            
    {message}
    """, 
            QMessageBox.Yes | QMessageBox.No
            )
        
        if confirm == QMessageBox.Yes:
            self.change_thread = FileChangeThread(change_data_r, change_data_rdi, self.ma_file_le.text())
            self.change_thread.file_changed.connect(self.change_finished)
            self.change_thread.start()
            
            self.change_progress = QProgressDialog("Changing...", "Cancel", 0, 0, self)
            self.change_progress.setWindowTitle("Change Reference")
            self.change_progress.setCancelButton(None)
            self.change_progress.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            self.change_progress.setWindowFlag(Qt.WindowCloseButtonHint, False)
            self.change_progress.resize(200, 100)
            self.change_progress.exec_()
    
    def change_finished(self, changed: bool, message: str):
        """
        If the reference path changed successfully, show information message

        Args:
            changed (bool): True if the reference path changed successfully
            message (str): Error message if the reference path not changed successfully
        """
        if changed:
            self.change_progress.close()
            QMessageBox.information(self, "Success", "Reference path changed successfully")
            self.load_file()
        else:
            self.change_progress.close()
            QMessageBox.critical(self, "Error", message)
                
    def closeEvent(self, event):
        if self.load_thread_running:
            self.load_thread.cancel()
        event.accept()


class FileChangeThread(QThread):
    """
    Thread class to change the reference path
    """
    file_changed = Signal(bool, str)
    
    def __init__(self, change_data_r: dict, change_data_rdi:dict, ma_file: str):
        super(FileChangeThread, self).__init__()
        self.change_data_r = change_data_r
        self.change_data_rdi = change_data_rdi
        self.ma_file = ma_file
        self.backup_file = ma_file.replace(".ma", "_low.ma")
        self.is_canceled = False
        
    def run(self):
        try:
            # copy original file to backup file
            if not os.path.exists(self.backup_file):
                with open(self.ma_file, "r") as original:
                    with open(self.backup_file, "w") as backup:
                        backup.write(original.read())
            
            with open(self.ma_file, "r") as f:
                lines = f.readlines()
            
            with open(self.ma_file, "w") as f:
                for idx, line in enumerate(lines):
                    if idx in self.change_data_r:
                        original, new = self.change_data_r[idx]
                        line = line.replace(original, f'"{new}"')
                        if new.endswith(".ma"):
                            line = line.replace("mayaBinary", "mayaAscii")
                        elif new.endswith(".mb"):
                            line = line.replace("mayaAscii", "mayaBinary")
                    if idx in self.change_data_rdi:
                        original, new = self.change_data_rdi[idx]
                        line = line.replace(original, f'"{new}"')
                        if new.endswith(".ma"):
                            line = line.replace("mayaBinary", "mayaAscii")
                        elif new.endswith(".mb"):
                            line = line.replace("mayaAscii", "mayaBinary")
                    f.write(line)
                
            self.file_changed.emit(True, "")
            
        except Exception as e:
            self.file_changed.emit(False, str(e))
            return
    
    def cancel(self):
        self.is_canceled = True
        self.quit()
        self.wait(1000)


class FileLoadThread(QThread):
    """
    Thread class to load the file and get the references
    """
    error_occurred = Signal(str)
    file_parsed = Signal(str)
    ref_found = Signal(list, list)

    def __init__(self, ma_file):
        super(FileLoadThread, self).__init__()
        self.ma_file = ma_file
        self.is_canceled = False
        self.found_list = []
        self.found_list2 = []
        
    def run(self):
        try:
            buffer = ""
            with open(self.ma_file, "r") as f:
                for idx, line in enumerate(f):
                    if self.is_canceled:
                        break
                    buffer += line.strip()

                    if ";" in line:
                        if "file -r " in buffer:
                            self.found_list.append((buffer, idx))
                        if "file -rdi " in buffer:
                            self.found_list2.append((buffer, idx))
                        buffer = ""
            self.ref_found.emit(self.found_list, self.found_list2)

        except Exception as e:
            self.error_occurred.emit(str(e))
            return
        
    def cancel(self):
        self.is_canceled = True
        self.quit()
        self.wait(1000)
        
    
if __name__ == '__main__':
    app = QApplication()
    ex = ReferenceChanger()
    ex.show()
    sys.exit(app.exec_())
        
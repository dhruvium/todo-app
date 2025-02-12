import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                             QCalendarWidget, QListWidget, QLineEdit,
                             QPushButton, QLabel, QListWidgetItem, 
                             QMenu, QAction, QStackedWidget)
from PyQt5.QtCore import QDate, Qt, QSize, QUrl
from PyQt5.QtGui import QFont, QColor, QPainter
from PyQt5.QtMultimedia import QSoundEffect
import time
import logging
from pathlib import Path



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='todoapp.log',
    filemode='w'
)

class CustomCalendar(QCalendarWidget):
    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        parent = self.parent()
        if parent:
            date_str = date.toString(Qt.ISODate)
            count = len(parent.todos.get(date_str, []))
            if count > 0:
                painter.save()
                painter.setFont(QFont('Arial', 8))
                painter.setPen(QColor(255, 255, 255))  # White text
                painter.drawText(rect, Qt.AlignRight | Qt.AlignTop, str(count))
                painter.restore()



class TodoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.todos = {}
        self.long_term_tasks = []
        self.current_date = None
        self.init_ui()
        self.load_data()
        self.setup_sound()

    def setup_sound(self):
        self.sound = QSoundEffect()
        try:
            if getattr(sys, 'frozen', False):
                # Packaged app - sound file is in Resources directory
                base_path = Path(sys._MEIPASS)
            else:
                # Development path
                base_path = Path(__file__).parent
                
            sound_path = base_path / "ting.wav"
            logging.info(f"Sound path: {sound_path}")
            self.sound.setSource(QUrl.fromLocalFile(str(sound_path)))
        except Exception as e:
            logging.error(f"Sound initialization failed: {str(e)}")


    def init_ui(self):
        main_layout = QHBoxLayout(self)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QCalendarWidget {
                background-color: #404040;
                border-radius: 10px;
                padding: 5px;
            }
            QListWidget {
                background-color: #404040;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QLineEdit {
                background-color: #404040;
                border: 2px solid #5A5A5A;
                border-radius: 5px;
                padding: 8px;
                font-size: 16px;
                color: white;
            }
            QPushButton {
                background-color: #5A5A5A;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: white;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #6C6C6C;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
        """)

        # Calendar section
        self.calendar = CustomCalendar()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.handle_date_changed)
        main_layout.addWidget(self.calendar)

        # Right side container
        right_layout = QVBoxLayout()
        
        # Header with date and switch button
        header_layout = QHBoxLayout()
        self.date_label = QLabel("Selected Date: ")
        self.switch_btn = QPushButton("⏳ Long-term Tasks")
        self.switch_btn.clicked.connect(self.toggle_view)
        header_layout.addWidget(self.date_label)
        header_layout.addWidget(self.switch_btn)
        right_layout.addLayout(header_layout)

        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()
        
        # Daily tasks view
        self.daily_view = QWidget()
        daily_layout = QVBoxLayout()
        self.todo_list = QListWidget()
        self.todo_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.todo_list.customContextMenuRequested.connect(self.show_daily_context_menu)
        self.todo_list.itemChanged.connect(self.handle_item_changed)
        self.todo_list.setSpacing(5)
        daily_layout.addWidget(self.todo_list)
        
        # Daily tasks input
        daily_input_layout = QHBoxLayout()
        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("Enter new task...")
        self.add_btn = QPushButton("➕ Add Task")
        self.add_btn.clicked.connect(self.add_todo)
        self.delete_btn = QPushButton("🗑️ Delete Task")
        self.delete_btn.clicked.connect(self.delete_todo)
        
        daily_input_layout.addWidget(self.todo_input)
        daily_input_layout.addWidget(self.add_btn)
        daily_input_layout.addWidget(self.delete_btn)
        daily_layout.addLayout(daily_input_layout)
        self.daily_view.setLayout(daily_layout)
        
        # Long-term tasks view
        self.long_term_view = QWidget()
        lt_layout = QVBoxLayout()
        self.lt_list = QListWidget()
        self.lt_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lt_list.customContextMenuRequested.connect(self.show_lt_context_menu)
        self.lt_list.setSpacing(5)
        lt_layout.addWidget(self.lt_list)
        
        # Long-term tasks input
        lt_input_layout = QHBoxLayout()
        self.lt_input = QLineEdit()
        self.lt_input.setPlaceholderText("Enter new long-term task...")
        self.lt_add_btn = QPushButton("➕ Add Task")
        self.lt_add_btn.clicked.connect(self.add_lt_task)
        self.lt_delete_btn = QPushButton("🗑️ Delete Task")
        self.lt_delete_btn.clicked.connect(self.delete_lt_task)
        
        lt_input_layout.addWidget(self.lt_input)
        lt_input_layout.addWidget(self.lt_add_btn)
        lt_input_layout.addWidget(self.lt_delete_btn)
        lt_layout.addLayout(lt_input_layout)
        self.long_term_view.setLayout(lt_layout)
        
        self.stacked_widget.addWidget(self.daily_view)
        self.stacked_widget.addWidget(self.long_term_view)
        right_layout.addWidget(self.stacked_widget)
        
        main_layout.addLayout(right_layout)

        self.setWindowTitle('Dhruvium To-do App')
        self.setGeometry(300, 300, 1000, 600)
        self.show()

    def handle_date_changed(self):
        self.current_date = self.calendar.selectedDate().toString(Qt.ISODate)
        self.date_label.setText(f"Selected Date: {self.current_date}")
        self.update_todo_list()

    def update_todo_list(self):
        self.todo_list.clear()
        if self.current_date in self.todos:
            for todo in self.todos[self.current_date]:
                item = QListWidgetItem(todo["text"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked if todo["done"] else Qt.Unchecked)
                
                font = QFont('Arial', 14)
                font.setStrikeOut(todo["done"])
                item.setFont(font)
                
                item.setForeground(QColor(255, 255, 255))
                item.setSizeHint(QSize(0, 40))
                
                if todo["done"]:
                    item.setBackground(QColor(67, 160, 71))
                    self.sound.play()
                else:
                    item.setBackground(QColor(198, 40, 40))
                
                self.todo_list.addItem(item)

    def toggle_view(self):
        if self.stacked_widget.currentIndex() == 0:
            self.stacked_widget.setCurrentIndex(1)
            self.switch_btn.setText("📅 Daily Tasks")
            self.update_lt_list()
        else:
            self.stacked_widget.setCurrentIndex(0)
            self.switch_btn.setText("⏳ Long-term Tasks")

    def update_lt_list(self):
        self.lt_list.clear()
        for task in self.long_term_tasks:
            item = QListWidgetItem(task)
            self.lt_list.addItem(item)

    def show_daily_context_menu(self, pos):
        item = self.todo_list.itemAt(pos)
        if item:
            menu = QMenu()
            move_action = QAction("⏳ Move to Long-term", self)
            move_action.triggered.connect(lambda: self.move_to_long_term(item))
            menu.addAction(move_action)
            menu.exec_(self.todo_list.mapToGlobal(pos))

    def show_lt_context_menu(self, pos):
        item = self.lt_list.itemAt(pos)
        if item:
            menu = QMenu()
            move_action = QAction("📅 Move to Daily", self)
            move_action.triggered.connect(lambda: self.move_to_daily(item))
            menu.addAction(move_action)
            menu.exec_(self.lt_list.mapToGlobal(pos))

    def move_to_long_term(self, item):
        task_text = item.text()
        if task_text:
            self.long_term_tasks.append(task_text)
            self.delete_todo_item(item)
            self.update_lt_list()
            self.calendar.updateCells()  # Update calendar counts

    def move_to_daily(self, item):
        task_text = item.text()
        if task_text and self.current_date:
            new_todo = {"text": task_text, "done": False}
            if self.current_date not in self.todos:
                self.todos[self.current_date] = []
            self.todos[self.current_date].append(new_todo)
            self.long_term_tasks.remove(task_text)
            self.update_lt_list()
            self.update_todo_list()
            self.calendar.updateCells()  # Update calendar counts

    def add_todo(self):
        if not self.current_date:
            return

        todo_text = self.todo_input.text().strip()
        if todo_text:
            new_todo = {
                "text": todo_text,
                "done": False
            }
            
            if self.current_date not in self.todos:
                self.todos[self.current_date] = []
            self.todos[self.current_date].append(new_todo)
            self.todo_input.clear()
            self.update_todo_list()
            self.calendar.updateCells()  # Update calendar counts

    def delete_todo(self):
        if not self.current_date or self.todo_list.currentRow() == -1:
            return

        del self.todos[self.current_date][self.todo_list.currentRow()]
        if not self.todos[self.current_date]:
            del self.todos[self.current_date]
        self.update_todo_list()
        self.calendar.updateCells()  # Update calendar counts

    def add_lt_task(self):
        text = self.lt_input.text().strip()
        if text:
            self.long_term_tasks.append(text)
            self.lt_list.addItem(text)
            self.lt_input.clear()

    def delete_lt_task(self):
        if self.lt_list.currentRow() >= 0 and self.lt_list.currentItem():
            self.long_term_tasks.pop(self.lt_list.currentRow())
            self.lt_list.takeItem(self.lt_list.currentRow())

    def handle_item_changed(self, item):
        if self.current_date in self.todos:
            index = self.todo_list.row(item)
            self.todos[self.current_date][index]["done"] = item.checkState() == Qt.Checked
            self.update_todo_list()

    def get_data_path(self):
        """Get correct data path for both development and packaged app"""
        try:
            if getattr(sys, 'frozen', False):
                # For packaged app - use proper macOS application support directory
                from AppKit import NSSearchPathForDirectoriesInDomains
                app_support = NSSearchPathForDirectoriesInDomains(14, 1, True)[0]  # NSApplicationSupportDirectory
                data_dir = Path(app_support) / "YourAppName"
            else:
                # Development path
                data_dir = Path(__file__).parent / "data"
    
            # Create directory if it doesn't exist
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir / "todos.json"
            
        except Exception as e:
            logging.error(f"Path error: {str(e)}")
            return Path.home() / "todos.json"  # Fallback to home directory


    def load_data(self):
        try:
            data_file = self.get_data_path()
            logging.info(f"Loading data from: {data_file}")
            
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    self.todos = data.get('todos', {})
                    self.long_term_tasks = data.get('long_term', [])
        except Exception as e:
            logging.error(f"Load error: {str(e)}", exc_info=True)

    def save_data(self):
        try:
            data_file = self.get_data_path()
            logging.info(f"Saving data to: {data_file}")
            
            data = {
                'todos': self.todos,
                'long_term': self.long_term_tasks
            }
            with open(data_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Save error: {str(e)}", exc_info=True)

    def closeEvent(self, event):
        logging.debug("Closing application")
        self.save_data()
        QApplication.processEvents()
        event.accept()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TodoApp()
    sys.exit(app.exec_())

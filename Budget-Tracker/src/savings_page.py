from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                           QHeaderView, QDialog, QLineEdit, QDateEdit,
                           QFormLayout, QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SavingsGoalDialog(QDialog):
    def __init__(self, parent=None, goal_data=None):
        super().__init__(parent)
        self.goal_data = goal_data
        self.setWindowTitle("Goal" if goal_data else "New Savings Goal")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Goal Name
        self.name_input = QLineEdit()
        if self.goal_data:
            self.name_input.setText(self.goal_data['name'])
        layout.addRow("Goal Name:", self.name_input)

        # Target Amount
        self.target_input = QSpinBox()
        self.target_input.setRange(0, 10000000)
        self.target_input.setSingleStep(1000)
        if self.goal_data:
            self.target_input.setValue(int(self.goal_data['target_amount']))
        layout.addRow("Target Amount (₹):", self.target_input)

        # Target Date
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setMinimumDate(QDate.currentDate())
        if self.goal_data:
            self.date_input.setDate(QDate.fromString(self.goal_data['target_date'], Qt.DateFormat.ISODate))
        else:
            self.date_input.setDate(QDate.currentDate().addMonths(6))
        layout.addRow("Target Date:", self.date_input)

        # Current Amount (only for new goals)
        self.current_input = QSpinBox()
        self.current_input.setRange(0, 10000000)
        self.current_input.setSingleStep(1000)
        if self.goal_data:
            self.current_input.setValue(int(self.goal_data['current_amount']))
        layout.addRow("Current Amount (₹):", self.current_input)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addRow("", button_layout)

    def get_data(self):
        return {
            'name': self.name_input.text(),
            'target_amount': self.target_input.value(),
            'target_date': self.date_input.date().toString(Qt.DateFormat.ISODate),
            'current_amount': self.current_input.value()
        }

class SavingsPage(QWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header
        header = QLabel("Savings Goals")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)

        # Overview
        overview_frame = QFrame()
        overview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        overview_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        overview_layout = QHBoxLayout(overview_frame)

        # Total Savings
        self.total_savings = QLabel("Total Savings: ₹0")
        self.total_savings.setFont(QFont("Segoe UI", 12))
        overview_layout.addWidget(self.total_savings)

        # Add Goal Button
        add_button = QPushButton("Add New Goal")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        add_button.clicked.connect(self.add_goal)
        overview_layout.addWidget(add_button)

        layout.addWidget(overview_frame)

        # Goals Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Goal", "Target Amount", "Current Amount", "Progress",
            "Target Date", "Days Left", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 10px;
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

        # Progress Chart
        chart_frame = QFrame()
        chart_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        chart_frame.setMinimumHeight(300)
        chart_layout = QVBoxLayout(chart_frame)
        
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        layout.addWidget(chart_frame)

    def load_data(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                id,
                name,
                target_amount,
                current_amount,
                target_date
            FROM savings_goals
            ORDER BY target_date
        """)
        goals = cursor.fetchall()
        
        # Update table
        self.table.setRowCount(len(goals))
        total_saved = 0
        
        current_date = QDate.currentDate()
        
        for row, goal in enumerate(goals):
            goal_id, name, target, current, target_date = goal
            total_saved += current
            
            # Goal Name
            self.table.setItem(row, 0, QTableWidgetItem(name))
            
            # Target Amount
            target_item = QTableWidgetItem(f"₹{target:,.2f}")
            target_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.table.setItem(row, 1, target_item)
            
            # Current Amount
            current_item = QTableWidgetItem(f"₹{current:,.2f}")
            current_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.table.setItem(row, 2, current_item)
            
            # Progress
            progress = (current / target * 100) if target > 0 else 0
            progress_item = QTableWidgetItem(f"{progress:.1f}%")
            progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if progress >= 100:
                progress_item.setForeground(QColor("#4CAF50"))
            self.table.setItem(row, 3, progress_item)
            
            # Target Date
            target_date_item = QTableWidgetItem(target_date)
            target_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, target_date_item)
            
            # Days Left
            target_qdate = QDate.fromString(target_date, Qt.DateFormat.ISODate)
            days_left = current_date.daysTo(target_qdate)
            days_item = QTableWidgetItem(str(max(0, days_left)))
            days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if days_left < 0:
                days_item.setForeground(QColor("#f44336"))
            self.table.setItem(row, 5, days_item)
            
            # Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 3px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
            edit_btn.clicked.connect(lambda checked, gid=goal_id: self.edit_goal(gid))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border-radius: 3px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_btn.clicked.connect(lambda checked, gid=goal_id: self.delete_goal(gid))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 6, action_widget)
        
        # Update total savings display
        self.total_savings.setText(f"Total Savings: ₹{total_saved:,.2f}")
        
        # Update chart
        self.update_chart(goals)

    def update_chart(self, goals):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        names = [goal[1] for goal in goals]
        currents = [goal[3] for goal in goals]
        targets = [goal[2] for goal in goals]
        
        x = range(len(names))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], targets, width, label='Target', color='#2196F3')
        ax.bar([i + width/2 for i in x], currents, width, label='Current', color='#4CAF50')
        
        ax.set_ylabel('Amount (₹)')
        ax.set_title('Savings Goals Progress')
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.legend()
        
        self.figure.tight_layout()
        self.canvas.draw()

    def add_goal(self):
        dialog = SavingsGoalDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO savings_goals (name, target_amount, current_amount, target_date)
                VALUES (?, ?, ?, ?)
            """, (data['name'], data['target_amount'], data['current_amount'],
                 data['target_date']))
            self.conn.commit()
            self.load_data()

    def edit_goal(self, goal_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, target_amount, current_amount, target_date
            FROM savings_goals WHERE id = ?
        """, (goal_id,))
        goal_data = cursor.fetchone()
        
        dialog = SavingsGoalDialog(self, {
            'name': goal_data[0],
            'target_amount': goal_data[1],
            'current_amount': goal_data[2],
            'target_date': goal_data[3]
        })
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            cursor.execute("""
                UPDATE savings_goals
                SET name = ?, target_amount = ?, current_amount = ?, target_date = ?
                WHERE id = ?
            """, (data['name'], data['target_amount'], data['current_amount'],
                 data['target_date'], goal_id))
            self.conn.commit()
            self.load_data()

    def delete_goal(self, goal_id):
        reply = QMessageBox.question(
            self,
            'Delete Goal',
            'Are you sure you want to delete this savings goal?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
            self.conn.commit()
            self.load_data()

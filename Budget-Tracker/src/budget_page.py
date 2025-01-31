from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                           QHeaderView, QSpinBox, QDialog, QLineEdit, QComboBox,
                           QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class CategoryDialog(QDialog):
    def __init__(self, parent=None, category_data=None):
        super().__init__(parent)
        self.category_data = category_data
        self.setWindowTitle("Category" if category_data else "New Category")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Category Name
        self.name_input = QLineEdit()
        if self.category_data:
            self.name_input.setText(self.category_data['name'])
        layout.addRow("Name:", self.name_input)

        # Category Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["expense", "income"])
        if self.category_data:
            self.type_combo.setCurrentText(self.category_data['type'])
        layout.addRow("Type:", self.type_combo)

        # Budget Amount
        self.budget_input = QSpinBox()
        self.budget_input.setRange(0, 1000000)
        self.budget_input.setSingleStep(100)
        if self.category_data:
            self.budget_input.setValue(int(self.category_data['budget']))
        layout.addRow("Monthly Budget (₹):", self.budget_input)

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
            'type': self.type_combo.currentText(),
            'budget': self.budget_input.value()
        }

class BudgetPage(QWidget):
    budget_updated = pyqtSignal()

    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header
        header = QLabel("Budget Management")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)

        # Budget Overview
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

        # Total Budget
        self.total_budget = QLabel("Total Budget: ₹0")
        self.total_budget.setFont(QFont("Segoe UI", 12))
        overview_layout.addWidget(self.total_budget)

        # Add Category Button
        add_button = QPushButton("Add Category")
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
        add_button.clicked.connect(self.add_category)
        overview_layout.addWidget(add_button)

        layout.addWidget(overview_frame)

        # Categories Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Category", "Type", "Monthly Budget", "Spent", "Actions"
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

        # Budget Distribution Chart
        chart_frame = QFrame()
        chart_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        chart_frame.setMinimumHeight(300)
        chart_layout = QVBoxLayout(chart_frame)
        
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        layout.addWidget(chart_frame)

    def load_data(self):
        cursor = self.conn.cursor()
        
        # Get categories with their current month spending
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.type,
                c.budget,
                COALESCE(SUM(t.amount), 0) as spent
            FROM categories c
            LEFT JOIN transactions t ON c.id = t.category_id
            AND strftime('%Y-%m', t.date) = strftime('%Y-%m', 'now')
            GROUP BY c.id
            ORDER BY c.type, c.name
        """)
        categories = cursor.fetchall()
        
        # Update table
        self.table.setRowCount(len(categories))
        total_budget = 0
        
        for row, cat in enumerate(categories):
            cat_id, name, cat_type, budget, spent = cat
            total_budget += budget
            
            # Category Name
            self.table.setItem(row, 0, QTableWidgetItem(name))
            
            # Type
            type_item = QTableWidgetItem(cat_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, type_item)
            
            # Budget
            budget_item = QTableWidgetItem(f"₹{budget:,.2f}")
            budget_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.table.setItem(row, 2, budget_item)
            
            # Spent
            spent_item = QTableWidgetItem(f"₹{spent:,.2f}")
            spent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            if spent > budget and budget > 0:
                spent_item.setForeground(QColor("#f44336"))
            self.table.setItem(row, 3, spent_item)
            
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
            edit_btn.clicked.connect(lambda checked, cid=cat_id: self.edit_category(cid))
            
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
            delete_btn.clicked.connect(lambda checked, cid=cat_id: self.delete_category(cid))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 4, action_widget)
        
        # Update total budget display
        self.total_budget.setText(f"Total Monthly Budget: ₹{total_budget:,.2f}")
        
        # Update chart
        self.update_chart(categories)

    def update_chart(self, categories):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        names = [cat[1] for cat in categories]
        budgets = [cat[3] for cat in categories]
        spent = [cat[4] for cat in categories]
        
        x = range(len(names))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], budgets, width, label='Budget', color='#2196F3')
        ax.bar([i + width/2 for i in x], spent, width, label='Spent', color='#4CAF50')
        
        ax.set_ylabel('Amount (₹)')
        ax.set_title('Budget vs Spending by Category')
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.legend()
        
        self.figure.tight_layout()
        self.canvas.draw()

    def add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO categories (name, type, budget)
                VALUES (?, ?, ?)
            """, (data['name'], data['type'], data['budget']))
            self.conn.commit()
            self.load_data()
            self.budget_updated.emit()

    def edit_category(self, category_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, type, budget FROM categories WHERE id = ?", (category_id,))
        cat_data = cursor.fetchone()
        
        dialog = CategoryDialog(self, {
            'name': cat_data[0],
            'type': cat_data[1],
            'budget': cat_data[2]
        })
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            cursor.execute("""
                UPDATE categories
                SET name = ?, type = ?, budget = ?
                WHERE id = ?
            """, (data['name'], data['type'], data['budget'], category_id))
            self.conn.commit()
            self.load_data()
            self.budget_updated.emit()

    def delete_category(self, category_id):
        reply = QMessageBox.question(
            self,
            'Delete Category',
            'Are you sure you want to delete this category?\nAll associated transactions will be preserved.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            self.conn.commit()
            self.load_data()
            self.budget_updated.emit()

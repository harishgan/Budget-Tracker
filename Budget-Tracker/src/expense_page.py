from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                           QLineEdit, QComboBox, QMessageBox, QHeaderView,
                           QMainWindow, QDateEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
from datetime import datetime
import sqlite3

class ExpensePage(QWidget):
    expense_added = pyqtSignal(float, str, str, str)  # amount, category, description, type

    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Add Expense Form
        form_frame = QFrame()
        form_frame.setObjectName("form_frame")
        form_frame.setStyleSheet("""
            QFrame#form_frame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        form_layout = QVBoxLayout(form_frame)
        
        # Title
        title = QLabel("Add New Expense")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        form_layout.addWidget(title)
        
        # Form fields
        fields_layout = QHBoxLayout()
        
        # Date
        date_layout = QVBoxLayout()
        date_label = QLabel("Date:")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)
        fields_layout.addLayout(date_layout)
        
        # Amount
        amount_layout = QVBoxLayout()
        amount_label = QLabel("Amount:")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount")
        self.amount_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_input)
        fields_layout.addLayout(amount_layout)
        
        # Category
        category_layout = QVBoxLayout()
        category_label = QLabel("Category:")
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        fields_layout.addLayout(category_layout)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Enter description")
        self.desc_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        fields_layout.addLayout(desc_layout)
        
        form_layout.addLayout(fields_layout)
        
        # Add button
        add_button = QPushButton("Add Expense")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_button.clicked.connect(self.add_expense)
        form_layout.addWidget(add_button)
        
        layout.addWidget(form_frame)
        
        # Expense History
        history_frame = QFrame()
        history_frame.setObjectName("history_frame")
        history_frame.setStyleSheet("""
            QFrame#history_frame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        history_layout = QVBoxLayout(history_frame)
        
        # Title
        history_title = QLabel("Expense History")
        history_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        history_layout.addWidget(history_title)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Category", "Amount", "Description", "Budget Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #ddd;
            }
        """)
        history_layout.addWidget(self.table)
        
        layout.addWidget(history_frame)

    def show_status_message(self, message, timeout=3000):
        """Show a message in the status bar"""
        # Find the main window by traversing up the widget hierarchy
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        
        if parent and isinstance(parent, QMainWindow):
            parent.statusBar().showMessage(message, timeout)

    def load_categories(self):
        """Load expense categories into combo box"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name 
                FROM categories 
                WHERE type = 'expense'
                ORDER BY name
            """)
            
            categories = cursor.fetchall()
            
            self.category_combo.clear()
            self.category_combo.addItem("Select Category")
            self.category_combo.addItems([cat[0] for cat in categories])
            
        except sqlite3.Error as e:
            print(f"Error loading categories: {e}")
            QMessageBox.warning(self, "Error", 
                              "Failed to load expense categories. Please try again.")

    def load_data(self):
        """Load expense history"""
        try:
            cursor = self.conn.cursor()
            
            # Get expense history with category names and budget status
            cursor.execute("""
                SELECT 
                    t.id,
                    t.date,
                    c.name as category,
                    t.amount,
                    t.description,
                    c.budget,
                    (
                        SELECT SUM(amount) 
                        FROM transactions 
                        WHERE category_id = t.category_id 
                        AND strftime('%Y-%m', date) = strftime('%Y-%m', t.date)
                    ) as monthly_total
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.type = 'expense'
                ORDER BY t.date DESC, t.id DESC
                LIMIT 100
            """)
            
            expenses = cursor.fetchall()
            
            self.table.setRowCount(len(expenses))
            
            for row, (expense_id, date_str, category, amount, description, budget, monthly_total) in enumerate(expenses):
                # Date
                date_item = QTableWidgetItem(
                    datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%b-%Y')
                )
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, date_item)
                
                # Category
                category_item = QTableWidgetItem(category)
                category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, category_item)
                
                # Amount
                amount_item = QTableWidgetItem(f"₹{amount:,.2f}")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.table.setItem(row, 2, amount_item)
                
                # Description
                desc_item = QTableWidgetItem(description or "")
                desc_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, 3, desc_item)
                
                # Budget Status
                if budget > 0:
                    percentage = (monthly_total / budget) * 100
                    if percentage >= 90:
                        status = "Over Budget!"
                        color = "#f44336"  # Red
                    elif percentage >= 75:
                        status = "Near Budget"
                        color = "#ff9800"  # Orange
                    else:
                        status = "Within Budget"
                        color = "#4caf50"  # Green
                    
                    status_item = QTableWidgetItem(
                        f"{status} ({percentage:.1f}%)"
                    )
                else:
                    status_item = QTableWidgetItem("No Budget Set")
                    color = "#757575"  # Gray
                
                status_item.setForeground(Qt.GlobalColor.white)
                status_item.setBackground(QColor(color))
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, status_item)
                
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
                edit_btn.clicked.connect(lambda checked, eid=expense_id: self.edit_expense(eid))
                
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
                delete_btn.clicked.connect(lambda checked, eid=expense_id: self.delete_expense(eid))
                
                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                self.table.setCellWidget(row, 5, action_widget)
            
            # Load categories
            self.load_categories()
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to load expense history")

    def add_expense(self):
        """Add a new expense or update existing one"""
        try:
            amount_text = self.amount_input.text().strip()
            category = self.category_combo.currentText()
            description = self.desc_input.text().strip()
            date = self.date_input.date().toString(Qt.DateFormat.ISODate)
            
            # Validate input
            if not amount_text:
                QMessageBox.warning(self, "Input Error", "Please enter an amount")
                return
            
            if category == "Select Category":
                QMessageBox.warning(self, "Input Error", "Please select a category")
                return
            
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a valid positive number")
                return
            
            # Get category ID
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            category_id = cursor.fetchone()
            
            if not category_id:
                QMessageBox.warning(self, "Error", "Selected category not found")
                return
            
            # If we're editing an existing expense
            if hasattr(self, 'editing_expense_id'):
                cursor.execute("""
                    UPDATE transactions 
                    SET date = ?, amount = ?, category_id = ?, description = ?
                    WHERE id = ?
                """, (date, amount, category_id[0], description, self.editing_expense_id))
                
                # Clear the editing flag
                delattr(self, 'editing_expense_id')
                success_msg = f"Updated expense: ₹{amount:,.2f} for {category}"
            else:
                # Add new transaction
                cursor.execute("""
                    INSERT INTO transactions (date, category_id, amount, description, type)
                    VALUES (?, ?, ?, ?, 'expense')
                """, (date, category_id[0], amount, description))
                success_msg = f"Added expense: ₹{amount:,.2f} for {category}"
            
            self.conn.commit()
            
            # Clear inputs
            self.amount_input.clear()
            self.category_combo.setCurrentIndex(0)
            self.desc_input.clear()
            self.date_input.setDate(QDate.currentDate())
            
            # Refresh data
            self.load_data()
            
            # Show success message
            self.show_status_message(success_msg)
            
            # Emit signal
            self.expense_added.emit(amount, category, description, "expense")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to save expense")
            self.conn.rollback()
        except Exception as e:
            print(f"Error saving expense: {e}")
            QMessageBox.warning(self, "Error", "An error occurred while saving expense")
            self.conn.rollback()

    def edit_expense(self, expense_id):
        """Edit an existing expense"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT t.date, t.amount, t.category_id, c.name, t.description
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.id = ?
            """, (expense_id,))
            
            expense = cursor.fetchone()
            if not expense:
                QMessageBox.warning(self, "Error", "Expense not found")
                return
            
            date_str, amount, category_id, category_name, description = expense
            
            # Pre-fill the form
            self.date_input.setDate(QDate.fromString(date_str, Qt.DateFormat.ISODate))
            self.amount_input.setText(str(amount))
            index = self.category_combo.findText(category_name)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            self.desc_input.setText(description or "")
            
            # Store the expense ID to update it later
            self.editing_expense_id = expense_id
            
            # Show message
            self.show_status_message("Update the expense details and click Add")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to edit expense")
            self.conn.rollback()

    def delete_expense(self, expense_id):
        """Delete an expense"""
        try:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this expense?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ?", (expense_id,))
                self.conn.commit()
                
                self.load_data()
                self.show_status_message("Expense deleted successfully")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to delete expense")
            self.conn.rollback()

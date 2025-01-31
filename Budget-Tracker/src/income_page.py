from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                           QLineEdit, QComboBox, QMessageBox, QHeaderView,
                           QMainWindow, QDateEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
from datetime import datetime, date
import sqlite3
from dateutil.relativedelta import relativedelta

class IncomePage(QWidget):
    income_added = pyqtSignal(float, str, str)  # amount, source, frequency

    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Add Income Form
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
        title = QLabel("Add New Income")
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
        
        # Source
        source_layout = QVBoxLayout()
        source_label = QLabel("Source:")
        self.source_combo = QComboBox()
        self.source_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)
        fields_layout.addLayout(source_layout)
        
        # Frequency
        freq_layout = QVBoxLayout()
        freq_label = QLabel("Frequency:")
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["One-time", "Monthly", "Quarterly", "Yearly"])
        self.freq_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_combo)
        fields_layout.addLayout(freq_layout)
        
        form_layout.addLayout(fields_layout)
        
        # Add button
        add_button = QPushButton("Add Income")
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
        add_button.clicked.connect(self.add_income)
        form_layout.addWidget(add_button)
        
        layout.addWidget(form_frame)
        
        # Income List
        list_frame = QFrame()
        list_frame.setObjectName("list_frame")
        list_frame.setStyleSheet("""
            QFrame#list_frame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        list_layout = QVBoxLayout(list_frame)
        
        # Title
        list_title = QLabel("Income History")
        list_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        list_layout.addWidget(list_title)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Source", "Amount", "Frequency", "Next Due", "Actions"
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
        list_layout.addWidget(self.table)
        
        layout.addWidget(list_frame)

    def load_data(self):
        """Load income history"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    id,
                    date,
                    source,
                    amount,
                    is_recurring,
                    frequency,
                    next_date
                FROM income
                ORDER BY date DESC, id DESC
                LIMIT 100
            """)
            
            incomes = cursor.fetchall()
            
            self.table.setRowCount(len(incomes))
            
            for row, (income_id, date_str, source, amount, is_recurring, frequency, next_date) in enumerate(incomes):
                # Date
                date_item = QTableWidgetItem(
                    datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%b-%Y')
                )
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, date_item)
                
                # Source
                source_item = QTableWidgetItem(source)
                source_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, source_item)
                
                # Amount
                amount_item = QTableWidgetItem(f"₹{amount:,.2f}")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.table.setItem(row, 2, amount_item)
                
                # Frequency
                freq_text = frequency.title() if is_recurring else "One-time"
                freq_item = QTableWidgetItem(freq_text)
                freq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, freq_item)
                
                # Next Due
                if next_date:
                    next_due = datetime.strptime(next_date, '%Y-%m-%d').strftime('%d-%b-%Y')
                    next_item = QTableWidgetItem(next_due)
                    
                    # Color code based on due date
                    today = date.today()
                    due_date = datetime.strptime(next_date, '%Y-%m-%d').date()
                    days_until = (due_date - today).days
                    
                    if days_until < 0:
                        next_item.setForeground(QColor("#f44336"))  # Red for overdue
                    elif days_until <= 7:
                        next_item.setForeground(QColor("#ff9800"))  # Orange for due soon
                    else:
                        next_item.setForeground(QColor("#4caf50"))  # Green for upcoming
                else:
                    next_item = QTableWidgetItem("N/A")
                
                next_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, next_item)
                
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
                edit_btn.clicked.connect(lambda checked, iid=income_id: self.edit_income(iid))
                
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
                delete_btn.clicked.connect(lambda checked, iid=income_id: self.delete_income(iid))
                
                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                self.table.setCellWidget(row, 5, action_widget)
            
            # Load sources
            self.load_sources()
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to load income history")

    def load_sources(self):
        """Load income sources"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT name 
                FROM categories 
                WHERE type = 'income'
                ORDER BY name
            """)
            
            sources = cursor.fetchall()
            
            self.source_combo.clear()
            self.source_combo.addItem("Select Source")
            self.source_combo.addItems([src[0] for src in sources])
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to load income sources")

    def calculate_next_date(self, frequency):
        """Calculate next due date based on frequency"""
        today = date.today()
        
        if frequency == "monthly":
            # Add one month, handling end-of-month cases
            next_date = today + relativedelta(months=1)
            # If original day is greater than last day of next month,
            # set to last day of next month
            if today.day > next_date.day:
                next_date = next_date.replace(day=next_date.day)
                
        elif frequency == "quarterly":
            # Add three months
            next_date = today + relativedelta(months=3)
            # Handle end-of-month cases
            if today.day > next_date.day:
                next_date = next_date.replace(day=next_date.day)
                
        elif frequency == "yearly":
            # Add one year
            next_date = today + relativedelta(years=1)
            
        else:  # one-time
            next_date = None
            
        return next_date

    def show_status_message(self, message, timeout=3000):
        """Show a message in the status bar"""
        # Find the main window by traversing up the widget hierarchy
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        
        if parent and isinstance(parent, QMainWindow):
            parent.statusBar().showMessage(message, timeout)

    def add_income(self):
        """Add new income entry or update existing one"""
        try:
            # Validate input
            amount_text = self.amount_input.text().strip()
            source = self.source_combo.currentText()
            frequency = self.freq_combo.currentText().lower()
            date = self.date_input.date().toString(Qt.DateFormat.ISODate)
            
            if not amount_text:
                QMessageBox.warning(self, "Input Error", "Please enter an amount")
                return
            
            if source == "Select Source":
                QMessageBox.warning(self, "Input Error", "Please select an income source")
                return
            
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a valid positive number")
                return
            
            # Calculate next due date for recurring income
            is_recurring = frequency != "one-time"
            next_date = self.calculate_next_date(frequency) if is_recurring else None
            
            cursor = self.conn.cursor()
            
            # If we're editing an existing income
            if hasattr(self, 'editing_income_id'):
                cursor.execute("""
                    UPDATE income 
                    SET date = ?, amount = ?, source = ?, is_recurring = ?, 
                        frequency = ?, next_date = ?
                    WHERE id = ?
                """, (date, amount, source, is_recurring, 
                      frequency if is_recurring else None,
                      next_date.isoformat() if next_date else None,
                      self.editing_income_id))
                
                # Clear the editing flag
                delattr(self, 'editing_income_id')
                success_msg = f"Updated {frequency} income: ₹{amount:,.2f} from {source}"
            else:
                # Add new income
                cursor.execute("""
                    INSERT INTO income (date, source, amount, is_recurring, 
                                      frequency, next_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date, source, amount, is_recurring, 
                      frequency if is_recurring else None,
                      next_date.isoformat() if next_date else None))
                success_msg = f"Added {frequency} income: ₹{amount:,.2f} from {source}"
            
            self.conn.commit()
            
            # Clear inputs
            self.amount_input.clear()
            self.source_combo.setCurrentIndex(0)
            self.freq_combo.setCurrentIndex(0)
            self.date_input.setDate(QDate.currentDate())
            
            # Refresh data
            self.load_data()
            
            # Show success message
            self.show_status_message(success_msg)
            
            # Emit signal
            self.income_added.emit(amount, source, frequency)
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to save income entry")
            self.conn.rollback()
        except Exception as e:
            print(f"Error saving income: {e}")
            QMessageBox.warning(self, "Error", "An error occurred while saving income")
            self.conn.rollback()

    def edit_income(self, income_id):
        """Edit an existing income entry"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT date, amount, source, is_recurring, frequency
                FROM income
                WHERE id = ?
            """, (income_id,))
            
            income = cursor.fetchone()
            if not income:
                QMessageBox.warning(self, "Error", "Income entry not found")
                return
            
            date_str, amount, source, is_recurring, frequency = income
            
            # Pre-fill the form
            self.date_input.setDate(QDate.fromString(date_str, Qt.DateFormat.ISODate))
            self.amount_input.setText(str(amount))
            index = self.source_combo.findText(source)
            if index >= 0:
                self.source_combo.setCurrentIndex(index)
            
            freq_index = self.freq_combo.findText(
                frequency.title() if is_recurring else "One-time"
            )
            if freq_index >= 0:
                self.freq_combo.setCurrentIndex(freq_index)
            
            # Store the income ID to update it later
            self.editing_income_id = income_id
            
            # Show message
            self.show_status_message("Update the income details and click Add")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to edit income entry")
            self.conn.rollback()

    def delete_income(self, income_id):
        """Delete an income entry"""
        try:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this income entry?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM income WHERE id = ?", (income_id,))
                self.conn.commit()
                
                self.load_data()
                self.show_status_message("Income entry deleted successfully")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to delete income entry")
            self.conn.rollback()

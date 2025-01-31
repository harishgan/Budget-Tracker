from PyQt6.QtWidgets import QCalendarWidget, QToolTip
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextCharFormat, QColor, QPalette
import sqlite3

class BudgetCalendarWidget(QCalendarWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.setup_ui()
        self.load_transaction_dates()

    def setup_ui(self):
        # Set calendar styling
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.SingleLetterDayNames)
        
        # Set custom format for weekends
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QColor("#9E9E9E"))
        self.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
        
        # Set today's date format
        today_format = QTextCharFormat()
        today_format.setBackground(QColor("#E3F2FD"))
        today_format.setForeground(QColor("#1976D2"))
        self.setDateTextFormat(QDate.currentDate(), today_format)
        
        # Connect signals
        self.activated.connect(self.show_date_tooltip)
        self.clicked.connect(self.show_date_tooltip)

    def load_transaction_dates(self):
        cursor = self.conn.cursor()
        
        # Get all dates with transactions and their total amounts
        cursor.execute("""
            SELECT 
                date,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                COUNT(*) as transaction_count
            FROM transactions 
            GROUP BY date
        """)
        
        transactions = cursor.fetchall()
        
        # Format dates with transactions
        for date_str, expenses, income, count in transactions:
            date = QDate.fromString(date_str, Qt.DateFormat.ISODate)
            
            # Create format based on transaction type
            fmt = QTextCharFormat()
            
            # If there's both income and expenses
            if income > 0 and expenses > 0:
                fmt.setBackground(QColor("#E8F5E9"))  # Light green
                fmt.setForeground(QColor("#2E7D32"))  # Dark green
            # If there's only income
            elif income > 0:
                fmt.setBackground(QColor("#E3F2FD"))  # Light blue
                fmt.setForeground(QColor("#1976D2"))  # Dark blue
            # If there's only expenses
            else:
                fmt.setBackground(QColor("#FFEBEE"))  # Light red
                fmt.setForeground(QColor("#C62828"))  # Dark red
            
            # Add a border to make the date stand out
            fmt.setFontWeight(600)  # Semi-bold
            
            # Store transaction info for tooltip
            fmt.setToolTip(f"""
                Date: {date.toString("MMM d, yyyy")}
                Transactions: {count}
                Income: ₹{income:,.2f}
                Expenses: ₹{expenses:,.2f}
                Net: ₹{income - expenses:,.2f}
            """.strip())
            
            self.setDateTextFormat(date, fmt)

    def show_date_tooltip(self, date):
        # Get the format for the date
        fmt = self.dateTextFormat(date)
        tooltip_text = fmt.toolTip()
        
        if tooltip_text:
            # Show tooltip at mouse position
            QToolTip.showText(self.cursor().pos(), tooltip_text)
        else:
            QToolTip.hideText()

    def update_transactions(self):
        """Refresh the calendar with latest transaction data"""
        # Clear existing formats except for weekends
        self.setup_ui()
        # Reload transaction dates
        self.load_transaction_dates()

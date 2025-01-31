import sqlite3
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                           QLineEdit, QComboBox, QTableWidget, QProgressBar,
                           QMessageBox, QFrame, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QIcon, QColor, QFont
import pandas as pd
from pathlib import Path
import json
from qt_material import apply_stylesheet
from src.dashboard import DashboardPage
from src.income_page import IncomePage
from src.expense_page import ExpensePage
from src.budget_page import BudgetPage
from src.savings_page import SavingsPage
from src.reports_page import ReportsPage

class BudgetTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Budget Tracker")
        self.setMinimumSize(1000, 700)
        
        # Connect to application quit signal
        QApplication.instance().aboutToQuit.connect(self.backup_database)
        
        try:
            self.init_db()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", 
                               f"Failed to initialize database: {str(e)}\nPlease ensure you have write permissions.")
            sys.exit(1)
        
        try:
            self.load_preferences()
        except Exception as e:
            QMessageBox.warning(self, "Preferences Error",
                              "Failed to load preferences. Using defaults.")
            self.preferences = self.get_default_preferences()
        
        try:
            self.apply_theme()
        except Exception as e:
            print(f"Failed to apply theme: {e}")
        
        self.init_ui()
        
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self.check_budget_alerts)
        self.notification_timer.start(3600000)  # Check every hour
        
        current_date = QDate.currentDate().toString("MMMM d, yyyy")
        self.statusBar().showMessage(f"Welcome to Budget Tracker! Today is {current_date}")
        
    def apply_theme(self):
        """Apply theme based on user preferences"""
        theme = self.preferences.get('theme', 'light')
        if theme == 'dark':
            apply_stylesheet(self, theme='dark_blue.xml')
        else:
            apply_stylesheet(self, theme='light_blue.xml')
    
    def backup_database(self):
        """Create a backup of the database before closing"""
        try:
            import shutil
            from datetime import datetime
            
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"budget_backup_{timestamp}.db"
            
            self.conn.close()
            
            shutil.copy2("budget.db", backup_path)
        except Exception as e:
            print(f"Failed to create backup: {e}")
    
    def get_default_preferences(self):
        """Return default preferences"""
        return {
            'theme': 'light',
            'currency': '₹',
            'start_page': 'dashboard',
            'notifications_enabled': True,
            'backup_enabled': True,
            'budget_alert_threshold': 80
        }

    def load_preferences(self):
        """Load user preferences from JSON file"""
        pref_file = Path("preferences.json")
        
        if pref_file.exists():
            with open(pref_file, 'r') as f:
                self.preferences = json.load(f)
        else:
            self.preferences = self.get_default_preferences()
            with open(pref_file, 'w') as f:
                json.dump(self.preferences, f, indent=4)

    def init_db(self):
        """Initialize the database and create tables"""
        db_path = Path("budget.db")
        self.conn = sqlite3.connect(db_path)
        
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                type TEXT CHECK(type IN ('expense', 'income')) NOT NULL,
                budget REAL DEFAULT 0,
                alert_threshold INTEGER DEFAULT 80,
                need_type INTEGER DEFAULT 0,  -- 1 for needs, 0 for wants
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                category_id INTEGER,
                amount REAL NOT NULL CHECK (amount > 0),
                description TEXT,
                type TEXT CHECK(type IN ('expense', 'income')) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
                    ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                target_amount REAL NOT NULL CHECK (target_amount > 0),
                current_amount REAL DEFAULT 0 CHECK (current_amount >= 0),
                target_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                monthly_contribution REAL DEFAULT 0 CHECK (monthly_contribution >= 0)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_fund (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                target_amount REAL NOT NULL CHECK (target_amount > 0),
                current_amount REAL DEFAULT 0 CHECK (current_amount >= 0),
                monthly_contribution REAL DEFAULT 0 CHECK (monthly_contribution >= 0),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                source TEXT NOT NULL,
                is_recurring BOOLEAN DEFAULT 0,
                frequency TEXT CHECK(frequency IN ('monthly', 'quarterly', 'yearly')),
                next_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_income_date ON income(date)")
        
        # Add default categories if none exist
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            default_categories = [
                # Essential expenses (needs)
                ("Housing", "expense", 15000, 1),
                ("Utilities", "expense", 3000, 1),
                ("Groceries", "expense", 8000, 1),
                ("Transportation", "expense", 5000, 1),
                ("Healthcare", "expense", 3000, 1),
                ("Insurance", "expense", 2000, 1),
                
                # Discretionary expenses (wants)
                ("Entertainment", "expense", 5000, 0),
                ("Dining Out", "expense", 4000, 0),
                ("Shopping", "expense", 5000, 0),
                ("Personal Care", "expense", 2000, 0),
                ("Education", "expense", 3000, 0),
                ("Gifts", "expense", 2000, 0),
                
                # Income categories
                ("Salary", "income", 0, 0),
                ("Freelance", "income", 0, 0),
                ("Investments", "income", 0, 0),
                ("Other Income", "income", 0, 0)
            ]
            
            cursor.executemany(
                "INSERT INTO categories (name, type, budget, need_type) VALUES (?, ?, ?, ?)",
                default_categories
            )
            
            # Initialize emergency fund
            cursor.execute("""
                INSERT INTO emergency_fund (id, target_amount, current_amount, monthly_contribution)
                VALUES (1, 100000, 0, 5000)
            """)
            
            self.conn.commit()

    def init_ui(self):
        """Initialize the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create navigation sidebar
        nav_frame = QFrame()
        nav_frame.setObjectName("nav_frame")
        nav_frame.setStyleSheet("""
            QFrame#nav_frame {
                background-color: #2c3e50;
                max-width: 200px;
                min-width: 200px;
            }
            QPushButton {
                color: white;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #3498db;
                font-weight: bold;
            }
        """)
        
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # App title
        title_label = QLabel("Budget Tracker")
        title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            padding: 20px;
        """)
        nav_layout.addWidget(title_label)
        
        # Navigation buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        
        nav_buttons = [
            ("Dashboard", "dashboard"),
            ("Expenses", "expenses"),
            ("Income", "income"),
            ("Budget", "budget"),
            ("Savings", "savings"),
            ("Reports", "reports")
        ]
        
        for text, page in nav_buttons:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("page", page)
            btn.clicked.connect(self.change_page)
            self.nav_group.addButton(btn)
            nav_layout.addWidget(btn)
        
        # Select dashboard by default
        self.nav_group.buttons()[0].setChecked(True)
        
        nav_layout.addStretch()
        
        # Add version info
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            color: #95a5a6;
            padding: 10px;
            font-size: 12px;
        """)
        nav_layout.addWidget(version_label)
        
        layout.addWidget(nav_frame)
        
        # Create stacked widget for pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("""
            QStackedWidget {
                background-color: #ecf0f1;
                padding: 20px;
            }
        """)
        
        # Add pages
        self.pages.addWidget(DashboardPage(self.conn))
        self.pages.addWidget(ExpensePage(self.conn))
        self.pages.addWidget(IncomePage(self.conn))
        self.pages.addWidget(BudgetPage(self.conn))
        self.pages.addWidget(SavingsPage(self.conn))
        self.pages.addWidget(ReportsPage(self.conn))
        
        layout.addWidget(self.pages)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
            }
        """)

    def change_page(self):
        """Change the current page based on navigation selection"""
        button = self.sender()
        page = button.property("page")
        
        page_index = {
            "dashboard": 0,
            "expenses": 1,
            "income": 2,
            "budget": 3,
            "savings": 4,
            "reports": 5
        }.get(page, 0)
        
        self.pages.setCurrentIndex(page_index)
    
    def on_expense_added(self, amount, category, description, expense_type):
        """Handle new expense added from dashboard"""
        self.statusBar().showMessage(
            f"Added {expense_type} expense: ₹{amount:,.2f} for {category}",
            3000
        )
    
    def on_budget_updated(self):
        """Handle budget updated from budget page"""
        self.statusBar().showMessage("Budget updated!", 3000)
    
    def check_budget_alerts(self):
        """Check for budget alerts and notify user"""
        if not self.preferences.get('notifications_enabled', True):
            return
            
        cursor = self.conn.cursor()
        current_month = QDate.currentDate().toString("yyyy-MM")
        
        cursor.execute("""
            SELECT c.name, c.budget, c.alert_threshold,
                   COALESCE(SUM(t.amount), 0) as spent
            FROM categories c
            LEFT JOIN transactions t 
                ON c.id = t.category_id 
                AND strftime('%Y-%m', t.date) = ?
            WHERE c.type = 'expense'
            GROUP BY c.id
            HAVING spent >= (c.budget * c.alert_threshold / 100)
        """, (current_month,))
        
        alerts = cursor.fetchall()
        
        if alerts:
            alert_msg = "Budget Alerts:\n\n"
            for name, budget, threshold, spent in alerts:
                pct = (spent / budget) * 100
                alert_msg += f"• {name}: {pct:.1f}% of budget spent (₹{spent:,.2f} / ₹{budget:,.2f})\n"
            
            QMessageBox.warning(self, "Budget Alerts", alert_msg)

    def closeEvent(self, event):
        """Handle application close event"""
        try:
            if self.preferences.get('backup_enabled', True):
                self.backup_database()
            self.conn.close()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Apply material design theme
    apply_stylesheet(app, theme='light_blue.xml')
    
    window = BudgetTracker()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

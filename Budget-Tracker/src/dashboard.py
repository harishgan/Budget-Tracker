from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QGridLayout, QLineEdit,
                           QComboBox, QSpacerItem, QSizePolicy, QMessageBox,
                           QProgressBar, QMainWindow)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import sqlite3
import time

class DashboardPage(QWidget):
    expense_added = pyqtSignal(float, str, str, str)  # amount, category, description, type

    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        self.cached_data = {}
        self.cache_timeout = 300  # 5 minutes
        self.last_update = None
        
        # Initialize UI first
        self.init_ui()
        
        # Load initial data
        self.load_categories()  # Load categories immediately
        self.load_data()
        
        # Setup auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(60000)  # Refresh every minute

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Top row with overview cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        # Monthly Budget Overview Card
        self.budget_card = self.create_overview_card(
            "Monthly Budget",
            "₹0 / ₹0",
            "budget_progress"
        )
        cards_layout.addWidget(self.budget_card)

        # Emergency Fund Card
        self.emergency_card = self.create_overview_card(
            "Emergency Fund",
            "₹0 / ₹0",
            "emergency_progress"
        )
        cards_layout.addWidget(self.emergency_card)

        # Savings Goals Card
        self.savings_card = self.create_overview_card(
            "Active Savings Goals",
            "0 goals",
            "savings_progress"
        )
        cards_layout.addWidget(self.savings_card)

        # Monthly Income Card
        self.income_card = self.create_overview_card(
            "Monthly Income",
            "₹0",
            "income_progress"
        )
        cards_layout.addWidget(self.income_card)

        layout.addLayout(cards_layout)

        # Middle row with analysis cards
        analysis_layout = QHBoxLayout()
        
        # Top Categories Card
        top_categories = QFrame()
        top_categories.setObjectName("analysis_card")
        top_categories.setStyleSheet("""
            QFrame#analysis_card {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        top_cat_layout = QVBoxLayout(top_categories)
        top_cat_layout.setSpacing(10)
        
        top_cat_title = QLabel("Top Spending Categories")
        top_cat_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_cat_layout.addWidget(top_cat_title)
        
        self.top_categories_list = QLabel()
        self.top_categories_list.setStyleSheet("font-size: 12px;")
        top_cat_layout.addWidget(self.top_categories_list)
        
        analysis_layout.addWidget(top_categories)
        
        # Spending Trends Card
        trends = QFrame()
        trends.setObjectName("analysis_card")
        trends.setStyleSheet("""
            QFrame#analysis_card {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        trends_layout = QVBoxLayout(trends)
        trends_layout.setSpacing(10)
        
        trends_title = QLabel("Spending Trends")
        trends_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        trends_layout.addWidget(trends_title)
        
        self.trends_list = QLabel()
        self.trends_list.setStyleSheet("font-size: 12px;")
        trends_layout.addWidget(self.trends_list)
        
        analysis_layout.addWidget(trends)
        
        # Budget Insights Card
        insights = QFrame()
        insights.setObjectName("analysis_card")
        insights.setStyleSheet("""
            QFrame#analysis_card {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        insights_layout = QVBoxLayout(insights)
        insights_layout.setSpacing(10)
        
        insights_title = QLabel("Budget Insights")
        insights_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        insights_layout.addWidget(insights_title)
        
        self.insights_list = QLabel()
        self.insights_list.setStyleSheet("font-size: 12px;")
        self.insights_list.setWordWrap(True)
        insights_layout.addWidget(self.insights_list)
        
        analysis_layout.addWidget(insights)
        
        layout.addLayout(analysis_layout)

        # Bottom row with charts
        charts_layout = QHBoxLayout()
        
        # Spending Overview Chart
        spending_frame = QFrame()
        spending_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        spending_frame.setMinimumHeight(300)
        spending_layout = QVBoxLayout(spending_frame)
        
        # Create matplotlib figure for spending
        self.spending_figure = Figure(figsize=(6, 4))
        self.spending_canvas = FigureCanvas(self.spending_figure)
        spending_layout.addWidget(self.spending_canvas)
        charts_layout.addWidget(spending_frame)

        # Category Distribution Chart
        category_frame = QFrame()
        category_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        category_frame.setMinimumHeight(300)
        category_layout = QVBoxLayout(category_frame)
        
        # Create matplotlib figure for categories
        self.category_figure = Figure(figsize=(6, 4))
        self.category_canvas = FigureCanvas(self.category_figure)
        category_layout.addWidget(self.category_canvas)
        charts_layout.addWidget(category_frame)

        layout.addLayout(charts_layout)

    def create_overview_card(self, title, initial_value, progress_bar_name):
        """Create an overview card with title, value and progress bar"""
        card = QFrame()
        card.setObjectName("overview_card")
        card.setStyleSheet("""
            QFrame#overview_card {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(initial_value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(value_label)
        
        # Progress Bar
        progress_bar = QProgressBar()
        progress_bar.setObjectName(progress_bar_name)
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        layout.addWidget(progress_bar)
        
        return card

    def load_data(self):
        """Load all dashboard data with caching"""
        try:
            current_time = time.time()
            if (self.last_update is None or 
                current_time - self.last_update > self.cache_timeout):
                
                self.load_budget_overview()
                self.load_emergency_fund()
                self.load_savings_goals()
                self.load_recent_transactions()
                self.load_monthly_income()
                self.load_analysis_data()
                self.update_charts()
                
                self.last_update = current_time
                
            self.update_ui_from_cache()
            
        except Exception as e:
            QMessageBox.warning(self, "Data Load Error",
                              f"Failed to load dashboard data: {str(e)}")

    def load_budget_overview(self):
        """Load budget overview data"""
        cursor = self.conn.cursor()
        current_month = datetime.now().strftime('%Y-%m')
        
        try:
            # Get total budget and spending
            cursor.execute("""
                WITH monthly_budget AS (
                    SELECT SUM(budget) as total_budget
                    FROM categories
                    WHERE type = 'expense'
                ),
                monthly_spending AS (
                    SELECT COALESCE(SUM(amount), 0) as total_spent
                    FROM transactions
                    WHERE type = 'expense'
                    AND strftime('%Y-%m', date) = ?
                )
                SELECT total_budget, total_spent
                FROM monthly_budget, monthly_spending
            """, (current_month,))
            
            result = cursor.fetchone()
            if result:
                total_budget, total_spent = result
                self.cached_data['budget'] = {
                    'total': total_budget or 0,
                    'spent': total_spent or 0,
                    'remaining': (total_budget or 0) - (total_spent or 0)
                }
            
        except sqlite3.Error as e:
            print(f"Database error in budget overview: {e}")
            self.cached_data['budget'] = {'total': 0, 'spent': 0, 'remaining': 0}

    def load_emergency_fund(self):
        """Load emergency fund data"""
        try:
            cursor = self.conn.cursor()
            
            # Calculate 6-month expense projection for NEED categories only
            cursor.execute("""
                WITH monthly_expenses AS (
                    -- Get average monthly expense for each NEED category
                    SELECT 
                        category_id,
                        ROUND(AVG(monthly_total), 2) as avg_monthly_expense
                    FROM (
                        SELECT 
                            t.category_id,
                            strftime('%Y-%m', t.date) as month,
                            SUM(t.amount) as monthly_total
                        FROM transactions t
                        JOIN categories c ON t.category_id = c.id
                        WHERE t.type = 'expense'
                        AND c.need_type = 1  -- Only NEED categories
                        AND t.date >= date('now', '-6 months')
                        GROUP BY t.category_id, month
                    ) monthly_data
                    GROUP BY category_id
                ),
                recurring_expenses AS (
                    -- Get all budgeted amounts from NEED categories
                    SELECT id as category_id, budget as monthly_budget
                    FROM categories
                    WHERE type = 'expense'
                    AND need_type = 1  -- Only NEED categories
                ),
                projected_expenses AS (
                    -- Combine historical averages with budgeted amounts
                    SELECT 
                        COALESCE(me.category_id, re.category_id) as category_id,
                        CASE 
                            WHEN me.avg_monthly_expense IS NOT NULL 
                            THEN me.avg_monthly_expense
                            ELSE re.monthly_budget
                        END as monthly_projection
                    FROM monthly_expenses me
                    FULL OUTER JOIN recurring_expenses re 
                    ON me.category_id = re.category_id
                )
                -- Calculate total 6-month projection
                SELECT ROUND(SUM(monthly_projection) * 6, 2) as six_month_projection
                FROM projected_expenses
            """)
            
            target_amount = cursor.fetchone()[0] or 0
            
            # Get current emergency fund amount
            cursor.execute("""
                SELECT current_amount, monthly_contribution
                FROM emergency_fund
                WHERE id = 1
            """)
            
            result = cursor.fetchone()
            if result:
                current_amount, monthly_contribution = result
            else:
                current_amount = 0
                monthly_contribution = 0
            
            # Update emergency fund target if it differs from projection
            cursor.execute("""
                UPDATE emergency_fund
                SET target_amount = ?
                WHERE id = 1
            """, (target_amount,))
            
            self.conn.commit()
            
            self.cached_data['emergency'] = {
                'target': target_amount,
                'current': current_amount,
                'monthly': monthly_contribution,
                'progress': (current_amount / target_amount * 100) if target_amount > 0 else 0
            }
                
        except sqlite3.Error as e:
            print(f"Database error in emergency fund: {e}")
            self.cached_data['emergency'] = {
                'target': 0, 'current': 0, 'monthly': 0, 'progress': 0
            }

    def load_savings_goals(self):
        """Load savings goals data"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    name,
                    target_amount,
                    current_amount,
                    target_date,
                    monthly_contribution,
                    (current_amount / target_amount * 100) as progress
                FROM savings_goals
                WHERE target_date >= date('now')
                ORDER BY target_date ASC
            """)
            
            goals = cursor.fetchall()
            self.cached_data['savings'] = {
                'goals': goals,
                'total_goals': len(goals),
                'total_saved': sum(goal[2] for goal in goals)
            }
            
        except sqlite3.Error as e:
            print(f"Database error in savings goals: {e}")
            self.cached_data['savings'] = {
                'goals': [], 'total_goals': 0, 'total_saved': 0
            }

    def load_recent_transactions(self):
        """Load recent transactions"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    t.date,
                    c.name as category,
                    t.amount,
                    t.description,
                    t.type
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.id
                ORDER BY t.date DESC, t.id DESC
                LIMIT 10
            """)
            
            self.cached_data['recent_transactions'] = cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Database error in recent transactions: {e}")
            self.cached_data['recent_transactions'] = []

    def load_monthly_income(self):
        """Load monthly income data"""
        try:
            cursor = self.conn.cursor()
            current_month = datetime.now().strftime('%Y-%m')
            
            # Get total monthly income
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as monthly_income
                FROM income
                WHERE strftime('%Y-%m', date) = ?
                   OR (is_recurring = 1 AND frequency = 'monthly')
            """, (current_month,))
            
            monthly_income = cursor.fetchone()[0]
            self.cached_data['income'] = {
                'monthly': monthly_income,
                'recurring': self.get_recurring_income()
            }
            
        except sqlite3.Error as e:
            print(f"Database error in monthly income: {e}")
            self.cached_data['income'] = {'monthly': 0, 'recurring': 0}

    def get_recurring_income(self):
        """Calculate total recurring monthly income"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM income
                WHERE is_recurring = 1 AND frequency = 'monthly'
            """)
            return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0

    def load_analysis_data(self):
        """Load analysis data for insights"""
        try:
            cursor = self.conn.cursor()
            current_month = datetime.now().strftime('%Y-%m')
            
            # Top spending categories
            cursor.execute("""
                SELECT 
                    c.name,
                    SUM(t.amount) as total,
                    COUNT(t.id) as count,
                    (SUM(t.amount) / c.budget * 100) as budget_percent
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE strftime('%Y-%m', t.date) = ?
                GROUP BY c.id
                ORDER BY total DESC
                LIMIT 5
            """, (current_month,))
            
            self.cached_data['top_categories'] = cursor.fetchall()
            
            # Month-over-month trends
            cursor.execute("""
                WITH monthly_totals AS (
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        SUM(amount) as total
                    FROM transactions
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 3
                )
                SELECT 
                    month,
                    total,
                    LAG(total) OVER (ORDER BY month) as prev_total
                FROM monthly_totals
            """)
            
            self.cached_data['trends'] = cursor.fetchall()
            
            # Calculate insights
            insights = []
            
            # Budget utilization insight
            cursor.execute("""
                SELECT 
                    c.name,
                    c.budget,
                    COALESCE(SUM(t.amount), 0) as spent,
                    (COALESCE(SUM(t.amount), 0) / c.budget * 100) as utilization
                FROM categories c
                LEFT JOIN transactions t ON c.id = t.category_id 
                    AND strftime('%Y-%m', t.date) = ?
                WHERE c.type = 'expense'
                GROUP BY c.id
                HAVING utilization > 90 OR utilization < 20
            """, (current_month,))
            
            for category in cursor.fetchall():
                name, budget, spent, utilization = category
                if utilization > 90:
                    insights.append(f"⚠️ {name} is at {utilization:.1f}% of budget")
                elif utilization < 20:
                    insights.append(f"💡 {name} is only at {utilization:.1f}% of budget")
            
            # Savings rate insight
            if 'income' in self.cached_data and self.cached_data['income']['monthly'] > 0:
                savings_rate = ((self.cached_data['income']['monthly'] - 
                               self.cached_data['budget']['spent']) / 
                               self.cached_data['income']['monthly'] * 100)
                if savings_rate < 20:
                    insights.append(f"⚠️ Low savings rate: {savings_rate:.1f}%")
                elif savings_rate > 40:
                    insights.append(f"🎯 Great savings rate: {savings_rate:.1f}%")
            
            self.cached_data['insights'] = insights
            
        except sqlite3.Error as e:
            print(f"Database error in analysis: {e}")
            self.cached_data['top_categories'] = []
            self.cached_data['trends'] = []
            self.cached_data['insights'] = []

    def update_ui_from_cache(self):
        """Update UI elements from cached data"""
        try:
            # Update budget card
            if 'budget' in self.cached_data:
                budget_data = self.cached_data['budget']
                budget_label = self.budget_card.findChild(QLabel, "value_label")
                if budget_label:
                    budget_label.setText(
                        f"₹{budget_data['spent']:,.2f} / ₹{budget_data['total']:,.2f}"
                    )
                
                budget_progress = self.budget_card.findChild(QProgressBar, "budget_progress")
                if budget_progress:
                    progress = (budget_data['spent'] / budget_data['total'] * 100 
                              if budget_data['total'] > 0 else 0)
                    budget_progress.setValue(int(progress))
            
            # Update emergency fund card
            if 'emergency' in self.cached_data:
                emergency_data = self.cached_data['emergency']
                emergency_label = self.emergency_card.findChild(QLabel, "value_label")
                if emergency_label:
                    emergency_label.setText(
                        f"₹{emergency_data['current']:,.2f} / ₹{emergency_data['target']:,.2f}"
                    )
                
                emergency_progress = self.emergency_card.findChild(QProgressBar, "emergency_progress")
                if emergency_progress:
                    emergency_progress.setValue(int(emergency_data['progress']))
            
            # Update savings goals card
            if 'savings' in self.cached_data:
                savings_data = self.cached_data['savings']
                savings_label = self.savings_card.findChild(QLabel, "value_label")
                if savings_label:
                    savings_label.setText(f"{savings_data['total_goals']} goals")
                
                savings_progress = self.savings_card.findChild(QProgressBar, "savings_progress")
                if savings_progress and savings_data['goals']:
                    avg_progress = [(goal[2], goal[1]) for goal in savings_data['goals'] 
                                  if goal[1] > 0]  # current, target pairs
                    if avg_progress:
                        total_progress = sum(curr/target * 100 for curr, target in avg_progress) / len(avg_progress)
                        savings_progress.setValue(int(total_progress))
            
            # Update income card
            if 'income' in self.cached_data:
                income_data = self.cached_data['income']
                income_label = self.income_card.findChild(QLabel, "value_label")
                if income_label:
                    income_label.setText(f"₹{income_data['monthly']:,.2f}")
                
                income_progress = self.income_card.findChild(QProgressBar, "income_progress")
                if income_progress:
                    recurring_percent = (income_data['recurring'] / income_data['monthly'] * 100 
                                      if income_data['monthly'] > 0 else 0)
                    income_progress.setValue(int(recurring_percent))
            
            # Update analysis cards
            if 'top_categories' in self.cached_data:
                top_cats_text = []
                for name, total, count, percent in self.cached_data['top_categories']:
                    top_cats_text.append(f"• {name}: ₹{total:,.2f} ({count} transactions)")
                self.top_categories_list.setText("\n".join(top_cats_text))
            
            if 'trends' in self.cached_data:
                trends_text = []
                for month, total, prev_total in self.cached_data['trends']:
                    month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
                    if prev_total:
                        change = ((total - prev_total) / prev_total * 100)
                        trends_text.append(f"• {month_name}: ₹{total:,.2f} ({change:+.1f}%)")
                    else:
                        trends_text.append(f"• {month_name}: ₹{total:,.2f}")
                self.trends_list.setText("\n".join(trends_text))
            
            if 'insights' in self.cached_data:
                self.insights_list.setText("\n".join(self.cached_data['insights']))
            
        except Exception as e:
            print(f"Error updating UI from cache: {e}")

    def update_charts(self):
        """Update all charts with latest data"""
        try:
            # Clear previous charts
            self.spending_figure.clear()
            self.category_figure.clear()
            
            # Set style
            plt.style.use('bmh')  # Using a built-in style
            
            # Create subplots with white background
            spending_ax = self.spending_figure.add_subplot(111, facecolor='white')
            category_ax = self.category_figure.add_subplot(111, facecolor='white')
            
            # Set figure background to white
            self.spending_figure.patch.set_facecolor('white')
            self.category_figure.patch.set_facecolor('white')
            
            # Spending Trends
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT date, SUM(amount) as daily_total
                FROM transactions
                WHERE type = 'expense'
                AND date >= date('now', '-30 days')
                GROUP BY date
                ORDER BY date
            """)
            
            results = cursor.fetchall()
            if results:
                dates, amounts = zip(*results)
                dates = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
                
                # Plot spending trend
                spending_ax.plot(dates, amounts, marker='o', color='#2196F3', linewidth=2, markersize=6)
                spending_ax.fill_between(dates, amounts, alpha=0.2, color='#2196F3')
                
                # Customize spending chart
                spending_ax.set_title('30-Day Spending Trend', pad=20, fontsize=12, fontweight='bold')
                spending_ax.set_xlabel('Date', labelpad=10)
                spending_ax.set_ylabel('Amount (₹)', labelpad=10)
                spending_ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
                spending_ax.tick_params(axis='x', rotation=45)
                spending_ax.grid(True, linestyle='--', alpha=0.7, color='#cccccc')
                
                # Format y-axis to show amounts in thousands
                spending_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
                
                # Add some padding to the plot
                spending_ax.margins(x=0.05)
            else:
                spending_ax.text(0.5, 0.5, 'No recent transactions',
                               ha='center', va='center', fontsize=12)
            
            # Category Distribution
            cursor.execute("""
                SELECT c.name, SUM(t.amount) as total
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.type = 'expense'
                AND t.date >= date('now', '-30 days')
                GROUP BY c.name
                ORDER BY total DESC
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            if results:
                categories, totals = zip(*results)
                
                # Custom colors for pie chart
                colors = ['#2196F3', '#4CAF50', '#FFC107', '#9C27B0', '#F44336']
                
                # Create pie chart
                wedges, texts, autotexts = category_ax.pie(
                    totals, 
                    labels=categories, 
                    colors=colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    wedgeprops={'width': 0.7}  # Create a donut chart
                )
                
                # Customize pie chart
                category_ax.set_title('Top 5 Expense Categories\n(Last 30 Days)', 
                                    pad=20, fontsize=12, fontweight='bold')
                
                # Enhance the appearance of labels and percentages
                plt.setp(autotexts, size=9, weight="bold", color='black')
                plt.setp(texts, size=10, color='black')
                
                # Add a legend
                category_ax.legend(
                    wedges, categories,
                    title="Categories",
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1)
                )
            else:
                category_ax.text(0.5, 0.5, 'No category data',
                               ha='center', va='center', fontsize=12)
            
            # Adjust layout and display
            self.spending_figure.tight_layout()
            self.category_figure.tight_layout()
            self.spending_canvas.draw()
            self.category_canvas.draw()
            
        except Exception as e:
            print(f"Error updating charts: {e}")
            # Show error message in charts
            for fig, canvas in [(self.spending_figure, self.spending_canvas),
                              (self.category_figure, self.category_canvas)]:
                fig.clear()
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, f'Error loading chart:\n{str(e)}',
                       ha='center', va='center', fontsize=10,
                       wrap=True)
                canvas.draw()

    def show_status_message(self, message, timeout=3000):
        """Show a message in the status bar"""
        # Find the main window by traversing up the widget hierarchy
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        
        if parent and isinstance(parent, QMainWindow):
            parent.statusBar().showMessage(message, timeout)

    def refresh_data(self):
        """Refresh all dashboard data"""
        self.load_data()
        self.load_categories()  # Refresh categories too

    def load_categories(self):
        """Load categories into the combo box"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name 
                FROM categories 
                WHERE type = 'expense'
                ORDER BY name
            """)
            
            categories = cursor.fetchall()
            
            # Store current selection if any
            current_category = None
            
            # Clear and update combo box
            # self.category_combo.clear()
            # self.category_combo.addItem("Select Category")  # Add default option
            
            # # Add categories
            # category_names = [cat[0] for cat in categories]
            # self.category_combo.addItems(category_names)
            
            # # Restore previous selection if valid
            # if current_category in category_names:
            #     index = self.category_combo.findText(current_category)
            #     self.category_combo.setCurrentIndex(index)
            # else:
            #     self.category_combo.setCurrentIndex(0)
            
        except sqlite3.Error as e:
            print(f"Error loading categories: {e}")
            QMessageBox.warning(self, "Error", 
                              "Failed to load expense categories. Please try again.")

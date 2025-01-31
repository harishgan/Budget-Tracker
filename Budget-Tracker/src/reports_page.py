from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QFrame, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sqlite3
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from .utils.colors import *
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ReportsPage(QWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.conn = db_connection
        plt.style.use('bmh')  # Use a clean base style
        plt.rcParams.update(CHART_STYLE)  # Apply our custom style
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header with title and export buttons
        header = QHBoxLayout()
        
        title = QLabel("Financial Reports")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        # CSV Export button
        export_csv_btn = QPushButton("Export as CSV")
        export_csv_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
        """)
        export_csv_btn.clicked.connect(self.export_csv)
        
        # PDF Export button
        export_pdf_btn = QPushButton("Export as PDF")
        export_pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SECONDARY};
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                margin-left: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {SECONDARY_HOVER};
            }}
        """)
        export_pdf_btn.clicked.connect(self.export_pdf)
        
        export_layout.addWidget(export_csv_btn)
        export_layout.addWidget(export_pdf_btn)
        
        header.addStretch()
        header.addLayout(export_layout)
        layout.addLayout(header)
        
        # Time range selector
        range_frame = QFrame()
        range_frame.setObjectName("range_frame")
        range_frame.setStyleSheet(f"""
            QFrame#range_frame {{
                background-color: {BACKGROUND_WHITE};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        range_layout = QHBoxLayout(range_frame)
        
        self.range_combo = QComboBox()
        self.range_combo.addItems(['Last 7 Days', 'Last 30 Days', 'Last 3 Months', 'Last 6 Months', 'Last Year'])
        self.range_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 5px;
                border: 1px solid {TEXT_SECONDARY};
                border-radius: 4px;
                min-width: 150px;
            }}
        """)
        self.range_combo.currentTextChanged.connect(self.update_charts)
        
        range_layout.addWidget(QLabel("Time Range:"))
        range_layout.addWidget(self.range_combo)
        range_layout.addStretch()
        
        layout.addWidget(range_frame)
        
        # Charts container
        charts_layout = QHBoxLayout()
        
        # Spending Trends
        trends_frame = self.create_chart_frame("Spending Trends")
        self.trends_figure = plt.figure(figsize=(8, 6))
        self.trends_canvas = FigureCanvas(self.trends_figure)
        trends_frame.layout().addWidget(self.trends_canvas)
        charts_layout.addWidget(trends_frame)
        
        # Category Distribution
        distribution_frame = self.create_chart_frame("Category Distribution")
        self.distribution_figure = plt.figure(figsize=(8, 6))
        self.distribution_canvas = FigureCanvas(self.distribution_figure)
        distribution_frame.layout().addWidget(self.distribution_canvas)
        charts_layout.addWidget(distribution_frame)
        
        layout.addLayout(charts_layout)
        
        # Income vs Expenses
        comparison_frame = self.create_chart_frame("Income vs Expenses")
        self.comparison_figure = plt.figure(figsize=(12, 6))
        self.comparison_canvas = FigureCanvas(self.comparison_figure)
        comparison_frame.layout().addWidget(self.comparison_canvas)
        layout.addWidget(comparison_frame)
        
        self.update_charts()
        
    def create_chart_frame(self, title):
        frame = QFrame()
        frame.setObjectName("chart_frame")
        frame.setStyleSheet(f"""
            QFrame#chart_frame {{
                background-color: {BACKGROUND_WHITE};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {TEXT_PRIMARY};
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        return frame
        
    def get_date_range(self):
        range_text = self.range_combo.currentText()
        end_date = datetime.now()
        
        if range_text == 'Last 7 Days':
            start_date = end_date - timedelta(days=7)
        elif range_text == 'Last 30 Days':
            start_date = end_date - timedelta(days=30)
        elif range_text == 'Last 3 Months':
            start_date = end_date - timedelta(days=90)
        elif range_text == 'Last 6 Months':
            start_date = end_date - timedelta(days=180)
        else:  # Last Year
            start_date = end_date - timedelta(days=365)
            
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
        
    def update_charts(self):
        try:
            self.update_spending_trends()
            self.update_category_distribution()
            self.update_income_expenses_comparison()
        except Exception as e:
            print(f"Error updating charts: {e}")
            
    def update_spending_trends(self):
        start_date, end_date = self.get_date_range()
        
        # Get daily spending data
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT date, SUM(amount) as daily_total
            FROM transactions
            WHERE type = 'expense'
            AND date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))
        
        results = cursor.fetchall()
        if not results:
            self.show_no_data_message(self.trends_figure)
            self.trends_canvas.draw()
            return
            
        dates, amounts = zip(*results)
        dates = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        
        self.trends_figure.clear()
        ax = self.trends_figure.add_subplot(111)
        
        # Plot spending trend
        ax.plot(dates, amounts, color=PRIMARY, marker='o', linewidth=2, markersize=6)
        ax.fill_between(dates, amounts, alpha=0.2, color=PRIMARY)
        
        # Customize chart
        ax.set_title('Daily Spending Trend', pad=20, fontsize=12, fontweight='bold')
        ax.set_xlabel('Date', labelpad=10)
        ax.set_ylabel('Amount (₹)', labelpad=10)
        
        # Format axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
        ax.tick_params(axis='x', rotation=45)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        
        self.trends_figure.tight_layout()
        self.trends_canvas.draw()
        
    def update_category_distribution(self):
        start_date, end_date = self.get_date_range()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'expense'
            AND t.date BETWEEN ? AND ?
            GROUP BY c.name
            ORDER BY total DESC
            LIMIT 8
        """, (start_date, end_date))
        
        results = cursor.fetchall()
        if not results:
            self.show_no_data_message(self.distribution_figure)
            self.distribution_canvas.draw()
            return
            
        categories, totals = zip(*results)
        
        self.distribution_figure.clear()
        ax = self.distribution_figure.add_subplot(111)
        
        # Create pie chart
        colors = CHART_COLORS[:len(categories)]
        wedges, texts, autotexts = ax.pie(
            totals, 
            labels=categories,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'width': 0.7}  # Create a donut chart
        )
        
        # Customize chart
        plt.setp(autotexts, size=9, weight="bold", color=TEXT_PRIMARY)
        plt.setp(texts, size=10)
        
        ax.set_title('Expense Distribution by Category', pad=20, fontsize=12, fontweight='bold')
        
        # Add legend
        ax.legend(
            wedges, categories,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        
        self.distribution_figure.tight_layout()
        self.distribution_canvas.draw()
        
    def update_income_expenses_comparison(self):
        start_date, end_date = self.get_date_range()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            WITH monthly_totals AS (
                SELECT 
                    strftime('%Y-%m', date) as month,
                    type,
                    SUM(amount) as total
                FROM transactions
                WHERE date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', date), type
            )
            SELECT 
                month,
                MAX(CASE WHEN type = 'income' THEN total ELSE 0 END) as income,
                MAX(CASE WHEN type = 'expense' THEN total ELSE 0 END) as expense
            FROM monthly_totals
            GROUP BY month
            ORDER BY month
        """, (start_date, end_date))
        
        results = cursor.fetchall()
        if not results:
            self.show_no_data_message(self.comparison_figure)
            self.comparison_canvas.draw()
            return
            
        months, incomes, expenses = zip(*results)
        months = [datetime.strptime(m + '-01', '%Y-%m-%d') for m in months]
        
        self.comparison_figure.clear()
        ax = self.comparison_figure.add_subplot(111)
        
        # Plot bars
        bar_width = 0.35
        x = range(len(months))
        
        income_bars = ax.bar([i - bar_width/2 for i in x], incomes, bar_width, 
                           label='Income', color=SECONDARY, alpha=0.7)
        expense_bars = ax.bar([i + bar_width/2 for i in x], expenses, bar_width,
                            label='Expenses', color=WARNING, alpha=0.7)
        
        # Customize chart
        ax.set_title('Monthly Income vs Expenses', pad=20, fontsize=12, fontweight='bold')
        ax.set_xlabel('Month', labelpad=10)
        ax.set_ylabel('Amount (₹)', labelpad=10)
        
        # Format axes
        ax.set_xticks(x)
        ax.set_xticklabels([d.strftime('%b %Y') for d in months], rotation=45)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        
        # Add legend
        ax.legend()
        
        # Add value labels on bars
        def add_value_labels(bars):
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'₹{int(height):,}',
                       ha='center', va='bottom', rotation=0,
                       fontsize=8)
        
        add_value_labels(income_bars)
        add_value_labels(expense_bars)
        
        self.comparison_figure.tight_layout()
        self.comparison_canvas.draw()
        
    def show_no_data_message(self, figure):
        figure.clear()
        ax = figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No data available for selected time range',
               ha='center', va='center', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])

    def export_csv(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Report as CSV", "", "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
                
            if not file_path.endswith('.csv'):
                file_path += '.csv'
                
            start_date, end_date = self.get_date_range()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write report header
                writer.writerow(['Financial Report'])
                writer.writerow([f'Period: {start_date} to {end_date}'])
                writer.writerow([])
                
                # Daily Spending Data
                writer.writerow(['Daily Spending'])
                writer.writerow(['Date', 'Amount'])
                
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT date, SUM(amount) as daily_total
                    FROM transactions
                    WHERE type = 'expense'
                    AND date BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date
                """, (start_date, end_date))
                
                for row in cursor.fetchall():
                    writer.writerow([row[0], f'₹{row[1]:,.2f}'])
                writer.writerow([])
                
                # Category Distribution
                writer.writerow(['Category Distribution'])
                writer.writerow(['Category', 'Total Amount', 'Percentage'])
                
                cursor.execute("""
                    SELECT c.name, SUM(t.amount) as total
                    FROM transactions t
                    JOIN categories c ON t.category_id = c.id
                    WHERE t.type = 'expense'
                    AND t.date BETWEEN ? AND ?
                    GROUP BY c.name
                    ORDER BY total DESC
                """, (start_date, end_date))
                
                category_data = cursor.fetchall()
                total_expenses = sum(row[1] for row in category_data)
                
                for name, amount in category_data:
                    percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                    writer.writerow([name, f'₹{amount:,.2f}', f'{percentage:.1f}%'])
                writer.writerow([])
                
                # Monthly Income vs Expenses
                writer.writerow(['Monthly Income vs Expenses'])
                writer.writerow(['Month', 'Income', 'Expenses', 'Net'])
                
                cursor.execute("""
                    WITH monthly_totals AS (
                        SELECT 
                            strftime('%Y-%m', date) as month,
                            type,
                            SUM(amount) as total
                        FROM transactions
                        WHERE date BETWEEN ? AND ?
                        GROUP BY strftime('%Y-%m', date), type
                    )
                    SELECT 
                        month,
                        MAX(CASE WHEN type = 'income' THEN total ELSE 0 END) as income,
                        MAX(CASE WHEN type = 'expense' THEN total ELSE 0 END) as expense
                    FROM monthly_totals
                    GROUP BY month
                    ORDER BY month
                """, (start_date, end_date))
                
                for month, income, expense in cursor.fetchall():
                    net = income - expense
                    writer.writerow([
                        datetime.strptime(month + '-01', '%Y-%m-%d').strftime('%B %Y'),
                        f'₹{income:,.2f}',
                        f'₹{expense:,.2f}',
                        f'₹{net:,.2f}'
                    ])
                
            QMessageBox.information(self, "Success", "Report exported successfully as CSV!")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export CSV: {str(e)}")
            
    def export_pdf(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Report as PDF", "", "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return
                
            if not file_path.endswith('.pdf'):
                file_path += '.pdf'
                
            start_date, end_date = self.get_date_range()
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=24
            )
            
            # Title
            elements.append(Paragraph("Financial Report", title_style))
            elements.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            cursor = self.conn.cursor()
            
            # Daily Spending
            elements.append(Paragraph("Daily Spending", heading_style))
            
            cursor.execute("""
                SELECT date, SUM(amount) as daily_total
                FROM transactions
                WHERE type = 'expense'
                AND date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
                LIMIT 10
            """, (start_date, end_date))
            
            data = [['Date', 'Amount']]
            for row in cursor.fetchall():
                date = datetime.strptime(row[0], '%Y-%m-%d').strftime('%d %b %Y')
                data.append([date, f'₹{row[1]:,.2f}'])
                
            table = Table(data, colWidths=[4*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))
            
            # Category Distribution
            elements.append(Paragraph("Category Distribution", heading_style))
            
            cursor.execute("""
                SELECT c.name, SUM(t.amount) as total
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.type = 'expense'
                AND t.date BETWEEN ? AND ?
                GROUP BY c.name
                ORDER BY total DESC
            """, (start_date, end_date))
            
            category_data = cursor.fetchall()
            total_expenses = sum(row[1] for row in category_data)
            
            data = [['Category', 'Amount', 'Percentage']]
            for name, amount in category_data:
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                data.append([name, f'₹{amount:,.2f}', f'{percentage:.1f}%'])
                
            table = Table(data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))
            
            # Monthly Income vs Expenses
            elements.append(Paragraph("Monthly Income vs Expenses", heading_style))
            
            cursor.execute("""
                WITH monthly_totals AS (
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        type,
                        SUM(amount) as total
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                    GROUP BY strftime('%Y-%m', date), type
                )
                SELECT 
                    month,
                    MAX(CASE WHEN type = 'income' THEN total ELSE 0 END) as income,
                    MAX(CASE WHEN type = 'expense' THEN total ELSE 0 END) as expense
                FROM monthly_totals
                GROUP BY month
                ORDER BY month
            """, (start_date, end_date))
            
            data = [['Month', 'Income', 'Expenses', 'Net']]
            for month, income, expense in cursor.fetchall():
                net = income - expense
                month_str = datetime.strptime(month + '-01', '%Y-%m-%d').strftime('%B %Y')
                data.append([
                    month_str,
                    f'₹{income:,.2f}',
                    f'₹{expense:,.2f}',
                    f'₹{net:,.2f}'
                ])
                
            table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            QMessageBox.information(self, "Success", "Report exported successfully as PDF!")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export PDF: {str(e)}")

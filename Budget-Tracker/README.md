# Personal Budget Tracker

A modern, feature-rich budget tracking application built with PyQt6 that helps you manage your finances effectively.

## Features

- 📊 Interactive Dashboard with real-time updates
- 💰 Income and Expense tracking
- 🎯 Budget management by categories
- 💹 Savings goals with progress tracking
- 📈 Detailed financial reports and analytics
- 📅 Calendar view for transactions
- 📤 Export data to CSV and PDF formats
- 🌓 Light/Dark theme support

## Installation

1. Make sure you have Python 3.8 or higher installed
2. Clone this repository or download the source code
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Navigate to the project directory:
```bash
cd Budget-Tracker
```

2. Run the application:
```bash
python budget_tracker.py
```

## First Time Setup

1. On first launch, the application will:
   - Create a new database file (budget.db)
   - Generate a default preferences file (preferences.json)
   - Set up default categories for income and expenses

2. You can customize the application by:
   - Adding your income sources
   - Creating expense categories
   - Setting up budget limits
   - Creating savings goals

## Data Storage

- All data is stored locally in a SQLite database (budget.db)
- Automatic backups are created in the 'backups' directory when closing the application
- Preferences are stored in preferences.json

## Troubleshooting

If you encounter any issues:

1. Ensure all dependencies are correctly installed:
```bash
pip install -r requirements.txt --upgrade
```

2. Check if the database file (budget.db) exists and is not corrupted
3. Verify that you have write permissions in the application directory
4. Look for backup files in the 'backups' directory if the main database is corrupted

## License

This project is licensed under the MIT License - see the LICENSE file for details.

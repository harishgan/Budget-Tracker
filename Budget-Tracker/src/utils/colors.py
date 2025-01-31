"""Color utilities for consistent styling across the application"""

# Main brand colors
PRIMARY = "#2196F3"  # Blue
PRIMARY_DARK = "#1976D2"  # Darker Blue
PRIMARY_HOVER = "#1565C0"  # Even Darker Blue for hover

SECONDARY = "#4CAF50"  # Green
SECONDARY_DARK = "#388E3C"  # Darker Green
SECONDARY_HOVER = "#2E7D32"  # Even Darker Green for hover

ACCENT = "#FFC107"  # Amber
WARNING = "#F44336"  # Red
WARNING_DARK = "#D32F2F"  # Darker Red
WARNING_HOVER = "#C62828"  # Even Darker Red for hover
PURPLE = "#9C27B0"  # Purple

# Chart colors
CHART_COLORS = [
    PRIMARY,    # Blue
    SECONDARY,  # Green
    ACCENT,     # Amber
    PURPLE,     # Purple
    WARNING,    # Red
    "#00BCD4",  # Cyan
    "#FF9800",  # Orange
    "#795548",  # Brown
    "#607D8B",  # Blue Grey
    "#E91E63",  # Pink
]

# Background colors
BACKGROUND_WHITE = "#FFFFFF"
BACKGROUND_LIGHT = "#F5F5F5"
BACKGROUND_GREY = "#E0E0E0"
BACKGROUND_DARK = "#212121"

# Text colors
TEXT_PRIMARY = "#212121"
TEXT_SECONDARY = "#757575"
TEXT_DISABLED = "#9E9E9E"

# Status colors
SUCCESS = SECONDARY
SUCCESS_DARK = SECONDARY_DARK
SUCCESS_HOVER = SECONDARY_HOVER
ERROR = WARNING
INFO = PRIMARY

# Chart style configuration
CHART_STYLE = {
    'figure.facecolor': BACKGROUND_WHITE,
    'axes.facecolor': BACKGROUND_WHITE,
    'axes.edgecolor': TEXT_SECONDARY,
    'axes.labelcolor': TEXT_PRIMARY,
    'axes.grid': True,
    'grid.color': '#E0E0E0',
    'grid.linestyle': '--',
    'grid.alpha': 0.7,
    'xtick.color': TEXT_SECONDARY,
    'ytick.color': TEXT_SECONDARY,
    'text.color': TEXT_PRIMARY,
    'font.family': 'Segoe UI',
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 12,
    'axes.titlepad': 20,
    'axes.labelpad': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'grid.alpha': 0.3,
    'grid.color': '#cccccc',
}

def get_color_by_index(index):
    """Get a color from the CHART_COLORS list by index (cycles if index > len)"""
    return CHART_COLORS[index % len(CHART_COLORS)]

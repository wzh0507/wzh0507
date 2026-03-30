import sys
import matplotlib
matplotlib.use('QtAgg')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget,
    QListWidget, QListWidgetItem, QStatusBar, QSplitter,
    QGraphicsOpacityEffect, QSizePolicy,
)
from PyQt6.QtCore import (
    Qt, QDate, QPropertyAnimation, QEasingCurve,
)

from database.db_manager import DatabaseManager
from core.nutrition_calc import completion_score
from ui.year_view import YearView
from ui.month_view import MonthView
from ui.day_view import DayView
from ui.ocr_dialog import OCRDialog
from ui.recipe_dialog import RecipeDialog


# ── Inline views ──────────────────────────────────────────────────────────────

class RecipesListView(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("🍽  All Recipes")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Seed data: 10 recipes loaded at first run")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        self.recipe_list = QListWidget()
        layout.addWidget(self.recipe_list)
        self._load()

    def _load(self):
        self.recipe_list.clear()
        for r in self.db.get_all_recipes():
            text = (
                f"{r['name']}   ·   "
                f"{r['calories']:.0f} kcal  |  "
                f"P {r['protein']:.0f}g  F {r['fat']:.0f}g  C {r['carbs']:.0f}g"
                f"   [{r.get('tags', '')}]"
            )
            self.recipe_list.addItem(QListWidgetItem(text))

    def refresh(self):
        self._load()


class Last7DaysCanvas(FigureCanvasQTAgg):
    def __init__(self, db_manager, parent=None):
        self.fig = Figure(figsize=(6, 3.5), facecolor='#F8F9FA')
        super().__init__(self.fig)
        self.db = db_manager
        self.setParent(parent)
        self._draw()

    def _draw(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('#F8F9FA')
        self.fig.patch.set_facecolor('#F8F9FA')

        today = QDate.currentDate()
        labels = []
        values = []
        colors = []
        for i in range(6, -1, -1):
            d = today.addDays(-i)
            date_str = d.toString("yyyy-MM-dd")
            totals = self.db.get_daily_nutrition(date_str)
            labels.append(d.toString("MM/dd"))
            kcal = totals['calories']
            values.append(kcal)
            colors.append('#4285F4' if kcal > 0 else '#E8EAED')

        bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=1.5)

        # Target line
        ax.axhline(y=2000, color='#EA4335', linestyle='--', linewidth=1.2, label='Target 2000 kcal')
        ax.legend(fontsize=9)

        ax.set_ylabel('kcal', fontsize=10, color='#5F6368')
        ax.set_title('Last 7 Days – Calorie Intake', fontsize=12, color='#202124', pad=10)
        ax.tick_params(colors='#5F6368', labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor('#E8EAED')

        self.fig.tight_layout()
        self.draw()


class AnalyticsView(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("📊  Analytics")
        title.setObjectName("title")
        layout.addWidget(title)

        self.canvas = Last7DaysCanvas(self.db)
        layout.addWidget(self.canvas)
        layout.addStretch()

    def refresh(self):
        self.canvas._draw()


# ── MainWindow ────────────────────────────────────────────────────────────────

# Page indices
PAGE_YEAR = 0
PAGE_MONTH = 1
PAGE_DAY = 2
PAGE_RECIPES = 3
PAGE_ANALYTICS = 4


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nutri-Vision 2026")

        db_path = Path(__file__).parent.parent / "data" / "nutrivision.db"
        self.db = DatabaseManager(db_path)

        self._history: list[int] = []  # page index history for back navigation
        self._build_ui()
        self._connect_signals()
        self.switch_view(PAGE_YEAR)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(4)

        logo = QLabel("Nutri-Vision")
        logo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #4285F4; padding: 8px 4px;"
        )
        sb_layout.addWidget(logo)
        sb_layout.addSpacing(8)

        nav_items = [
            ("📅  Calendar", PAGE_YEAR),
            ("🍽  Recipes", PAGE_RECIPES),
            ("📊  Analytics", PAGE_ANALYTICS),
        ]
        self._nav_buttons: list[QPushButton] = []
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, i=idx: self.switch_view(i))
            sb_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        # OCR button
        ocr_btn = QPushButton("📷  OCR Scanner")
        ocr_btn.setObjectName("nav_btn")
        ocr_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ocr_btn.clicked.connect(self._open_ocr)
        sb_layout.addWidget(ocr_btn)

        sb_layout.addStretch()

        today_btn = QPushButton("Go to Today")
        today_btn.clicked.connect(self._go_today)
        sb_layout.addWidget(today_btn)

        main_layout.addWidget(self.sidebar)

        # Right side: topbar + stack
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(56)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        app_title = QLabel("Nutri-Vision 2026")
        app_title.setObjectName("title")
        tb_layout.addWidget(app_title)
        tb_layout.addStretch()

        today = QDate.currentDate()
        date_label = QLabel(today.toString("dddd, MMMM d, yyyy"))
        date_label.setObjectName("subtitle")
        tb_layout.addWidget(date_label)

        right_layout.addWidget(topbar)

        # Stacked widget
        self.stack = QStackedWidget()

        self.year_view = YearView(self.db, year=2026)
        self.month_view = MonthView(self.db)
        self.day_view = DayView(self.db, self)
        self.recipes_view = RecipesListView(self.db)
        self.analytics_view = AnalyticsView(self.db)

        self.stack.addWidget(self.year_view)    # 0
        self.stack.addWidget(self.month_view)   # 1
        self.stack.addWidget(self.day_view)     # 2
        self.stack.addWidget(self.recipes_view) # 3
        self.stack.addWidget(self.analytics_view)  # 4

        right_layout.addWidget(self.stack)
        main_layout.addWidget(right_widget, stretch=1)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Welcome to Nutri-Vision 2026  ·  Target: 2000 kcal/day")

    # ── Signal connections ────────────────────────────────────────────────────

    def _connect_signals(self):
        self.year_view.month_clicked.connect(self.show_month_view)
        self.month_view.day_clicked.connect(self.show_day_view)
        self.month_view.back_requested.connect(self.go_back)
        self.day_view.back_requested.connect(self.go_back)

    # ── Navigation ────────────────────────────────────────────────────────────

    def switch_view(self, index: int):
        if self.stack.currentIndex() != index:
            self._history.append(self.stack.currentIndex())

        # Refresh the target view
        if index == PAGE_YEAR:
            self.year_view.refresh()
        elif index == PAGE_RECIPES:
            self.recipes_view.refresh()
        elif index == PAGE_ANALYTICS:
            self.analytics_view.refresh()

        self._animate_switch(index)
        self._update_nav_buttons(index)

    def _animate_switch(self, index: int):
        target = self.stack.widget(index)
        effect = QGraphicsOpacityEffect(target)
        target.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.stack.setCurrentIndex(index)
        anim.start()

    def _update_nav_buttons(self, index: int):
        page_to_nav = {PAGE_YEAR: 0, PAGE_RECIPES: 1, PAGE_ANALYTICS: 2}
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(page_to_nav.get(index, -1) == i)

    def show_month_view(self, year: int, month: int):
        self.month_view.set_month(year, month)
        self.switch_view(PAGE_MONTH)

    def show_day_view(self, date_str: str):
        self.day_view.set_date(date_str)
        self.switch_view(PAGE_DAY)

    def go_back(self):
        if self._history:
            prev = self._history.pop()
            self._animate_switch(prev)
            self._update_nav_buttons(prev)
        else:
            self.switch_view(PAGE_YEAR)

    def _open_ocr(self):
        dlg = OCRDialog(self.db, parent=self)
        dlg.exec()
        self.recipes_view.refresh()

    def _go_today(self):
        today = QDate.currentDate()
        date_str = today.toString("yyyy-MM-dd")
        self.show_day_view(date_str)

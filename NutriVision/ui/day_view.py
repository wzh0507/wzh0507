import matplotlib
matplotlib.use('QtAgg')

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSplitter, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate


MEAL_TYPES = [
    ("早餐", "Breakfast"),
    ("午餐", "Lunch"),
    ("晚餐", "Dinner"),
    ("加餐", "Snack"),
]

TARGET_CALORIES = 2000.0


class MealCard(QFrame):
    """Card for a single meal type."""

    add_requested = pyqtSignal(str)        # meal_type
    delete_requested = pyqtSignal(int)     # log_id

    def __init__(self, meal_zh: str, meal_en: str, parent=None):
        super().__init__(parent)
        self.meal_zh = meal_zh
        self.meal_en = meal_en
        self.setObjectName("card")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel(f"{self.meal_zh}  {self.meal_en}")
        title.setObjectName("card_title")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+")
        add_btn.setObjectName("add_btn")
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(lambda: self.add_requested.emit(self.meal_en))
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Container for log entries
        self.entries_layout = QVBoxLayout()
        self.entries_layout.setSpacing(2)
        layout.addLayout(self.entries_layout)

    def set_logs(self, logs: list):
        """Populate this card with log entries."""
        # Clear existing
        while self.entries_layout.count():
            item = self.entries_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not logs:
            placeholder = QLabel("No meals logged")
            placeholder.setStyleSheet("color: #9AA0A6; font-size: 12px;")
            self.entries_layout.addWidget(placeholder)
            return

        for log in logs:
            factor = log.get('actual_intake_grams', 100) / 100.0
            kcal = log.get('calories', 0) * factor
            grams = log.get('actual_intake_grams', 100)
            name = log.get('name', 'Unknown')

            row = QHBoxLayout()
            name_lbl = QLabel(f"{name}  ({grams:.0f}g)")
            name_lbl.setStyleSheet("font-size: 13px; color: #202124;")
            kcal_lbl = QLabel(f"{kcal:.0f} kcal")
            kcal_lbl.setStyleSheet("font-size: 12px; color: #5F6368;")
            del_btn = QPushButton("🗑")
            del_btn.setObjectName("delete_btn")
            del_btn.setFixedSize(26, 26)
            log_id = log['id']
            del_btn.clicked.connect(lambda checked, lid=log_id: self.delete_requested.emit(lid))

            row.addWidget(name_lbl)
            row.addStretch()
            row.addWidget(kcal_lbl)
            row.addWidget(del_btn)

            wrapper = QWidget()
            wrapper.setLayout(row)
            self.entries_layout.addWidget(wrapper)


class NutritionDonutCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(3.5, 3.5), facecolor='#F8F9FA')
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)

    def update_chart(self, protein: float, fat: float, carbs: float, total_kcal: float):
        self.ax.clear()
        self.fig.patch.set_facecolor('#F8F9FA')

        remaining = max(0.0, TARGET_CALORIES - total_kcal)
        sizes = [protein * 4, fat * 9, carbs * 4, remaining]  # kcal per macro
        labels = ['Protein', 'Fat', 'Carbs', '']
        colors = ['#4285F4', '#FBBC04', '#34A853', '#E8EAED']

        if sum(sizes) == 0:
            sizes = [1]
            labels = ['']
            colors = ['#E8EAED']

        wedges, _ = self.ax.pie(
            sizes,
            labels=None,
            colors=colors,
            startangle=90,
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2),
        )

        self.ax.text(
            0, 0,
            f"{total_kcal:.0f}\nkcal",
            ha='center', va='center',
            fontsize=13, fontweight='bold', color='#202124',
        )
        self.ax.set_aspect('equal')

        # Legend
        legend_items = [
            (colors[0], f"Protein  {protein:.1f}g"),
            (colors[1], f"Fat  {fat:.1f}g"),
            (colors[2], f"Carbs  {carbs:.1f}g"),
        ]
        for idx, (color, text) in enumerate(legend_items):
            self.ax.annotate(
                text,
                xy=(0, -1.4 - idx * 0.18),
                ha='center', va='center',
                fontsize=9, color='#5F6368',
                xycoords='data',
            )

        self.fig.tight_layout()
        self.draw()


class DayView(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, db_manager, main_window, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.main_window = main_window
        self.date_str = QDate.currentDate().toString("yyyy-MM-dd")
        self._meal_cards: dict[str, MealCard] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(56)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondary")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(self.back_requested.emit)
        tb_layout.addWidget(back_btn)

        self.date_label = QLabel()
        self.date_label.setObjectName("title")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_layout.addWidget(self.date_label, stretch=1)
        tb_layout.addSpacing(90)

        root.addWidget(topbar)

        # Content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: meal cards in a scroll area
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 16, 10, 16)
        left_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        cards_container = QWidget()
        self.cards_layout = QVBoxLayout(cards_container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)

        for meal_zh, meal_en in MEAL_TYPES:
            card = MealCard(meal_zh, meal_en)
            card.add_requested.connect(self._open_recipe_dialog)
            card.delete_requested.connect(self._delete_log)
            self._meal_cards[meal_en] = card
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
        scroll.setWidget(cards_container)
        left_layout.addWidget(scroll)

        splitter.addWidget(left_widget)

        # Right: donut chart
        right_widget = QWidget()
        right_widget.setMinimumWidth(260)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 16, 20, 16)
        right_layout.setSpacing(8)

        chart_title = QLabel("Today's Nutrition")
        chart_title.setObjectName("card_title")
        chart_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(chart_title)

        self.donut_canvas = NutritionDonutCanvas()
        right_layout.addWidget(self.donut_canvas)
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setSizes([700, 300])

        root.addWidget(splitter)

    def set_date(self, date_str: str):
        self.date_str = date_str
        # Format display: e.g. "Monday, January 1, 2026"
        qdate = QDate.fromString(date_str, "yyyy-MM-dd")
        self.date_label.setText(qdate.toString("dddd, MMMM d, yyyy"))
        self.refresh()

    def refresh(self):
        logs = self.db.get_logs_by_date(self.date_str)

        # Group by meal_type
        grouped: dict[str, list] = {meal_en: [] for _, meal_en in MEAL_TYPES}
        for log in logs:
            mt = log.get('meal_type', 'Breakfast')
            if mt in grouped:
                grouped[mt].append(log)

        for meal_en, card in self._meal_cards.items():
            card.set_logs(grouped.get(meal_en, []))

        # Update chart
        totals = self.db.get_daily_nutrition(self.date_str)
        self.donut_canvas.update_chart(
            protein=totals['protein'],
            fat=totals['fat'],
            carbs=totals['carbs'],
            total_kcal=totals['calories'],
        )

    def _open_recipe_dialog(self, meal_type: str):
        from ui.recipe_dialog import RecipeDialog
        dlg = RecipeDialog(self.db, meal_type, parent=self)
        if dlg.exec():
            recipe_id = dlg.selected_recipe_id
            grams = dlg.selected_grams
            if recipe_id is not None:
                self.db.add_log(self.date_str, meal_type, recipe_id, grams)
                self.refresh()

    def _delete_log(self, log_id: int):
        self.db.delete_log(log_id)
        self.refresh()

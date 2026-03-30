import sys
import calendar
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont


class DayCircleWidget(QLabel):
    """Small colored circle representing a single calendar day."""

    def __init__(self, day: int, score: float, is_today: bool = False, parent=None):
        super().__init__(parent)
        self.day = day
        self.score = score  # 0.0 – 1.0
        self.is_today = is_today
        self.setFixedSize(26, 26)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_style()

    def _apply_style(self):
        if self.day <= 0:
            self.setText("")
            self.setStyleSheet("background: transparent;")
            return

        self.setText(str(self.day))

        if self.score <= 0:
            bg = "#FFFFFF"
            text_color = "#5F6368"
        elif self.score < 0.3:
            bg = "#E3F2FD"
            text_color = "#1565C0"
        elif self.score < 0.6:
            bg = "#90CAF9"
            text_color = "#0D47A1"
        elif self.score < 0.9:
            bg = "#42A5F5"
            text_color = "#FFFFFF"
        else:
            bg = "#1565C0"
            text_color = "#FFFFFF"

        border = "2px solid #4285F4" if self.is_today else "1px solid #E8EAED"
        self.setStyleSheet(
            f"background-color: {bg}; color: {text_color}; border-radius: 13px; "
            f"border: {border}; font-size: 9px; font-weight: {'bold' if self.is_today else 'normal'};"
        )


class MonthMiniCard(QFrame):
    """A small card showing a mini calendar for one month."""

    month_clicked = pyqtSignal(int, int)  # year, month

    def __init__(self, year: int, month: int, db_manager, targets: dict, parent=None):
        super().__init__(parent)
        self.year = year
        self.month = month
        self.db = db_manager
        self.targets = targets
        self.setObjectName("card")
        self.setFixedHeight(190)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        month_name = calendar.month_abbr[self.month]
        title = QLabel(f"{month_name} {self.year}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 11px; font-weight: bold; color: #202124;")
        layout.addWidget(title)

        # Day-of-week headers
        dow_layout = QHBoxLayout()
        dow_layout.setSpacing(2)
        for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(26)
            lbl.setStyleSheet("font-size: 8px; color: #9AA0A6;")
            dow_layout.addWidget(lbl)
        layout.addLayout(dow_layout)

        # Grid placeholder — populated in refresh()
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(2)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.grid_widget)
        layout.addStretch()

    def refresh(self):
        # Clear previous
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        logs = self.db.get_logs_by_month(self.year, self.month)
        # Build score map: day -> score
        from core.nutrition_calc import completion_score
        day_logs: dict[int, list] = {}
        for log in logs:
            day_num = int(log['date'].split('-')[2])
            day_logs.setdefault(day_num, []).append(log)

        today = QDate.currentDate()
        first_dow, num_days = calendar.monthrange(self.year, self.month)
        # Monday=0 in Python, same as Qt Monday

        col = first_dow  # start column (0=Mon)
        row = 0
        for day in range(1, num_days + 1):
            is_today = (today.year() == self.year and today.month() == self.month and today.day() == day)
            sc = completion_score(day_logs.get(day, []), self.targets)
            circle = DayCircleWidget(day, sc, is_today)
            self.grid_layout.addWidget(circle, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def mousePressEvent(self, event):
        self.month_clicked.emit(self.year, self.month)
        super().mousePressEvent(event)


class YearView(QWidget):
    month_clicked = pyqtSignal(int, int)

    def __init__(self, db_manager, year: int = 2026, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.year = year
        self.targets = {'calories': 2000.0}
        self._month_cards: list[MonthMiniCard] = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(16)

        # Title
        title = QLabel(str(self.year))
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        # Scrollable grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(16)
        self.grid.setContentsMargins(0, 0, 0, 0)

        for i in range(12):
            month = i + 1
            card = MonthMiniCard(self.year, month, self.db, self.targets)
            card.month_clicked.connect(self.month_clicked.emit)
            self._month_cards.append(card)
            self.grid.addWidget(card, i // 3, i % 3)

        scroll.setWidget(container)
        root.addWidget(scroll)

    def refresh(self):
        for card in self._month_cards:
            card.refresh()

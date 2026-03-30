import calendar
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor


class DayCell(QFrame):
    clicked = pyqtSignal(str)  # "YYYY-MM-DD"

    def __init__(self, date_str: str, day_num: int, has_logs: bool,
                 is_today: bool, is_current_month: bool, parent=None):
        super().__init__(parent)
        self.date_str = date_str
        self.setFixedHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        num_label = QLabel(str(day_num))
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font_color = "#202124" if is_current_month else "#BDBDBD"
        bg = "#FFFFFF"
        border = "border: none;"

        if is_today:
            border = "border: 2px solid #4285F4; border-radius: 10px;"
            font_color = "#4285F4"
            num_label.setStyleSheet(f"color: {font_color}; font-weight: bold; font-size: 13px;")
        else:
            num_label.setStyleSheet(f"color: {font_color}; font-size: 13px;")

        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: 10px; {border} }}"
            "QFrame:hover { background-color: #F1F3F4; }"
        )
        layout.addWidget(num_label)

        if has_logs:
            dot = QLabel("●")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setStyleSheet("color: #34A853; font-size: 8px;")
            layout.addWidget(dot)

    def mousePressEvent(self, event):
        self.clicked.emit(self.date_str)
        super().mousePressEvent(event)


class MonthView(QWidget):
    day_clicked = pyqtSignal(str)
    back_requested = pyqtSignal()

    def __init__(self, db_manager, year: int = 2026, month: int = 1, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.year = year
        self.month = month
        self._day_cells: list[DayCell] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondary")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)

        header.addStretch()

        prev_btn = QPushButton("‹")
        prev_btn.setObjectName("icon_btn")
        prev_btn.setFixedSize(36, 36)
        prev_btn.clicked.connect(self._prev_month)

        self.month_label = QLabel()
        self.month_label.setObjectName("title")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setMinimumWidth(200)

        next_btn = QPushButton("›")
        next_btn.setObjectName("icon_btn")
        next_btn.setFixedSize(36, 36)
        next_btn.clicked.connect(self._next_month)

        header.addWidget(prev_btn)
        header.addWidget(self.month_label)
        header.addWidget(next_btn)
        header.addStretch()
        root.addLayout(header)

        # Weekday headers
        dow_layout = QHBoxLayout()
        dow_layout.setSpacing(4)
        for day_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            lbl = QLabel(day_name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9AA0A6; font-size: 12px; font-weight: bold;")
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            dow_layout.addWidget(lbl)
        root.addLayout(dow_layout)

        # Calendar grid container
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.grid_container)
        root.addStretch()

    def set_month(self, year: int, month: int):
        self.year = year
        self.month = month
        self.refresh()

    def refresh(self):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._day_cells.clear()

        self.month_label.setText(
            f"{calendar.month_name[self.month]} {self.year}"
        )

        logs = self.db.get_logs_by_month(self.year, self.month)
        days_with_logs = {int(l['date'].split('-')[2]) for l in logs}

        today = QDate.currentDate()
        first_dow, num_days = calendar.monthrange(self.year, self.month)

        col = first_dow
        row = 0

        # Padding cells before first day
        for _ in range(first_dow):
            empty = QWidget()
            self.grid_layout.addWidget(empty, row, _ % 7)

        for day in range(1, num_days + 1):
            date_str = f"{self.year}-{self.month:02d}-{day:02d}"
            is_today = (today.year() == self.year and today.month() == self.month and today.day() == day)
            cell = DayCell(
                date_str=date_str,
                day_num=day,
                has_logs=(day in days_with_logs),
                is_today=is_today,
                is_current_month=True,
            )
            cell.clicked.connect(self.day_clicked.emit)
            self._day_cells.append(cell)
            self.grid_layout.addWidget(cell, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _prev_month(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.refresh()

    def _next_month(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.refresh()

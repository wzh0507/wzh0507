from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QDoubleSpinBox,
    QFrame, QSplitter, QSizePolicy,
)
from PyQt6.QtCore import Qt


class RecipeDialog(QDialog):
    def __init__(self, db_manager, meal_type: str, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.meal_type = meal_type
        self.selected_recipe_id: int | None = None
        self.selected_grams: float = 100.0
        self._all_recipes: list[dict] = []

        self.setWindowTitle(f"Add to {meal_type}")
        self.setMinimumSize(580, 440)
        self._build_ui()
        self._load_recipes()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        title = QLabel(f"Add to  {self.meal_type}")
        title.setObjectName("title")
        root.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: search + list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Filter by name or tags…")
        self.search_edit.textChanged.connect(self._filter_recipes)
        left_layout.addWidget(self.search_edit)

        self.recipe_list = QListWidget()
        self.recipe_list.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.recipe_list)

        splitter.addWidget(left_widget)

        # Right: details panel
        right = QFrame()
        right.setObjectName("card")
        right.setMinimumWidth(200)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(10)

        self.detail_name = QLabel("—")
        self.detail_name.setObjectName("card_title")
        self.detail_name.setWordWrap(True)
        right_layout.addWidget(self.detail_name)

        self.detail_calories = QLabel("Calories: —")
        self.detail_calories.setStyleSheet("color: #5F6368; font-size: 13px;")
        self.detail_protein = QLabel("Protein: —")
        self.detail_protein.setStyleSheet("color: #5F6368; font-size: 13px;")
        self.detail_fat = QLabel("Fat: —")
        self.detail_fat.setStyleSheet("color: #5F6368; font-size: 13px;")
        self.detail_carbs = QLabel("Carbs: —")
        self.detail_carbs.setStyleSheet("color: #5F6368; font-size: 13px;")

        for lbl in [self.detail_calories, self.detail_protein, self.detail_fat, self.detail_carbs]:
            right_layout.addWidget(lbl)

        right_layout.addSpacing(8)

        grams_label = QLabel("Amount (grams):")
        grams_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        right_layout.addWidget(grams_label)

        self.grams_spin = QDoubleSpinBox()
        self.grams_spin.setRange(1.0, 2000.0)
        self.grams_spin.setValue(100.0)
        self.grams_spin.setSuffix(" g")
        self.grams_spin.setSingleStep(10.0)
        right_layout.addWidget(self.grams_spin)
        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([340, 220])
        root.addWidget(splitter)

        # Bottom buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)

        self.add_btn = QPushButton("✓  Add")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.add_btn)
        root.addLayout(btn_row)

    def _load_recipes(self):
        self._all_recipes = self.db.get_all_recipes()
        self._populate_list(self._all_recipes)

    def _populate_list(self, recipes: list[dict]):
        self.recipe_list.clear()
        for recipe in recipes:
            text = f"{recipe['name']}  ·  {recipe['calories']:.0f} kcal"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, recipe['id'])
            self.recipe_list.addItem(item)

    def _filter_recipes(self, text: str):
        text = text.lower().strip()
        if not text:
            self._populate_list(self._all_recipes)
            return
        filtered = [
            r for r in self._all_recipes
            if text in r['name'].lower() or text in (r.get('tags') or '').lower()
        ]
        self._populate_list(filtered)

    def _on_selection_changed(self, current, previous):
        if current is None:
            self.add_btn.setEnabled(False)
            return

        recipe_id = current.data(Qt.ItemDataRole.UserRole)
        recipe = next((r for r in self._all_recipes if r['id'] == recipe_id), None)
        if recipe:
            self.selected_recipe_id = recipe_id
            self.detail_name.setText(recipe['name'])
            self.detail_calories.setText(f"Calories: {recipe['calories']:.0f} kcal / 100g")
            self.detail_protein.setText(f"Protein: {recipe['protein']:.1f} g / 100g")
            self.detail_fat.setText(f"Fat: {recipe['fat']:.1f} g / 100g")
            self.detail_carbs.setText(f"Carbs: {recipe['carbs']:.1f} g / 100g")
            self.add_btn.setEnabled(True)

    def _accept(self):
        self.selected_grams = self.grams_spin.value()
        self.accept()

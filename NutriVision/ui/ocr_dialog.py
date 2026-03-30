from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QFormLayout, QFrame,
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent


class ImageDropZone(QLabel):
    """A QLabel that accepts drag-and-drop image files and click-to-browse."""

    SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path: str | None = None
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_placeholder()

    def _set_placeholder(self):
        exts = "  ".join(e.lstrip('.') for e in self.SUPPORTED_EXTENSIONS)
        self.setText(f"📷  Drop image here or click to browse\n({exts})")
        self.setStyleSheet(
            "QLabel {"
            "  border: 2px dashed #DADCE0;"
            "  border-radius: 12px;"
            "  background-color: #F8F9FA;"
            "  color: #9AA0A6;"
            "  font-size: 13px;"
            "}"
        )

    def _load_image(self, path: str):
        self.image_path = path
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                200, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(pixmap)
            self.setStyleSheet(
                "QLabel {"
                "  border: 2px solid #4285F4;"
                "  border-radius: 12px;"
                "  background-color: #E8F0FE;"
                "}"
            )

    def mousePressEvent(self, event):
        ext_filter = "Images (" + " ".join(f"*{e}" for e in self.SUPPORTED_EXTENSIONS) + ")"
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", ext_filter)
        if path:
            self._load_image(path)
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                suffix = Path(url.toLocalFile()).suffix.lower()
                if suffix in self.SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            suffix = Path(file_path).suffix.lower()
            if suffix in self.SUPPORTED_EXTENSIONS:
                self._load_image(file_path)
                event.acceptProposedAction()
                return
        event.ignore()


class OCRDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("OCR Nutrition Scanner")
        self.setFixedSize(520, 520)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("📷  Scan Nutrition Label")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Drop or select a nutrition label image to auto-extract values")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.drop_zone = ImageDropZone()
        layout.addWidget(self.drop_zone)

        extract_btn = QPushButton("🔍  Extract Nutrition")
        extract_btn.clicked.connect(self._extract)
        layout.addWidget(extract_btn)

        # Editable fields
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.food_name_edit = QLineEdit()
        self.food_name_edit.setPlaceholderText("Food name")
        self.calories_edit = QLineEdit()
        self.calories_edit.setPlaceholderText("0")
        self.protein_edit = QLineEdit()
        self.protein_edit.setPlaceholderText("0")
        self.fat_edit = QLineEdit()
        self.fat_edit.setPlaceholderText("0")
        self.carbs_edit = QLineEdit()
        self.carbs_edit.setPlaceholderText("0")

        form.addRow("Food Name:", self.food_name_edit)
        form.addRow("Calories (kcal):", self.calories_edit)
        form.addRow("Protein (g):", self.protein_edit)
        form.addRow("Fat (g):", self.fat_edit)
        form.addRow("Carbs (g):", self.carbs_edit)
        layout.addLayout(form)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾  Save to Recipes")
        save_btn.clicked.connect(self._save_recipe)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _extract(self):
        if not self.drop_zone.image_path:
            QMessageBox.information(self, "No Image", "Please select or drop an image first.")
            return

        from core.ocr_engine import OCREngine
        engine = OCREngine()
        result = engine.extract_nutrition(self.drop_zone.image_path)

        self.food_name_edit.setText(result.get('food_name', ''))
        self.calories_edit.setText(str(result.get('calories', '')))
        self.protein_edit.setText(str(result.get('protein', '')))
        self.fat_edit.setText(str(result.get('fat', '')))
        self.carbs_edit.setText(str(result.get('carbs', '')))

    def _save_recipe(self):
        name = self.food_name_edit.text().strip() or "Scanned Food"
        try:
            calories = float(self.calories_edit.text() or 0)
            protein = float(self.protein_edit.text() or 0)
            fat = float(self.fat_edit.text() or 0)
            carbs = float(self.carbs_edit.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for nutrition values.")
            return

        self.db.add_recipe(
            name=name,
            ingredients="",
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
            tags="ocr",
        )
        QMessageBox.information(self, "Saved", f'"{name}" has been saved to your recipes.')
        self.accept()

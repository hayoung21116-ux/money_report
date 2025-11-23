from __future__ import annotations
import sys
from pathlib import Path
from typing import Literal, Optional
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QDialog, QFormLayout, QLineEdit, QColorDialog, QComboBox,
    QDateEdit, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QFrame, QTabWidget, QToolTip, QSizePolicy
)
from PySide6.QtCharts import QLineSeries, QValueAxis, QDateTimeAxis, QScatterSeries
from PySide6.QtCore import QRect, QRectF, Qt, QDate, QSize, Signal, QPointF, QDateTime, QMargins
from PySide6.QtGui import QAction, QPalette, QColor, QPixmap, QPainter, QDoubleValidator, QCursor, QFont, QBrush, QPainterPath
from PySide6.QtWidgets import QGraphicsSimpleTextItem, QGraphicsScene
from PySide6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis, QStackedBarSeries

from domain import Account, Transaction, ValuationRecord
from services import format_currency, gen_id
from datetime import datetime, timezone

# ==== UI COMPONENTS ========================================================

class AccountCard(QFrame):
    """Custom widget to display account information in a card format"""
    
    clicked = Signal(str)  # account_id

    def __init__(self, account: Account):
        super().__init__()
        self.account_id = account.id
        self.setup_ui(account)

    def setup_ui(self, account: Account) -> None:
        """Setup the card UI elements and styling"""
        self.setFixedSize(QSize(320, 100))
        self.setFrameShape(QFrame.StyledPanel)
        self.setAutoFillBackground(True)
        
        # 배경색 강제 적용
        palette = self.palette()
        color = "#808080" if account.status == "dead" else account.color
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

        text_color = "white" if color == "#000000" else "black"
        self.setStyleSheet(f"""
            AccountCard {{
                background-color: {color};
                border-radius: 16px;
                color: {text_color};
                font-family: 'NanumSquare', '맑은 고딕', 'Segoe UI', sans-serif;
            }}
            * {{
                background-color: transparent;
                color: {text_color};
            }}
        """)

        # 메인 레이아웃 (좌측 아이콘, 우측 내용)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 10, 16, 10)
        main_layout.setSpacing(12)

        # --- 좌측 아이콘 영역 ---
        icon_label = QLabel()
        source_pixmap = QPixmap()
        if account.image_path:
            loaded_pixmap = QPixmap(account.image_path)
            if not loaded_pixmap.isNull():
                source_pixmap = loaded_pixmap
        
        # Fallback to a default icon or colored circle if no image is loaded
        if source_pixmap.isNull():
            logical_size = 40
            device_pixel_ratio = self.devicePixelRatio()
            if device_pixel_ratio == 0:
                device_pixel_ratio = 1.0

            high_res_size = QSize(logical_size * device_pixel_ratio, logical_size * device_pixel_ratio)
            circular_fallback_pixmap = QPixmap(high_res_size)
            circular_fallback_pixmap.fill(Qt.transparent)
            circular_fallback_pixmap.setDevicePixelRatio(device_pixel_ratio)

            painter = QPainter(circular_fallback_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw the circle
            if (account.type == "소비") or (account.status == "dead"):
                painter.setBrush(QBrush(QColor("white"))) # Force white circle for 소비 & deactivated accounts
            else:
                painter.setBrush(QBrush(QColor(account.color))) # Use account color otherwise
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, logical_size, logical_size)

            # Draw the text
            if (account.type == "소비"):
                painter.setPen(QColor("black")) # Force black text for white circle
            elif (account.status == "dead"):
                painter.setPen(QColor("#808080"))
            else:
                painter.setPen(QColor("white" if QColor(account.color).lightness() < 128 else "black"))
            painter.setFont(QFont("NanumSquare", 16, QFont.Bold))
            painter.drawText(QRect(0, 0, logical_size, logical_size), Qt.AlignCenter, account.name[0] if account.name else "?")
            
            painter.end()
            icon_label.setPixmap(circular_fallback_pixmap)
        else:
            # High-quality rendering for actual images
            logical_size = 40
            device_pixel_ratio = self.devicePixelRatio()
            if device_pixel_ratio == 0: # Should not happen, but safety first
                device_pixel_ratio = 1.0

            # Create a pixmap with high resolution for sharp display
            high_res_size = QSize(logical_size * device_pixel_ratio, logical_size * device_pixel_ratio)
            circular_pixmap = QPixmap(high_res_size)
            circular_pixmap.fill(Qt.transparent) # Fill with transparent color
            circular_pixmap.setDevicePixelRatio(device_pixel_ratio)

            painter = QPainter(circular_pixmap)
            painter.setRenderHint(QPainter.Antialiasing) # Smooth edges for the circle
            painter.setRenderHint(QPainter.SmoothPixmapTransform) # High-quality image scaling

            # Create a circular clipping path
            path = QPainterPath()
            path.addEllipse(0, 0, logical_size, logical_size) # Use logical size for drawing
            painter.setClipPath(path)

            # Calculate source and target rectangles for drawing the image
            # Target is the full logical size of the pixmap (the circle)
            target_rect = QRectF(0, 0, logical_size, logical_size)
            
            # Source rectangle from the original pixmap.
            # We want to scale the pixmap so it covers the target_rect (the circle)
            # while maintaining its aspect ratio. This is "cover" or "aspectfill" mode.
            source_rect = source_pixmap.rect()
            target_aspect = target_rect.width() / target_rect.height()
            source_aspect = source_rect.width() / source_rect.height()

            if source_aspect > target_aspect:
                # Source is wider relative to its height than the target.
                # It will be height-limited. We need to crop the sides.
                new_h = source_rect.height()
                new_w = new_h * target_aspect
                x_offset = (source_rect.width() - new_w) / 2
                source_rect = QRectF(x_offset, 0, new_w, new_h)
            else:
                # Source is taller relative to its width than the target (or same aspect).
                # It will be width-limited. We need to crop the top/bottom.
                new_w = source_rect.width()
                new_h = new_w / target_aspect
                y_offset = (source_rect.height() - new_h) / 2
                source_rect = QRectF(0, y_offset, new_w, new_h)

            painter.drawPixmap(target_rect, source_pixmap, source_rect.toRect())
            painter.end()
            
            icon_label.setPixmap(circular_pixmap)

        icon_label.setFixedSize(40, 40)
        icon_label.setStyleSheet("background-color: transparent;")
        main_layout.addWidget(icon_label, alignment=Qt.AlignVCenter)

        # --- 가운데 텍스트 영역 ---
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        # 계좌 이름
        lbl_name = QLabel(f"{account.name}")
        lbl_name.setStyleSheet("""
            font-family: 'NanumSquare';
            font-weight: 400;
            font-size: 14px;
            background-color: transparent;
        """)
        lbl_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 잔액 or 자산
        if account.type == "투자":
            lbl_bal = QLabel(format_currency(account.asset_value))
        else:
            lbl_bal = QLabel(format_currency(account.balance()))
        
        lbl_bal.setStyleSheet("""
            font-family: 'NanumSquare';
            font-weight: 800;
            font-size: 22px;
            background-color: transparent;
        """)
        lbl_bal.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        text_layout.addWidget(lbl_name)
        text_layout.addWidget(lbl_bal)
        main_layout.addLayout(text_layout)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.account_id)

class AccountDialog(QDialog):
    """Dialog for creating new accounts"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("계좌 추가")
        self.chosen_color = self.generate_random_color()
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the dialog UI components"""
        layout = QFormLayout(self)
        
        # Account name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("계좌명을 입력하세요")
        
        # Account type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["현금", "투자", "소비"])
        
        # Initial balance field
        self.balance_edit = QLineEdit()
        self.balance_edit.setPlaceholderText("0")
        self.balance_edit.setValidator(QDoubleValidator())
        
        # Color picker button
        self.color_btn = QPushButton("색상 선택")
        self.color_btn.clicked.connect(self.choose_color)
        self.update_color_button()

        # Image selector
        self.image_combo = QComboBox()
        self.image_combo.addItem("이미지 없음", "") # Default option for no image
        images_dir = Path("images")
        if images_dir.exists():
            # Search for png, jpg, and jpeg files
            image_files = []
            for ext in ["*.png", "*.jpg", "*.jpeg"]:
                image_files.extend(images_dir.glob(ext))
            
            for image_file in sorted(image_files):
                self.image_combo.addItem(image_file.stem, str(image_file)) # Use filename as text, full path as data
        
        # Add fields to layout
        layout.addRow("계좌명", self.name_edit)
        layout.addRow("계좌 유형", self.type_combo)
        layout.addRow("초기 잔액", self.balance_edit)
        layout.addRow("색상", self.color_btn)
        layout.addRow("이미지", self.image_combo)
        
        # OK button
        btn_ok = QPushButton("추가")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

    def generate_random_color(self) -> str:
        """Generate a random hex color code"""
        import random
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def update_color_button(self) -> None:
        """Update the color button to show the current color"""
        self.color_btn.setStyleSheet(f"""
            background-color: {self.chosen_color};
            color: {'white' if QColor(self.chosen_color).lightness() < 128 else 'black'};
        """)

    def choose_color(self) -> None:
        """Open color picker dialog and update chosen color"""
        color = QColorDialog.getColor(QColor(self.chosen_color), self)
        if color.isValid():
            self.chosen_color = color.name()
            self.update_color_button()

    def get_data(self) -> tuple[str, str, str, float, str]:
        """Get the entered account data from the dialog"""
        try:
            bal = float(self.balance_edit.text() or 0)
        except ValueError:
            raise ValueError("잔액이 숫자가 아닙니다.")
        return (
            self.name_edit.text().strip(),
            self.type_combo.currentText(),
            self.chosen_color,
            bal,
            self.image_combo.currentData() # Get the full path from the selected item's data
        )

class AccountEditDialog(QDialog):
    """Dialog for editing existing accounts"""
    
    def __init__(self, account: Account):
        super().__init__()
        self.setWindowTitle("계좌 수정")
        self.chosen_color = account.color
        self.setup_ui(account)

    def setup_ui(self, account: Account) -> None:
        """Setup the dialog UI components"""
        self.layout = QFormLayout(self)
        
        # Account name field
        self.name_edit = QLineEdit(account.name)
        
        # Account type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["현금", "투자"])
        self.type_combo.setCurrentText(account.type)
        
        # Balance field
        self.balance_edit = QLineEdit(str(account.balance()))
        self.balance_edit.setValidator(QDoubleValidator())

        # Investment specific fields
        self.investment_frame = QFrame()
        self.investment_layout = QFormLayout(self.investment_frame)
        
        self.purchase_amount_edit = QLineEdit(str(account.purchase_amount))
        self.purchase_amount_edit.setValidator(QDoubleValidator())
        self.purchase_amount_edit.setPlaceholderText("총 매입 금액")

        self.cash_holding_edit = QLineEdit(str(account.cash_holding))
        self.cash_holding_edit.setValidator(QDoubleValidator())
        self.cash_holding_edit.setPlaceholderText("보유 현금")

        self.evaluated_amount_edit = QLineEdit(str(account.evaluated_amount))
        self.evaluated_amount_edit.setValidator(QDoubleValidator())
        self.evaluated_amount_edit.setPlaceholderText("현재 평가 금액")

        self.valuation_date_edit = QDateEdit()
        self.valuation_date_edit.setCalendarPopup(True)
        self.valuation_date_edit.setDisplayFormat("yyyy-MM-dd")
        if account.last_valuation_date:
            self.valuation_date_edit.setDate(QDate.fromString(account.last_valuation_date, "yyyy-MM-dd"))
        else:
            self.valuation_date_edit.setDate(QDate.currentDate())
        
        self.investment_layout.addRow("매입 금액", self.purchase_amount_edit)
        self.investment_layout.addRow("보유 현금", self.cash_holding_edit)
        self.investment_layout.addRow("평가 금액", self.evaluated_amount_edit)
        self.investment_layout.addRow("평가 날짜", self.valuation_date_edit)
        
        # Show/hide investment fields based on account type
        self.type_combo.currentTextChanged.connect(self.toggle_investment_fields)
        self.toggle_investment_fields(self.type_combo.currentText())
        
        # Color picker button
        self.color_btn = QPushButton("색상 선택")
        self.color_btn.clicked.connect(self.choose_color)
        self.update_color_button()

        # Image selector
        self.image_combo = QComboBox()
        self.image_combo.addItem("이미지 없음", "") # Default option for no image
        images_dir = Path("images")
        if images_dir.exists():
            current_image_path = Path(account.image_path) if account.image_path else None
            is_current_image_present = current_image_path and current_image_path.exists() and current_image_path.is_file()
            
            if is_current_image_present:
                 self.image_combo.addItem(current_image_path.stem, str(current_image_path))

            # Search for png, jpg, and jpeg files
            image_files = []
            for ext in ["*.png", "*.jpg", "*.jpeg"]:
                image_files.extend(images_dir.glob(ext))

            for image_file in sorted(image_files):
                # Avoid adding the current image again if it was already added above
                if not (is_current_image_present and image_file == current_image_path):
                    self.image_combo.addItem(image_file.stem, str(image_file))
        
        # Set the current image if it exists and was found
        if account.image_path:
            index = self.image_combo.findData(account.image_path)
            if index != -1:
                self.image_combo.setCurrentIndex(index)
            else:
                # If image path is set but not found in the list, it might be an invalid path
                # or an image not in the 'images' directory. Add it as a custom path.
                self.image_combo.addItem(f"기타: {Path(account.image_path).name}", account.image_path)
                self.image_combo.setCurrentIndex(self.image_combo.count() - 1)
        else:
            self.image_combo.setCurrentIndex(0) # "이미지 없음"

        # Add fields to layout
        self.layout.addRow("계좌명", self.name_edit)
        self.layout.addRow("계좌 유형", self.type_combo)
        self.layout.addRow("잔액", self.balance_edit) # This will be hidden for investment accounts
        self.layout.addRow(self.investment_frame) # Add investment fields frame
        self.layout.addRow("색상", self.color_btn)
        self.layout.addRow("이미지", self.image_combo)
        
        # Show/hide balance field based on account type
        self.type_combo.currentTextChanged.connect(self.toggle_balance_field)
        self.toggle_balance_field(self.type_combo.currentText())
        
        # Save button
        btn_ok = QPushButton("저장")
        btn_ok.clicked.connect(self.accept)
        self.layout.addWidget(btn_ok)

    def choose_color(self) -> None:
        """Open color picker dialog and update chosen color"""
        color = QColorDialog.getColor(QColor(self.chosen_color), self)
        if color.isValid():
            self.chosen_color = color.name()
            self.update_color_button()

    def update_color_button(self) -> None:
        """Update the color button to show the current color"""
        self.color_btn.setStyleSheet(f"""
            background-color: {self.chosen_color};
            color: {'white' if QColor(self.chosen_color).lightness() < 128 else 'black'};
        """)

    def toggle_investment_fields(self, account_type: str) -> None:
        """Show or hide investment-specific fields based on account type"""
        self.investment_frame.setVisible(account_type == "투자")

    def toggle_balance_field(self, account_type: str) -> None:
        """Show or hide balance field based on account type"""
        # Find the row index for the "잔액" field
        balance_row_index = -1
        for i in range(self.layout.rowCount()):
            item = self.layout.itemAt(i, QFormLayout.LabelRole)
            if item and item.widget() and item.widget().text() == "잔액":
                balance_row_index = i
                break
        
        if balance_row_index != -1:
            self.layout.itemAt(balance_row_index, QFormLayout.LabelRole).widget().setVisible(account_type != "투자")
            self.layout.itemAt(balance_row_index, QFormLayout.FieldRole).widget().setVisible(account_type != "투자")

    def get_data(self) -> tuple[str, str, float, str, str, float, float, float, str]:
        """Get the edited account data from the dialog"""
        try:
            balance = float(self.balance_edit.text())
            purchase_amount = float(self.purchase_amount_edit.text() or 0.0)
            cash_holding = float(self.cash_holding_edit.text() or 0.0)
            evaluated_amount = float(self.evaluated_amount_edit.text() or 0.0)
            valuation_date_str = self.valuation_date_edit.date().toString("yyyy-MM-dd")
            return (
                self.name_edit.text().strip(),
                self.type_combo.currentText(),
                balance,
                self.chosen_color,
                self.image_combo.currentData(), # Get the full path from the selected item's data
                purchase_amount,
                cash_holding,
                evaluated_amount,
                valuation_date_str
            )
        except ValueError:
            raise ValueError("입력된 값 중 숫자가 아닌 것이 있습니다.")

class TransactionDialog(QDialog):
    """Dialog for adding new transactions"""
    
    def __init__(self, account: Account, service):
        super().__init__()
        self.account = account
        self.service = service
        self.setWindowTitle("거래 추가")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the dialog UI components"""
        vbox = QVBoxLayout(self)
        self.setup_transaction_form(vbox)
        self.setup_action_button(vbox)
        
    def setup_transaction_form(self, parent_layout: QVBoxLayout) -> None:
        """Setup the transaction input form"""
        form = QFormLayout()
        
        # Transaction type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["income", "expense"])
        self.type_combo.currentTextChanged.connect(self.update_category_options)
        
        # Amount
        self.amount_edit = QLineEdit()
        self.amount_edit.setValidator(QDoubleValidator())
        
        # Category
        self.category_combo = QComboBox()
        self.update_category_options()
        
        # Memo
        self.memo_edit = QLineEdit()
        
        # Date
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        
        # Add fields to form
        form.addRow("타입", self.type_combo)
        form.addRow("금액", self.amount_edit)
        form.addRow("카테고리", self.category_combo)
        form.addRow("메모", self.memo_edit)
        form.addRow("날짜", self.date_edit)
        
        parent_layout.addLayout(form)
        
    def setup_action_button(self, parent_layout: QVBoxLayout) -> None:
        """Setup the add transaction button"""
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_txn)
        parent_layout.addWidget(add_btn)

    def update_category_options(self) -> None:
        """Update available categories based on transaction type"""
        self.category_combo.clear()
        if self.type_combo.currentText() == "income":
            if self.account.type == "투자":
                self.category_combo.addItems(["이동", "수익"])
            else:
                self.category_combo.addItems(["저축", "이자", "이동", "대출"])
        else:
            if self.account.type == "투자":
                self.category_combo.addItems(["이동", "손익"])
            else:
                self.category_combo.addItems(["지출", "투자", "이동"])
        self.category_combo.setCurrentIndex(0)

    def add_txn(self) -> None:
        """Add new transaction with validation"""
        try:
            amt = float(self.amount_edit.text())
            if amt < 0:
                raise ValueError("금액은 양수 값이어야 합니다.")
            date_str = self.date_edit.date().toString("yyyy-MM-dd")
            iso_date = f"{date_str}T00:00:00Z"
            
            # Add transaction and get updated account
            self.service.add_transaction(
                self.account.id, 
                self.type_combo.currentText(),
                amt, 
                self.category_combo.currentText(), 
                self.memo_edit.text(), 
                iso_date
            )
            # Get latest account data
            updated_account = self.service.get_account(self.account.id)
            # Update parent's account reference
            if hasattr(self.parent(), 'account'):
                self.parent().account = updated_account
            # Refresh parent table immediately after adding transaction
            if hasattr(self.parent(), 'refresh_table'):
                self.parent().refresh_table()
            # Update parent UI if available
            if hasattr(self.parent(), 'update_ui'):
                self.parent().update_ui()
            self.close()
            
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.warning(self, "에러", f"거래 추가 실패: {str(e)}")

class TransactionTableDialog(QDialog):
    """Dialog for viewing and managing account transactions"""
    
    def __init__(self, account: Account, service):
        super().__init__()
        self.account = account
        self.service = service
        self.current_sort_ascending = False
        self.setWindowTitle(f"{account.name} 거래 내역")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the dialog UI components"""
        vbox = QVBoxLayout(self)
        self.setup_account_info(vbox)
        self.setup_transaction_table(vbox)
        self.setup_action_buttons(vbox)
        
    def setup_account_info(self, parent_layout: QVBoxLayout) -> None:
        """Setup the account information section"""
        account_frame = QFrame()
        account_frame.setFrameShape(QFrame.StyledPanel)
        account_layout = QHBoxLayout(account_frame)
        
        # Account info
        info_layout = QVBoxLayout()
        lbl_name = QLabel(f"{self.account.name} ({self.account.type})")
        lbl_name.setStyleSheet("font-size: 18px; font-weight: bold;")

        if self.account.type == "투자":
            lbl_asset_value = QLabel(f"자산: {format_currency(self.account.asset_value)}")
            lbl_purchase_amount = QLabel(f"매입금액: {format_currency(self.account.purchase_amount)}")
            lbl_evaluated_amount = QLabel(f"평가금액: {format_currency(self.account.evaluated_amount)}")
            
            return_rate_text = f"수익률: {self.account.return_rate:.2f}%"
            if self.account.last_valuation_date:
                return_rate_text += f" ({self.account.last_valuation_date})"
            lbl_return_rate = QLabel(return_rate_text)

            info_layout.addWidget(lbl_name)
            info_layout.addWidget(lbl_asset_value)
            info_layout.addWidget(lbl_purchase_amount)
            info_layout.addWidget(lbl_evaluated_amount)
            info_layout.addWidget(lbl_return_rate)
        else:
            lbl_balance = QLabel(f"잔액: {format_currency(self.account.balance())}")
            info_layout.addWidget(lbl_name)
            info_layout.addWidget(lbl_balance)
        
        account_layout.addLayout(info_layout)
        
        # Account management buttons
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("계좌 수정")
        edit_btn.clicked.connect(self.edit_account)
        deactivate_btn = QPushButton("계좌 활성화" if self.account.status == "dead" else "계좌 비활성화")
        deactivate_btn.clicked.connect(self.deactivate_account)
        delete_btn = QPushButton("계좌 삭제")
        delete_btn.clicked.connect(self.delete_account)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(deactivate_btn)
        btn_layout.addWidget(delete_btn)
        account_layout.addLayout(btn_layout)
        
        parent_layout.addWidget(account_frame)
        
    def setup_transaction_table(self, parent_layout: QVBoxLayout) -> None:
        """Setup the transaction table"""
        self.table = QTableWidget()
        
        if self.account.type == "소비":
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(["타입", "금액", "카테고리", "메모", "날짜", "항목"])
        else:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["타입", "금액", "카테고리", "메모", "날짜"])
            
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.cellDoubleClicked.connect(self.edit_transaction)
        
        self.refresh_table()
        parent_layout.addWidget(self.table)
        
    def setup_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """Setup action buttons for transactions"""
        btn_layout = QHBoxLayout()
        
        # Delete transaction button
        delete_btn = QPushButton("거래 삭제")
        delete_btn.clicked.connect(self.delete_transaction)
        btn_layout.addWidget(delete_btn)

        # Add transaction button
        add_btn = QPushButton("거래 추가")
        add_btn.clicked.connect(self.add_transaction)
        btn_layout.addWidget(add_btn)
        
        # Sort combo box
        sort_combo = QComboBox()
        sort_combo.addItems(["최신순", "오래된순"])
        sort_combo.currentTextChanged.connect(
            lambda text: self.refresh_table(ascending=text == "오래된순")
        )
        btn_layout.addWidget(sort_combo)
        
        parent_layout.addLayout(btn_layout)

    def refresh_table(self, ascending: bool = False) -> None:
        """Refresh the transaction table with current data"""
        self.current_sort_ascending = ascending
        # Get fresh account data from service
        self.account = self.service.get_account(self.account.id)
        # Get transactions from account
        txns = self.account.transactions.copy()
        # Sort transactions by date
        txns.sort(key=lambda t: t.date, reverse=not ascending)
            
        self.table.setRowCount(len(txns))
        for row, t in enumerate(txns):
            self.table.setItem(row, 0, QTableWidgetItem(t.type))
            self.table.setItem(row, 1, QTableWidgetItem(format_currency(t.amount)))
            self.table.setItem(row, 2, QTableWidgetItem(t.category))
            self.table.setItem(row, 3, QTableWidgetItem(t.memo))
            self.table.setItem(row, 4, QTableWidgetItem(t.date))
            if self.account.type == "소비":
                self.table.setItem(row, 5, QTableWidgetItem(t.item))
            
            if t.type == "income" and t.category == "이동":
                light_yellow = QColor("#FFFACD")  # LemonChiffon - 아주 옅은 노란색
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(light_yellow)

    def add_transaction(self) -> None:
        """Open dialog to add a new transaction"""
        dlg = TransactionDialog(self.account, self.service)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_table()
            # Update parent UI if available
            if hasattr(self.parent(), 'update_ui'):
                self.parent().update_ui()

    def edit_account(self) -> None:
        """Open dialog to edit account details"""
        dlg = AccountEditDialog(self.account)
        if dlg.exec() == QDialog.Accepted:
            try:
                # Unpack all values, including new investment ones
                new_name, new_type, new_balance, new_color, new_image_path, new_purchase_amount, new_cash_holding, new_evaluated_amount, new_valuation_date = dlg.get_data()
                if not new_name:
                    QMessageBox.warning(self, "에러", "계좌명을 입력하세요.")
                    return
                
                # Calculate the difference to adjust opening_balance
                balance_diff = new_balance - self.account.balance()
                self.account.opening_balance += balance_diff
                self.account.name = new_name
                self.account.type = new_type
                self.account.color = new_color
                self.account.image_path = new_image_path # Update image path
                
                # Update investment specific fields
                if self.account.type == "투자":
                    self.account.purchase_amount = new_purchase_amount
                    self.account.cash_holding = new_cash_holding
                    self.account.evaluated_amount = new_evaluated_amount
                    self.account.last_valuation_date = new_valuation_date
                
                self.service.update_account(self.account)
                self.setWindowTitle(f"{new_name} 거래 내역")
                self.refresh_table()
                if hasattr(self.parent(), 'update_ui'):
                    self.parent().update_ui()
                    
            except ValueError as e:
                QMessageBox.warning(self, "에러", str(e))
            except Exception as e:
                # Catching generic exception for cases where get_data returns less than 9 values (e.g. for non-investment accounts if not handled carefully)
                # However, get_data now always returns 9 values.
                QMessageBox.warning(self, "에러", f"계좌 수정 중 오류 발생: {str(e)}")

    def delete_account(self) -> None:
        """Handle account deletion with confirmation"""
        reply = QMessageBox.question(
            self,
            "계좌 삭제",
            "정말로 이 계좌를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Close dialog first to avoid reference issues
            self.close()
            # Delete the account
            self.service.delete_account(self.account.id)
            # Update parent UI if available
            if hasattr(self.parent(), 'update_ui'):
                self.parent().update_ui()

    def deactivate_account(self) -> None:
        """Handle account deactivation/activation with confirmation"""
        if self.account.balance() != 0:
            QMessageBox.warning(self, "경고", "잔액이 0이 아닌 계좌는 비활성화할 수 없습니다.")
            return
            
        action = "활성화" if self.account.status == "dead" else "비활성화"
        reply = QMessageBox.question(
            self,
            f"계좌 {action}",
            f"정말로 이 계좌를 {action}하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.service.toggle_account_status(self.account.id)
            self.close()
            # The parent window will handle UI updates when dialog closes

    def delete_transaction(self) -> None:
        """Delete selected transactions with confirmation"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "경고", "삭제할 거래를 선택해주세요")
            return
            
        reply = QMessageBox.question(
            self,
            "거래 삭제",
            "정말로 선택한 거래를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get transactions in same order as table
            txns = sorted(self.account.transactions, 
                         key=lambda t: t.date, 
                         reverse=not self.current_sort_ascending)
            
            # Delete in reverse order to maintain correct indices
            for row in sorted(selected_rows, key=lambda r: r.row(), reverse=True):
                txn_to_delete = txns[row.row()]
                self.account.transactions.remove(txn_to_delete)
            
            self.service.update_account(self.account)
            self.refresh_table()
            if hasattr(self.parent(), 'update_ui'):
                self.parent().update_ui()

    def edit_transaction(self, row: int, column: int) -> None:
        """Edit transaction at specified row"""
        # Get transactions in same order as table
        txns = sorted(self.account.transactions, 
                     key=lambda t: t.date, 
                     reverse=not self.current_sort_ascending)
        txn = txns[row]
        
        dlg = QDialog(self)
        dlg.setWindowTitle("거래 수정")
        
        vbox = QVBoxLayout(dlg)
        form = QFormLayout()
        
        # Transaction type
        type_combo = QComboBox()
        type_combo.addItems(["income", "expense"])
        type_combo.setCurrentText(txn.type)
        
        # Amount
        amount_edit = QLineEdit(str(txn.amount))
        
        # Category
        category_combo = QComboBox()
        
        def update_categories():
            current_category = category_combo.currentText()
            category_combo.clear()
            if type_combo.currentText() == "income":
                categories = ["이동", "수익"] if self.account.type == "투자" else ["저축", "이자", "이동", "대출"]
            else:
                categories = ["지출", "투자", "이동"]
            category_combo.addItems(categories)
            if current_category in categories:
                category_combo.setCurrentText(current_category)
            else:
                category_combo.setCurrentIndex(0)
        
        type_combo.currentTextChanged.connect(update_categories)
        update_categories()
        
        # Memo
        memo_edit = QLineEdit(txn.memo)
        
        # Date
        date_edit = QDateEdit(QDate.fromString(txn.date[:10], "yyyy-MM-dd"))
        date_edit.setCalendarPopup(True)
        
        # Add fields to form
        form.addRow("타입", type_combo)
        form.addRow("금액", amount_edit)
        form.addRow("카테고리", category_combo)
        if self.account.type == "소비":
            item_combo = QComboBox()
            item_combo.addItems(["경조사", "병원", "여행", "기타"])
            item_combo.setCurrentText(txn.item)
            form.addRow("항목", item_combo)
        form.addRow("메모", memo_edit)
        form.addRow("날짜", date_edit)
        
        vbox.addLayout(form)
        
        # Save button
        save_btn = QPushButton("수정")
        save_btn.clicked.connect(dlg.accept)
        vbox.addWidget(save_btn)
        
        if dlg.exec() == QDialog.Accepted:
            try:
                amt = float(amount_edit.text())
                date_str = date_edit.date().toString("yyyy-MM-dd")
                iso_date = f"{date_str}T00:00:00Z"
                
                # Update transaction
                txn.type = type_combo.currentText()
                txn.amount = amt
                txn.category = category_combo.currentText()
                txn.memo = memo_edit.text()
                txn.date = iso_date
                if self.account.type == "소비":
                    txn.item = item_combo.currentText()
                
                self.service.update_account(self.account)
                self.refresh_table()
                if hasattr(self.parent(), 'update_ui'):
                    self.parent().update_ui()
                    
            except ValueError as e:
                QMessageBox.warning(self, "에러", f"잘못된 입력: {str(e)}")
            except Exception as e:
                QMessageBox.warning(self, "에러", str(e))

class SalaryDialog(QDialog):
    """Dialog for adding salary data"""
    
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setWindowTitle("월급 입력")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the dialog UI components"""
        vbox = QVBoxLayout(self)
        self.setup_salary_form(vbox)
        self.setup_action_button(vbox)
        
    def setup_salary_form(self, parent_layout: QVBoxLayout) -> None:
        """Setup the salary input form"""
        form = QFormLayout()
        
        # Month input
        self.month_combo = QComboBox()
        months = [f"{year}-{month:02d}" for year in range(2020, 2030) for month in range(1, 13)]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentText(QDate.currentDate().toString("yyyy-MM"))
        
        # Amount input
        self.amount_edit = QLineEdit()
        self.amount_edit.setValidator(QDoubleValidator())

        # Person input
        self.person_combo = QComboBox()
        self.person_combo.addItems(["민규", "하영"])
        
        # Add fields to form
        form.addRow("월", self.month_combo)
        form.addRow("금액", self.amount_edit)
        form.addRow("이름", self.person_combo)
        
        parent_layout.addLayout(form)
        
    def setup_action_button(self, parent_layout: QVBoxLayout) -> None:
        """Setup the add salary button"""
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_salary)
        parent_layout.addWidget(add_btn)

    def add_salary(self) -> None:
        """Add new salary with validation"""
        try:
            amount = float(self.amount_edit.text())
            if amount < 0:
                raise ValueError("금액은 양수 값이어야 합니다.")
                
            month = self.month_combo.currentText()
            person = self.person_combo.currentText()
            self.service.add_salary(amount, month, person)
            self.close()
            
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", str(e))
        except Exception as e:
            QMessageBox.warning(self, "에러", f"월급 추가 실패: {str(e)}")

class StatsDialog(QDialog):
    """Dialog for displaying monthly financial statistics"""
    
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setWindowTitle("월별 통계")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup the dialog UI components"""
        layout = QVBoxLayout(self)

        # Year selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("연도 선택:"))
        self.year_combo = QComboBox()
        current_year = QDate.currentDate().year()
        for year in range(2020, current_year + 2): # Add next year for future planning
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentTextChanged.connect(self.update_all_tabs)
        selector_layout.addWidget(self.year_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tab pages
        self.portfolio_tab = QWidget()
        self.net_income_tab = QWidget()
        self.savings_tab = QWidget()
        self.salary_tab = QWidget()
        
        # Add tabs
        self.tab_widget.addTab(self.portfolio_tab, "포트폴리오")
        self.tab_widget.addTab(self.net_income_tab, "순수익")
        self.tab_widget.addTab(self.savings_tab, "저축+이자")
        self.tab_widget.addTab(self.salary_tab, "월급")
        
        # Setup tab layouts
        self.setup_portfolio_tab()
        self.setup_net_income_tab()
        self.setup_savings_tab()
        self.setup_salary_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Initial update
        self.update_all_tabs()
        
    def update_all_tabs(self) -> None:
        """Update all tabs based on the selected year"""
        selected_year = self.year_combo.currentText()
        
        # Update Net Income Tab
        self.update_net_income_tab_summary(selected_year)
        self.update_net_income_chart_for_year(selected_year)
        
        # Update Savings Tab
        self.update_savings_tab_summary(selected_year)
        self.update_savings_chart_for_year(selected_year)
        
        # Update Salary Tab
        self.update_salary_tab_summary(selected_year)
        self.update_salary_chart_for_year(selected_year)

        # Update Portfolio Tab
        self.update_portfolio_tab()
        
    def setup_portfolio_tab(self) -> None:
        """Setup portfolio tab with donut chart"""
        layout = QVBoxLayout(self.portfolio_tab)

        # Label for asset amounts above the chart
        self.portfolio_amounts_label = QLabel()
        self.portfolio_amounts_label.setStyleSheet("font-family: 'NanumSquare'; font-size: 14px; padding: 10px;")
        self.portfolio_amounts_label.setWordWrap(True)
        layout.addWidget(self.portfolio_amounts_label)
        
        # Chart
        self.portfolio_chart = QChartView()
        self.portfolio_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.portfolio_chart)
        
    def update_portfolio_tab(self) -> None:
        """Update the portfolio donut chart and amounts label"""
        asset_values = self.calculate_asset_allocation()
        chart = self.create_portfolio_donut_chart(asset_values)
        self.portfolio_chart.setChart(chart)

    def calculate_asset_allocation(self) -> dict[str, float]:
        """Calculate the total value for each asset category"""
        categories = {
            "현금": 0.0,
            "부동산": 0.0,
            "비트코인": 0.0,
            "주식": 0.0,
            "기타": 0.0
        }
        accounts = self.service.list_accounts()
        
        for acc in accounts:
            if acc.status == "dead":
                continue
            
            value = acc.asset_value if acc.type == "투자" else acc.balance()

            if value <= 0:
                continue

            if acc.type == "투자":
                # This is an investment account, categorize it further
                # Categorize investment accounts by name or image path
                account_name_lower = acc.name.lower()
                image_path_lower = Path(acc.image_path).stem.lower() if acc.image_path else ""
                
                if "부동산" in account_name_lower or "부동산" in image_path_lower:
                    categories["부동산"] += value
                elif "비트코인" in account_name_lower or "비트코인" in image_path_lower or "bitcoin" in image_path_lower:
                    categories["비트코인"] += value
                elif any(keyword in account_name_lower or keyword in image_path_lower for keyword in ["주식", "증권", "나무", "한국투자", "ibk", "ok저축은행"]):
                    categories["주식"] += value
                else:
                    categories["기타"] += value
            else:
                # All other non-investment accounts are treated as cash
                categories["현금"] += value
        
        final_categories = {k: v for k, v in categories.items() if v > 0}
        return final_categories # Remove categories with 0 value

    def create_portfolio_donut_chart(self, asset_values: dict[str, float]) -> QChart:
        """Create a donut chart showing asset allocation"""
        from PySide6.QtCharts import QPieSeries, QPieSlice

        chart = QChart()
        chart.setTitle("자산 분포")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(False)
        chart.legend().setFont(QFont("NanumSquare", 9))
        chart.legend().setAlignment(Qt.AlignBottom)

        series = QPieSeries()
        series.setHoleSize(0.35) # This creates the "donut" effect

        colors = {
            "현금": "#4CAF50",  # Green
            "부동산": "#2196F3", # Blue
            "비트코인": "#FF9800", # Amber
            "주식": "#9C27B0",  # Purple
            "기타": "#607D8B"   # Blue Grey
        }

        # First, create and add all slices to the series
        for category, value in asset_values.items():
            # The label for QPieSlice constructor is used for the legend and should only show the category name
            pie_slice = QPieSlice(f"{category}", value)
            pie_slice.setBrush(QColor(colors.get(category, "#000000")))
            series.append(pie_slice)
        
        # After all slices are added, set the labels for the slices themselves
        for pie_slice in series.slices():
            # Set the label text for the slice itself to be the category name and the percentage
            category_name = pie_slice.label() 
            percentage_text = f"{pie_slice.percentage() * 100:.1f}%"
            value_text = f"{format_currency(pie_slice.value())}"
            label_text = f"{category_name}\n{value_text}\n({percentage_text})"
            pie_slice.setLabel(label_text)
            
            # Set label font and color
            pie_slice.setLabelFont(QFont("NanumSquare", 10, QFont.Bold))
            pie_slice.setLabelColor(Qt.black)

            # Adjust label position to be inside the slice
            pie_slice.setLabelArmLengthFactor(0.4) 
            # Make the label visible
            pie_slice.setLabelVisible(True)
            
            # Add hover functionality to show tooltip with slice information
            def handle_slice_hover(status: bool, slice_obj: QPieSlice = pie_slice):
                if not status:
                    QToolTip.hideText()
                    return
                category = slice_obj.label()
                value = format_currency(slice_obj.value())
                percentage = f"{slice_obj.percentage() * 100:.1f}%"
                tooltip_text = f"{category}\n금액: {value}\n비중: {percentage}"
                QToolTip.showText(QCursor.pos(), tooltip_text)
            
            pie_slice.hovered.connect(handle_slice_hover)
            
        chart.addSeries(series)
        return chart

    def setup_net_income_tab(self) -> None:
        """Setup net income tab with chart and summary"""
        layout = QVBoxLayout(self.net_income_tab)

        # Summary label
        self.net_income_summary_label = QLabel()
        self.net_income_summary_label.setStyleSheet("font-family: 'NanumSquare'; font-size: 14px; padding: 10px;")
        self.net_income_summary_label.setWordWrap(True)
        layout.addWidget(self.net_income_summary_label)
        
        # Chart
        self.net_income_chart = QChartView()
        self.net_income_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.net_income_chart)

    def setup_savings_tab(self) -> None:
        """Setup savings tab with chart and summary"""
        layout = QVBoxLayout(self.savings_tab)

        # Summary label
        self.savings_summary_label = QLabel()
        self.savings_summary_label.setStyleSheet("font-family: 'NanumSquare'; font-size: 14px; padding: 10px;")
        self.savings_summary_label.setWordWrap(True)
        layout.addWidget(self.savings_summary_label)
        
        # Chart
        self.savings_chart = QChartView()
        self.savings_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.savings_chart)

    def setup_salary_tab(self) -> None:
        """Setup salary tab with chart and summary"""
        layout = QVBoxLayout(self.salary_tab)

        # Summary label
        self.salary_summary_label = QLabel()
        self.salary_summary_label.setStyleSheet("font-family: 'NanumSquare'; font-size: 14px; padding: 10px;")
        self.salary_summary_label.setWordWrap(True)
        layout.addWidget(self.salary_summary_label)
        
        # Chart
        self.salary_chart = QChartView()
        self.salary_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.salary_chart)

    def update_net_income_tab_summary(self, year: str) -> None:
        """Update net income summary for the selected year"""
        # Calculate net income data for the year
        # This is a placeholder implementation - you should implement actual business logic
        total_income = 0
        total_expense = 0
        
        # Get transactions from all accounts for the selected year
        accounts = self.service.list_accounts()
        for account in accounts:
            for transaction in account.transactions:
                if transaction.date.startswith(year):
                    if transaction.type == "income":
                        total_income += transaction.amount
                    elif transaction.type == "expense":
                        total_expense += transaction.amount
        
        net_income = total_income - total_expense
        
        summary_text = f"{year}년 순수익 요약\n"
        summary_text += f"총 수입: {format_currency(total_income)}\n"
        summary_text += f"총 지출: {format_currency(total_expense)}\n"
        summary_text += f"순수익: {format_currency(net_income)}"
        
        self.net_income_summary_label.setText(summary_text)

    def update_net_income_chart_for_year(self, year: str) -> None:
        """Update net income chart for the selected year"""
        from PySide6.QtCharts import QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
        
        chart = QChart()
        chart.setTitle(f"{year}년 순수익 추이")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create monthly data
        months = ["1월", "2월", "3월", "4월", "5월", "6월", 
                 "7월", "8월", "9월", "10월", "11월", "12월"]
        
        income_set = QBarSet("수입")
        expense_set = QBarSet("지출")
        
        # Calculate monthly income and expenses
        monthly_income = [0] * 12
        monthly_expense = [0] * 12
        
        accounts = self.service.list_accounts()
        for account in accounts:
            for transaction in account.transactions:
                if transaction.date.startswith(year):
                    month = int(transaction.date[5:7]) - 1  # Convert to 0-based index
                    if 0 <= month < 12:
                        if transaction.type == "income":
                            monthly_income[month] += transaction.amount
                        elif transaction.type == "expense":
                            monthly_expense[month] += transaction.amount
        
        income_set.append(monthly_income)
        expense_set.append(monthly_expense)
        
        # Create bar series
        bar_series = QBarSeries()
        bar_series.append(income_set)
        bar_series.append(expense_set)
        
        chart.addSeries(bar_series)
        
        # Setup axes
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        max_value = max(max(monthly_income), max(monthly_expense))
        axis_y.setRange(0, max_value * 1.1)
        chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        self.net_income_chart.setChart(chart)

    def update_savings_tab_summary(self, year: str) -> None:
        """Update savings summary for the selected year"""
        # Calculate savings data for the year
        total_savings = 0
        total_interest = 0
        
        accounts = self.service.list_accounts()
        for account in accounts:
            for transaction in account.transactions:
                if transaction.date.startswith(year):
                    if transaction.type == "income" and transaction.category == "저축":
                        total_savings += transaction.amount
                    elif transaction.type == "income" and transaction.category == "이자":
                        total_interest += transaction.amount
        
        summary_text = f"{year}년 저축+이자 요약\n"
        summary_text += f"저축: {format_currency(total_savings)}\n"
        summary_text += f"이자: {format_currency(total_interest)}\n"
        summary_text += f"합계: {format_currency(total_savings + total_interest)}"
        
        self.savings_summary_label.setText(summary_text)

    def update_savings_chart_for_year(self, year: str) -> None:
        """Update savings chart for the selected year"""
        from PySide6.QtCharts import QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
        
        chart = QChart()
        chart.setTitle(f"{year}년 저축+이자 추이")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create monthly data
        months = ["1월", "2월", "3월", "4월", "5월", "6월", 
                 "7월", "8월", "9월", "10월", "11월", "12월"]
        
        savings_set = QBarSet("저축")
        interest_set = QBarSet("이자")
        
        # Calculate monthly savings and interest
        monthly_savings = [0] * 12
        monthly_interest = [0] * 12
        
        accounts = self.service.list_accounts()
        for account in accounts:
            for transaction in account.transactions:
                if transaction.date.startswith(year):
                    month = int(transaction.date[5:7]) - 1  # Convert to 0-based index
                    if 0 <= month < 12:
                        if transaction.type == "income" and transaction.category == "저축":
                            monthly_savings[month] += transaction.amount
                        elif transaction.type == "income" and transaction.category == "이자":
                            monthly_interest[month] += transaction.amount
        
        savings_set.append(monthly_savings)
        interest_set.append(monthly_interest)
        
        # Create bar series
        bar_series = QBarSeries()
        bar_series.append(savings_set)
        bar_series.append(interest_set)
        
        chart.addSeries(bar_series)
        
        # Setup axes
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        max_value = max(max(monthly_savings), max(monthly_interest))
        axis_y.setRange(0, max_value * 1.1 if max_value > 0 else 1000)
        chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        self.savings_chart.setChart(chart)

    def update_salary_tab_summary(self, year: str) -> None:
        """Update salary summary for the selected year"""
        # Get salary data from service
        # This assumes the service has a method to get salary data
        try:
            # Placeholder implementation - you may need to implement actual salary data retrieval
            total_salary = 0
            salary_count = 0
            
            # This would need to be implemented in your service
            # salaries = self.service.get_salaries_by_year(year)
            # for salary in salaries:
            #     total_salary += salary.amount
            #     salary_count += 1
            
            summary_text = f"{year}년 월급 요약\n"
            summary_text += f"총 월급: {format_currency(total_salary)}\n"
            summary_text += f"지급 횟수: {salary_count}회"
            if salary_count > 0:
                avg_salary = total_salary / salary_count
                summary_text += f"\n평균: {format_currency(avg_salary)}"
            
            self.salary_summary_label.setText(summary_text)
        except Exception as e:
            self.salary_summary_label.setText(f"{year}년 월급 데이터를 불러올 수 없습니다.")

    def update_salary_chart_for_year(self, year: str) -> None:
        """Update salary chart for the selected year"""
        from PySide6.QtCharts import QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
        
        chart = QChart()
        chart.setTitle(f"{year}년 월급 추이")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create monthly data
        months = ["1월", "2월", "3월", "4월", "5월", "6월", 
                 "7월", "8월", "9월", "10월", "11월", "12월"]
        
        salary_set = QBarSet("월급")
        
        # Calculate monthly salary
        monthly_salary = [0] * 12
        
        # This would need to be implemented in your service
        # salaries = self.service.get_salaries_by_year(year)
        # for salary in salaries:
        #     month = int(salary.month[5:7]) - 1  # Convert to 0-based index
        #     if 0 <= month < 12:
        #         monthly_salary[month] += salary.amount
        
        salary_set.append(monthly_salary)
        
        # Create bar series
        bar_series = QBarSeries()
        bar_series.append(salary_set)
        
        chart.addSeries(bar_series)
        
        # Setup axes
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        max_value = max(monthly_salary) if max(monthly_salary) > 0 else 1000
        axis_y.setRange(0, max_value * 1.1)
        chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)
        
        self.salary_chart.setChart(chart)

class ValuationDialog(QDialog):
    """평가 기록 추가 다이얼로그"""
    
    def __init__(self, account: Account):
        super().__init__()
        self.account = account
        self.setWindowTitle("평가 기록 추가")
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """다이얼로그 UI 구성"""
        layout = QFormLayout(self)
        
        # 거래 타입 선택
        self.type_combo = QComboBox()
        self.type_combo.addItems(["매수", "매도", "평가"])
        self.type_combo.currentTextChanged.connect(self.update_dialog_title)
        
        # 평가금액 입력
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("평가금액을 입력하세요")
        self.amount_edit.setValidator(QDoubleValidator())
        
        # 이전 평가금액 표시 (참고용)
        latest_valuation = self.account.latest_valuation
        if latest_valuation:
            previous_amount_label = QLabel(f"이전 평가금액: {format_currency(latest_valuation.evaluated_amount)}")
            layout.addRow(previous_amount_label)
        
        # 평가일 선택
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        
        # 메모 입력
        self.memo_edit = QLineEdit()
        self.memo_edit.setPlaceholderText("평가 사유 또는 메모 (선택사항)")
        
        layout.addRow("거래 타입", self.type_combo)
        layout.addRow("평가금액", self.amount_edit)
        layout.addRow("평가일", self.date_edit)
        layout.addRow("메모", self.memo_edit)
        
        # 추가 버튼
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.accept)
        layout.addWidget(add_btn)
        
        # 초기 타이틀 설정
        self.update_dialog_title()
        
    def update_dialog_title(self) -> None:
        """거래 타입에 따라 다이얼로그 타이틀 업데이트"""
        type_text = self.type_combo.currentText()
        if type_text == "매수":
            self.setWindowTitle("매수 기록 추가")
        elif type_text == "매도":
            self.setWindowTitle("매도 기록 추가")
        else:
            self.setWindowTitle("평가 기록 추가")
        
    def get_data(self) -> tuple[float, str, str, str]:
        """입력된 데이터 반환"""
        try:
            amount = float(self.amount_edit.text())
            if amount < 0:
                raise ValueError("평가금액은 0 이상이어야 합니다.")
        except ValueError:
            raise ValueError("유효한 평가금액을 입력하세요.")
            
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        iso_date = f"{date_str}T00:00:00Z"
        
        memo = self.memo_edit.text().strip()
        
        # 거래 타입 변환
        type_map = {"매수": "buy", "매도": "sell", "평가": "valuation"}
        transaction_type = type_map[self.type_combo.currentText()]
        
        return amount, iso_date, memo, transaction_type

class ValuationChartDialog(QDialog):
    """투자 계좌 자산 평가금액 그래프 다이얼로그"""
    
    def __init__(self, account: Account, service):
        super().__init__()
        self.account = account
        self.service = service
        self.setWindowTitle(f"{account.name} 자산 평가 추이")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """다이얼로그 UI 구성"""
        layout = QVBoxLayout(self)
        
        # 계좌 정보 영역
        self.setup_account_info(layout)
        
        # 그래프 영역
        self.setup_chart(layout)
        
        # 평가 관리 버튼 영역
        self.setup_action_buttons(layout)
        
        # 초기 데이터 로드
        self.update_chart()
        
    def setup_account_info(self, parent_layout: QVBoxLayout) -> None:
        """계좌 정보 표시 영역"""
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QHBoxLayout(info_frame)
        
        # 계좌 기본 정보
        lbl_name = QLabel(f"{self.account.name}")
        lbl_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        latest_valuation = self.account.latest_valuation
        if latest_valuation:
            lbl_current_value = QLabel(f"현재 평가금액: {format_currency(latest_valuation.evaluated_amount)}")
            lbl_last_date = QLabel(f"최근 평가일: {latest_valuation.evaluation_date[:10]}")
            
            # 수익률 계산 및 표시 (Account의 return_rate 속성 사용)
            return_rate = self.account.return_rate
            if return_rate != 0:
                return_rate_text = f"수익률: {return_rate:.2f}%"
                lbl_return_rate = QLabel(return_rate_text)
                
                # 수익률에 따른 색상 지정
                if return_rate > 0:
                    lbl_return_rate.setStyleSheet("color: red;")
                elif return_rate < 0:
                    lbl_return_rate.setStyleSheet("color: blue;")
                else:
                    lbl_return_rate.setStyleSheet("color: black;")
            else:
                lbl_return_rate = QLabel("수익률: -")
        else:
            lbl_current_value = QLabel("현재 평가금액: -")
            lbl_last_date = QLabel("최근 평가일: -")
            lbl_return_rate = QLabel("수익률: -")
        
        info_layout.addWidget(lbl_name)
        info_layout.addWidget(lbl_current_value)
        info_layout.addWidget(lbl_last_date)
        info_layout.addWidget(lbl_return_rate)
        info_layout.addStretch()
        
        parent_layout.addWidget(info_frame)
        
    def setup_chart(self, parent_layout: QVBoxLayout) -> None:
        """그래프 표시 영역"""
        # 차트 뷰 생성
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumSize(700, 400)  # 최소 크기 설정
        self.chart_view.setStyleSheet("background-color: white; border: 1px solid #cccccc;")  # 스타일 설정
        
        parent_layout.addWidget(self.chart_view)
        
    def setup_action_buttons(self, parent_layout: QVBoxLayout) -> None:
        """평가 관리 버튼 영역"""
        button_layout = QHBoxLayout()
        
        # 계좌 수정 버튼
        edit_account_btn = QPushButton("계좌 수정")
        edit_account_btn.clicked.connect(self.edit_account)
        button_layout.addWidget(edit_account_btn)
        
        # 평가 추가 버튼
        add_valuation_btn = QPushButton("평가 추가")
        add_valuation_btn.clicked.connect(self.add_valuation)
        button_layout.addWidget(add_valuation_btn)
        
        # 평가 기간 선택
        self.period_combo = QComboBox()
        self.period_combo.addItems(["전체 기간", "1개월", "3개월", "6개월", "1년"])
        self.period_combo.currentTextChanged.connect(self.update_chart)
        button_layout.addWidget(self.period_combo)
        
        # 자동 평가 버튼
        auto_valuation_btn = QPushButton("자동 평가")
        auto_valuation_btn.clicked.connect(self.auto_valuation)
        button_layout.addWidget(auto_valuation_btn)
        
        button_layout.addStretch()
        parent_layout.addLayout(button_layout)
        
    def update_chart(self, period: str = "전체 기간") -> None:
        """그래프 업데이트"""
        valuations = self.get_filtered_valuations(period)
        chart = self.create_valuation_chart(valuations)
        self.chart_view.setChart(chart)
        
    def get_filtered_valuations(self, period: str) -> list[ValuationRecord]:
        """기간에 따른 평가 기록 필터링"""
        from datetime import datetime, timedelta
        all_valuations = self.service.get_valuations(self.account.id)
        
        # "transaction_type": "valuation"인 기록이 있는지 확인
        valuation_records = [v for v in all_valuations if v.transaction_type == "valuation"]
        
        if valuation_records:
            # 가장 최근의 valuation 기록 찾기
            latest_valuation = max(valuation_records, key=lambda v: v.evaluation_date)
            
            # 가장 최근의 valuation 기록과 그 이후의 모든 기록만 반환
            latest_date = datetime.fromisoformat(latest_valuation.evaluation_date.replace('Z', '+00:00'))
            filtered_valuations = [v for v in all_valuations 
                                 if datetime.fromisoformat(v.evaluation_date.replace('Z', '+00:00')) >= latest_date]
            
            # 기간 필터링 적용
            if period != "전체 기간":
                from datetime import datetime, timedelta
                end_date = datetime.now()
                
                if period == "1개월":
                    start_date = end_date - timedelta(days=30)
                elif period == "3개월":
                    start_date = end_date - timedelta(days=90)
                elif period == "6개월":
                    start_date = end_date - timedelta(days=180)
                elif period == "1년":
                    start_date = end_date - timedelta(days=365)
                else:
                    return filtered_valuations
                    
                return [v for v in filtered_valuations 
                        if datetime.fromisoformat(v.evaluation_date.replace('Z', '+00:00')) >= start_date]
            
            return filtered_valuations
        
        # valuation 기록이 없는 경우 기존 로직 적용
        if period == "전체 기간":
            return all_valuations
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        
        if period == "1개월":
            start_date = end_date - timedelta(days=30)
        elif period == "3개월":
            start_date = end_date - timedelta(days=90)
        elif period == "6개월":
            start_date = end_date - timedelta(days=180)
        elif period == "1년":
            start_date = end_date - timedelta(days=365)
        else:
            return all_valuations
            
        return [v for v in all_valuations 
                if datetime.fromisoformat(v.evaluation_date.replace('Z', '+00:00')) >= start_date]
        
    def create_valuation_chart(self, valuations: list[ValuationRecord]) -> QChart:
        """평가금액 변화 그래프 생성"""
        from PySide6.QtCharts import QLineSeries, QValueAxis, QDateTimeAxis, QScatterSeries, QBarSeries, QBarSet, QBarCategoryAxis
        
        chart = QChart()
        chart.setTitle("자산 평가금액 변화 추이")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 차트 배경 및 테두리 설정
        chart.setBackgroundBrush(QBrush(QColor(255, 255, 255)))  # 흰색 배경
        chart.setMargins(QMargins(10, 10, 10, 10))  # 마진 설정
        chart.layout().setContentsMargins(0, 0, 0, 0)  # 레이아웃 마진 제거
        
        if not valuations:
            # 데이터가 없을 경우 메시지 표시
            from PySide6.QtCharts import QBarSeries, QBarSet, QBarCategoryAxis
            
            # 빈 바 시리즈 생성하여 메시지 표시
            bar_set = QBarSet("데이터 없음")
            bar_set.append([0])  # 높이 0의 바 추가
            
            bar_series = QBarSeries()
            bar_series.append(bar_set)
            
            # 카테고리 축
            category_axis = QBarCategoryAxis()
            category_axis.append(["평가 기록이 없습니다"])
            
            chart.addSeries(bar_series)
            chart.addAxis(category_axis, Qt.AlignBottom)
            bar_series.attachAxis(category_axis)
            
            # Y축 설정
            axis_y = QValueAxis()
            axis_y.setRange(0, 1)
            axis_y.setVisible(False)  # Y축 숨기기
            chart.addAxis(axis_y, Qt.AlignLeft)
            bar_series.attachAxis(axis_y)
            
            # 차트 중앙에 텍스트 추가 - 차트가 생성된 후 타이머로 추가
            from PySide6.QtWidgets import QGraphicsTextItem
            from PySide6.QtCore import QTimer
            
            def add_no_data_text():
                if chart.scene():
                    text_item = QGraphicsTextItem()
                    text_item.setPlainText("평가 기록이 없습니다\n'평가 추가' 버튼을 클릭하여 데이터를 추가하세요")
                    text_item.setDefaultTextColor(QColor("#888888"))
                    text_item.setFont(QFont("NanumSquare", 12))
                    text_item.setTextWidth(300)
                    text_item.setPos(150, 150)  # 차트 중앙 근처에 위치
                    chart.scene().addItem(text_item)
            
            # 차트가 표시된 후 텍스트 추가
            QTimer.singleShot(100, add_no_data_text)
            
            return chart
        
        # 단일 데이터 포인트일 경우 산점도로 명확하게 표시
        if len(valuations) == 1:
            from PySide6.QtCharts import QScatterSeries
            
            scatter = QScatterSeries()
            scatter.setName("평가금액")
            scatter.setColor(QColor("#e74c3c"))  # 빨간색
            scatter.setMarkerSize(15.0)  # 마커 크기 키우기
            scatter.setUseOpenGL(True)
            
            # 데이터 포인트 추가
            valuation = valuations[0]
            date_str = valuation.evaluation_date
            
            if 'T' in date_str and 'Z' in date_str:
                date_time = QDateTime.fromString(date_str, "yyyy-MM-ddThh:mm:ssZ")
            else:
                date_time = QDateTime.fromString(date_str, Qt.ISODate)
            
            if date_time.isValid():
                value = valuation.evaluated_amount
                scatter.append(date_time.toMSecsSinceEpoch(), value)
            
            chart.addSeries(scatter)
            
            # X축 (날짜) 설정
            axis_x = QDateTimeAxis()
            axis_x.setFormat("yyyy-MM-dd")
            axis_x.setTitleText("평가일")
            
            # 단일 날짜를 중심으로 앞뒤로 하루씩 범위 설정
            start_date = date_time.addDays(-1)
            end_date = date_time.addDays(1)
            axis_x.setRange(start_date, end_date)
            
            chart.addAxis(axis_x, Qt.AlignBottom)
            scatter.attachAxis(axis_x)
            
            # Y축 (금액) 설정 - 숫자 표시하지 않음
            axis_y = QValueAxis()
            axis_y.setLabelsVisible(False)  # Y축 레이블 숨기기
            axis_y.setTitleText("")  # Y축 제목 제거
            axis_y.setLineVisible(False)  # Y축 선 숨기기
            
            # Y축 범위 설정 - 0을 포함하도록
            min_y = 0
            max_y = value * 1.2  # 20% 여유
            axis_y.setRange(min_y, max_y)
            
            chart.addAxis(axis_y, Qt.AlignLeft)
            scatter.attachAxis(axis_y)
            
            # 차트 레전드는 숨기기
            chart.legend().setVisible(False)
            
            # 툴팁 추가 - chartView의 이벤트를 사용하여 구현
            def show_tooltip_for_single_point(pos: QPointF):
                # 마우스 위치와 데이터 포인트의 거리 계산
                chart_pos = self.chart_view.chart().mapToValue(pos)
                data_point = QPointF(date_time.toMSecsSinceEpoch(), value)
                
                # 거리 계산 (화면 좌표 기준)
                scene_pos = self.chart_view.mapFromScene(pos)
                data_scene_pos = self.chart_view.chart().mapToPosition(data_point)
                
                # QPointF 연산을 위해 명시적 타입 변환
                scene_x = float(scene_pos.x())
                scene_y = float(scene_pos.y())
                data_x = float(data_scene_pos.x())
                data_y = float(data_scene_pos.y())
                
                distance = abs(scene_x - data_x) + abs(scene_y - data_y)
                
                if distance < 20:  # 20픽셀 이내면 툴팁 표시
                    date_str = valuations[0].evaluation_date[:10]
                    value_str = format_currency(valuations[0].evaluated_amount)
                    memo_str = f"\n메모: {valuations[0].memo}" if valuations[0].memo else ""
                    type_str = {"buy": "매수", "sell": "매도", "valuation": "평가"}.get(valuations[0].transaction_type, "평가")
                    QToolTip.showText(QCursor.pos(), f"{date_str}\n{type_str}\n금액: {value_str}{memo_str}")
                else:
                    QToolTip.hideText()
            
            # ChartView의 마우스 이동 이벤트 연결
            self.chart_view.setMouseTracking(True)
            original_mouse_move_event = self.chart_view.mouseMoveEvent
            
            def mouse_move_event(event):
                if original_mouse_move_event:
                    original_mouse_move_event(event)
                show_tooltip_for_single_point(event.pos())
            
            self.chart_view.mouseMoveEvent = mouse_move_event
            
            # 차트 뷰에 레이블 추가를 위한 타이머 설정
            def add_label_to_chart():
                # 차트 뷰에서 씬 가져오기
                scene = self.chart_view.scene()
                if scene:
                    # 차트의 좌표계를 씬의 좌표계로 변환
                    chart_rect = self.chart_view.chart().plotArea()
                    chart_pos = QPointF(date_time.toMSecsSinceEpoch(), value)
                    
                    # 차트 내에서의 상대적 위치 계산 (0.0 ~ 1.0)
                    x_axis = chart.axisX()
                    y_axis = chart.axisY()
                    
                    x_min = x_axis.min()
                    x_max = x_axis.max()
                    y_min = y_axis.min()
                    y_max = y_axis.max()
                    
                    # 상대적 위치 계산
                    chart_x = float(chart_pos.x())
                    chart_y = float(chart_pos.y())
                    rel_x = (chart_x - x_min) / (x_max - x_min)
                    rel_y = 1.0 - (chart_y - y_min) / (y_max - y_min)  # Y축은 반대
                    
                    # 씬 좌표로 변환
                    scene_x = chart_rect.left() + rel_x * chart_rect.width()
                    scene_y = chart_rect.top() + rel_y * chart_rect.height()
                    
                    # 금액 레이블 생성
                    value_text = scene.addText(format_currency(value))
                    value_text.setFont(QFont("NanumSquare", 10, QFont.Bold))
                    value_text.setDefaultTextColor(QColor("#333333"))
                    
                    # 레이블 위치 조정 (데이터 포인트 위쪽)
                    text_rect = value_text.boundingRect()
                    label_x = scene_x - text_rect.width() / 2
                    label_y = scene_y - text_rect.height() - 5  # 5px 위쪽
                    value_text.setPos(label_x, label_y)
            
            # 차트가 표시된 후 레이블 추가
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, add_label_to_chart)
            
        else:
            # 여러 데이터 포인트일 경우 매수/매도 pair를 식별하여 표시
            
            # Trade pair 가져오기
            trade_pairs = self.service.get_trade_pairs(self.account.id)
            
            # 전체 추세선 추가 (모든 점을 연결하는 회색 선)
            line_series = QLineSeries()
            line_series.setName("추세선")
            line_series.setColor(QColor("#95a5a6"))  # 회색 선
            line_series.setUseOpenGL(True)
            
            # 라인 그래프에 데이터 포인트 추가
            for valuation in valuations:
                date_str = valuation.evaluation_date
                if 'T' in date_str and 'Z' in date_str:
                    date_time = QDateTime.fromString(date_str, "yyyy-MM-ddThh:mm:ssZ")
                else:
                    date_time = QDateTime.fromString(date_str, Qt.ISODate)
                
                if date_time.isValid():
                    value = valuation.evaluated_amount
                    line_series.append(date_time.toMSecsSinceEpoch(), value)
            
            chart.addSeries(line_series)
            
            
            # X축 (날짜) 설정
            axis_x = QDateTimeAxis()
            axis_x.setFormat("yyyy-MM-dd")
            axis_x.setTitleText("평가일")
            
            start_date_str = valuations[0].evaluation_date
            end_date_str = valuations[-1].evaluation_date
            
            start_date = QDateTime.fromString(start_date_str, Qt.ISODate)
            end_date = QDateTime.fromString(end_date_str, Qt.ISODate)
            
            if start_date.isValid() and end_date.isValid():
                axis_x.setRange(start_date, end_date)
            
            # Y축 (금액) 설정
            axis_y = QValueAxis()
            axis_y.setLabelFormat("%.0f")
            axis_y.setTitleText("평가금액 (원)")
            
            values = [v.evaluated_amount for v in valuations]
            min_value = min(values)
            max_value = max(values)
            padding = (max_value - min_value) * 0.1  # 10% padding
            y_min = max(0, min_value - padding)
            y_max = max_value + padding
            
            axis_y.setRange(y_min, y_max)
            
            # 축을 차트에 추가
            chart.addAxis(axis_x, Qt.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignLeft)
            
            # 라인 시리즈에 축 연결
            line_series.attachAxis(axis_x)
            line_series.attachAxis(axis_y)
            
            # 각 페어별로 연결선 추가 (모든 페어는 매수/매도 쌍으로 완료됨)
            for i, pair in enumerate(trade_pairs):
                    pair_line = QLineSeries()
                    pair_line.setName(f"Pair {i+1}")
                    
                    # 수익률에 따른 선 색상 지정
                    if pair.return_rate > 0:
                        pair_line.setColor(QColor("#e74c3c"))  # 빨간색 (수익)
                    elif pair.return_rate < 0:
                        pair_line.setColor(QColor("#3498db"))  # 파란색 (손실)
                    else:
                        pair_line.setColor(QColor("#95a5a6"))  # 회색 (변동 없음)
                    
                    pair_line.setUseOpenGL(True)
                    # QLineSeries는 setWidth() 메소드가 없음, 대신 setPen()을 사용하여 선 스타일 설정
                    from PySide6.QtGui import QPen
                    pen = QPen(pair_line.color())
                    pen.setWidth(3)  # 선 굵기 설정
                    pair_line.setPen(pen)
                    
                    # 매수 지점
                    buy_date_str = pair.buy_valuation.evaluation_date
                    buy_date_time = QDateTime.fromString(buy_date_str, Qt.ISODate)
                    buy_value = pair.buy_valuation.evaluated_amount
                    
                    # 매도 지점
                    sell_date_str = pair.sell_valuation.evaluation_date
                    sell_date_time = QDateTime.fromString(sell_date_str, Qt.ISODate)
                    sell_value = pair.sell_valuation.evaluated_amount
                    
                    if buy_date_time.isValid() and sell_date_time.isValid():
                        # 페어 연결선에 데이터 포인트 추가
                        pair_line.append(buy_date_time.toMSecsSinceEpoch(), buy_value)
                        pair_line.append(sell_date_time.toMSecsSinceEpoch(), sell_value)
                        
                        chart.addSeries(pair_line)
                        pair_line.attachAxis(axis_x)
                        pair_line.attachAxis(axis_y)
                        
                        # 페어 연결선 정보 저장 (마우스 이동 이벤트에서 사용)
                        pair_line.setProperty("pair_data", pair)
            
            # 각 포인트마다 다른 색상의 산점도 추가 (매수: 빨간색, 매도: 파란색)
            for i, valuation in enumerate(valuations):
                scatter = QScatterSeries()
                scatter.setName(f"평가금액 {i+1}")
                
                # 거래 타입에 따른 색상 지정
                if valuation.transaction_type == "buy":
                    color = "#e74c3c"  # 빨간색 (매수)
                elif valuation.transaction_type == "sell":
                    color = "#3498db"  # 파란색 (매도)
                else:
                    color = "#2ecc71"  # 초록색 (평가)
                
                scatter.setColor(QColor(color))
                scatter.setMarkerSize(12.0)
                scatter.setUseOpenGL(True)
                scatter.setBorderColor(QColor(color))
                
                # 날짜 형식을 명시적으로 지정하여 파싱
                date_str = valuation.evaluation_date
                if 'T' in date_str and 'Z' in date_str:
                    date_time = QDateTime.fromString(date_str, "yyyy-MM-ddThh:mm:ssZ")
                else:
                    date_time = QDateTime.fromString(date_str, Qt.ISODate)
                
                if date_time.isValid():
                    value = valuation.evaluated_amount
                    scatter.append(date_time.toMSecsSinceEpoch(), value)
                
                chart.addSeries(scatter)
                scatter.attachAxis(axis_x)
                scatter.attachAxis(axis_y)
                
                # 각 포인트에 툴팁 추가 - chartView의 이벤트를 사용하여 구현
                def show_tooltip_for_point(pos: QPointF, valuation_data=valuation):
                    # 마우스 위치와 데이터 포인트의 거리 계산
                    chart_pos = self.chart_view.chart().mapToValue(pos)
                    
                    # 날짜 형식을 명시적으로 지정하여 파싱
                    date_str = valuation_data.evaluation_date
                    if 'T' in date_str and 'Z' in date_str:
                        date_time = QDateTime.fromString(date_str, "yyyy-MM-ddThh:mm:ssZ")
                    else:
                        date_time = QDateTime.fromString(date_str, Qt.ISODate)
                    
                    if date_time.isValid():
                        value = valuation_data.evaluated_amount
                        data_point = QPointF(date_time.toMSecsSinceEpoch(), value)
                        
                        # 거리 계산 (화면 좌표 기준)
                        scene_pos = self.chart_view.mapFromScene(pos)
                        data_scene_pos = self.chart_view.chart().mapToPosition(data_point)
                        
                        # QPoint 연산을 위해 개별 좌표 추출
                        scene_x = scene_pos.x()
                        scene_y = scene_pos.y()
                        data_x = data_scene_pos.x()
                        data_y = data_scene_pos.y()
                        
                        # 맨해튼 거리 계산
                        distance = abs(scene_x - data_x) + abs(scene_y - data_y)
                        
                        if distance < 20:  # 20픽셀 이내면 툴팁 표시
                            date_str = valuation_data.evaluation_date[:10]
                            value_str = format_currency(valuation_data.evaluated_amount)
                            memo_str = f"\n메모: {valuation_data.memo}" if valuation_data.memo else ""
                            type_str = {"buy": "매수", "sell": "매도", "valuation": "평가"}.get(valuation_data.transaction_type, "평가")
                            QToolTip.showText(QCursor.pos(), f"{date_str}\n{type_str}\n금액: {value_str}{memo_str}")
                        else:
                            QToolTip.hideText()
            
            # 여러 데이터 포인트에 대한 툴팁 처리 함수
            def show_tooltip_for_multiple_points(pos: QPointF):
                # 페어 연결선에 대한 툴팁 확인
                for i, pair in enumerate(trade_pairs):
                    # 모든 페어는 매수/매도 쌍으로 완료됨
                    # 매수/매도 지점의 좌표
                    buy_date_str = pair.buy_valuation.evaluation_date
                    buy_date_time = QDateTime.fromString(buy_date_str, Qt.ISODate)
                    buy_value = pair.buy_valuation.evaluated_amount
                    buy_point = QPointF(buy_date_time.toMSecsSinceEpoch(), buy_value)
                    
                    sell_date_str = pair.sell_valuation.evaluation_date
                    sell_date_time = QDateTime.fromString(sell_date_str, Qt.ISODate)
                    sell_value = pair.sell_valuation.evaluated_amount
                    sell_point = QPointF(sell_date_time.toMSecsSinceEpoch(), sell_value)
                    
                    # 화면 좌표로 변환
                    buy_scene_pos = self.chart_view.chart().mapToPosition(buy_point)
                    sell_scene_pos = self.chart_view.chart().mapToPosition(sell_point)
                    mouse_scene_pos = self.chart_view.mapFromScene(pos)
                    
                    # 선과 점 사이의 거리 계산 (화면 좌표 기준)
                    distance_to_line = self.point_to_line_distance_scene(mouse_scene_pos, buy_scene_pos, sell_scene_pos)
                    
                    if distance_to_line < 20:  # 20픽셀 이내면 툴팁 표시 (임시로 넓힘)
                        buy_date = pair.buy_valuation.evaluation_date[:10]
                        sell_date = pair.sell_valuation.evaluation_date[:10]
                        buy_value_str = format_currency(pair.buy_valuation.evaluated_amount)
                        sell_value_str = format_currency(pair.sell_valuation.evaluated_amount)
                        return_rate = f"{pair.return_rate:+.2f}%"
                        
                        tooltip_text = f"매수: {buy_date} ({buy_value_str})\n"
                        tooltip_text += f"매도: {sell_date} ({sell_value_str})\n"
                        tooltip_text += f"수익률: {return_rate}"
                        
                        QToolTip.showText(QCursor.pos(), tooltip_text)
                        return  # 페어 연결선 툴팁을 우선 표시
                
                # 데이터 포인트에 대한 툴팁 확인
                for valuation in valuations:
                    # 날짜 형식을 명시적으로 지정하여 파싱
                    date_str = valuation.evaluation_date
                    if 'T' in date_str and 'Z' in date_str:
                        date_time = QDateTime.fromString(date_str, "yyyy-MM-ddThh:mm:ssZ")
                    else:
                        date_time = QDateTime.fromString(date_str, Qt.ISODate)
                    
                    if date_time.isValid():
                        value = valuation.evaluated_amount
                        data_point = QPointF(date_time.toMSecsSinceEpoch(), value)
                        
                        # 거리 계산 (화면 좌표 기준)
                        scene_pos = self.chart_view.mapFromScene(pos)
                        data_scene_pos = self.chart_view.chart().mapToPosition(data_point)
                        
                        # QPoint 연산을 위해 개별 좌표 추출
                        scene_x = scene_pos.x()
                        scene_y = scene_pos.y()
                        data_x = data_scene_pos.x()
                        data_y = data_scene_pos.y()

                        # 맨해튼 거리 계산
                        distance = abs(scene_x - data_x) + abs(scene_y - data_y)
                        
                        if distance < 20:  # 20픽셀 이내면 툴팁 표시
                            date_str = valuation.evaluation_date[:10]
                            value_str = format_currency(valuation.evaluated_amount)
                            memo_str = f"\n메모: {valuation.memo}" if valuation.memo else ""
                            type_str = {"buy": "매수", "sell": "매도", "valuation": "평가"}.get(valuation.transaction_type, "평가")
                            QToolTip.showText(QCursor.pos(), f"{date_str}\n{type_str}\n금액: {value_str}{memo_str}")
                            return  # 첫 번째로 찾은 포인트만 툴팁 표시
                
                QToolTip.hideText()
            
            # 점과 선 사이의 거리 계산 메소드 (화면 좌표 기준)
            def point_to_line_distance_scene(point: QPointF, line_start: QPointF, line_end: QPointF) -> float:
                # 점에서 선까지의 최단 거리 계산 (화면 좌표 기준)
                import math
                
                x0, y0 = point.x(), point.y()
                x1, y1 = line_start.x(), line_start.y()
                x2, y2 = line_end.x(), line_end.y()
                
                # 선분의 길이
                line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if line_length == 0:
                    # 선분의 길이가 0이면 점과 시작점 사이의 거리 반환
                    return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
                
                # 투영 계산
                t = max(0, min(1, ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)) / line_length**2))
                
                # 투영점의 좌표
                projection_x = x1 + t * (x2 - x1)
                projection_y = y1 + t * (y2 - y1)
                
                # 점과 투영점 사이의 거리
                distance = math.sqrt((x0 - projection_x)**2 + (y0 - projection_y)**2)
                
                return distance
            
            # 클래스 메소드로도 정의
            self.point_to_line_distance_scene = point_to_line_distance_scene
            
            # ChartView의 마우스 이동 이벤트 연결
            self.chart_view.setMouseTracking(True)
            original_mouse_move_event = self.chart_view.mouseMoveEvent
            
            def mouse_move_event(event):
                if original_mouse_move_event:
                    original_mouse_move_event(event)
                show_tooltip_for_multiple_points(event.pos())
            
            self.chart_view.mouseMoveEvent = mouse_move_event
            
            # 수익률 레이블 추가를 위한 타이머 설정
            def add_return_rate_labels():
                # 차트 뷰에서 씬 가져오기
                scene = self.chart_view.scene()
                
                if scene:
                    for i, pair in enumerate(trade_pairs):
                        if pair.return_rate is not None:
                            # 매수 지점
                            buy_date_str = pair.buy_valuation.evaluation_date
                            buy_date_time = QDateTime.fromString(buy_date_str, Qt.ISODate)
                            buy_value = pair.buy_valuation.evaluated_amount
                            
                            # 매도 지점
                            sell_date_str = pair.sell_valuation.evaluation_date
                            sell_date_time = QDateTime.fromString(sell_date_str, Qt.ISODate)
                            sell_value = pair.sell_valuation.evaluated_amount
                            
                            if buy_date_time.isValid() and sell_date_time.isValid():
                                # 매수/매도 지점의 좌표 계산
                                buy_timestamp = buy_date_time.toMSecsSinceEpoch()
                                sell_timestamp = sell_date_time.toMSecsSinceEpoch()
                                
                                # 차트의 좌표계를 씬의 좌표계로 변환
                                chart_rect = self.chart_view.chart().plotArea()
                                
                                # 차트 내에서의 상대적 위치 계산 (0.0 ~ 1.0)
                                x_axis = chart.axisX()
                                y_axis = chart.axisY()
                                
                                x_min = x_axis.min()
                                x_max = x_axis.max()
                                y_min = y_axis.min()
                                y_max = y_axis.max()
                                
                                # 매수 지점 좌표 변환
                                buy_chart_pos = QPointF(buy_timestamp, buy_value)
                                buy_chart_x = float(buy_chart_pos.x())
                                buy_chart_y = float(buy_chart_pos.y())
                                buy_rel_x = (buy_chart_x - x_min) / (x_max - x_min)
                                buy_rel_y = 1.0 - (buy_chart_y - y_min) / (y_max - y_min)
                                buy_scene_x = chart_rect.left() + buy_rel_x * chart_rect.width()
                                buy_scene_y = chart_rect.top() + buy_rel_y * chart_rect.height()
                                
                                # 매도 지점 좌표 변환
                                sell_chart_pos = QPointF(sell_timestamp, sell_value)
                                sell_chart_x = float(sell_chart_pos.x())
                                sell_chart_y = float(sell_chart_pos.y())
                                sell_rel_x = (sell_chart_x - x_min) / (x_max - x_min)
                                sell_rel_y = 1.0 - (sell_chart_y - y_min) / (y_max - y_min)
                                sell_scene_x = chart_rect.left() + sell_rel_x * chart_rect.width()
                                sell_scene_y = chart_rect.top() + sell_rel_y * chart_rect.height()
                                
                                # 연결선 위의 중간 지점 계산
                                mid_scene_x = (buy_scene_x + sell_scene_x) / 2
                                mid_scene_y = (buy_scene_y + sell_scene_y) / 2
                                
                                # 수익률 텍스트 생성
                                return_rate_text = f"{pair.return_rate:+.2f}%"  # + 부호 추가
                                return_label = scene.addText(return_rate_text)
                                return_label.setFont(QFont("NanumSquare", 9, QFont.Bold))
                                
                                # 배경 사각형 추가 (가독성 향상)
                                text_rect = return_label.boundingRect()
                                padding = 4
                                bg_rect = scene.addRect(
                                    mid_scene_x - text_rect.width() / 2 - padding,
                                    mid_scene_y - text_rect.height() / 2 - padding,
                                    text_rect.width() + padding * 2,
                                    text_rect.height() + padding * 2
                                )
                                
                                # 수익률에 따른 색상 지정
                                if pair.return_rate > 0:
                                    return_label.setDefaultTextColor(QColor("#ffffff"))  # 흰색 텍스트
                                    bg_rect.setBrush(QColor("#e74c3c"))  # 빨간색 배경
                                elif pair.return_rate < 0:
                                    return_label.setDefaultTextColor(QColor("#ffffff"))  # 흰색 텍스트
                                    bg_rect.setBrush(QColor("#3498db"))  # 파란색 배경
                                else:
                                    return_label.setDefaultTextColor(QColor("#ffffff"))  # 흰색 텍스트
                                    bg_rect.setBrush(QColor("#333333"))  # 검은색 배경
                                
                                bg_rect.setPen(Qt.NoPen)  # 테두리 없음
                                
                                # 텍스트 위치 조정 (배경 중앙)
                                label_x = mid_scene_x - text_rect.width() / 2
                                label_y = mid_scene_y - text_rect.height() / 2
                                return_label.setPos(label_x, label_y)
                                
                                # 배경을 텍스트 뒤로 보내기
                                bg_rect.setZValue(-1)
                                return_label.setZValue(0)
            
            # 차트가 표시된 후 수익률 레이블 추가
            from PySide6.QtCore import QTimer
            
            def delayed_add_return_rate_labels():
                # 차트가 완전히 렌더링될 때까지 기다린 후 레이블 추가
                add_return_rate_labels()
                # 추가로 한번 더 지연하여 레이블이 제대로 표시되도록 함
                QTimer.singleShot(200, add_return_rate_labels)
            
            QTimer.singleShot(300, delayed_add_return_rate_labels)
            
            # 레전드 숨기기
            chart.legend().setVisible(False)
        
        return chart
        
    def add_valuation(self) -> None:
        """새로운 평가 기록 추가 다이얼로그"""
        dlg = ValuationDialog(self.account)
        if dlg.exec() == QDialog.Accepted:
            try:
                amount, date, memo, transaction_type = dlg.get_data()
                self.service.add_valuation(self.account.id, amount, date, memo, transaction_type)
                self.update_chart()
                # 계좌 정보 업데이트
                self.account = self.service.get_account(self.account.id)
                self.setup_account_info(self.layout())
            except Exception as e:
                QMessageBox.warning(self, "에러", f"평가 추가 실패: {str(e)}")
                
    def auto_valuation(self) -> None:
        """자동 평가 실행 (현재 날짜와 금액으로 평가 기록 추가)"""
        from datetime import datetime, timezone
        
        # 가장 최근 평가금액 가져오기
        latest_valuation = self.account.latest_valuation
        if not latest_valuation:
            QMessageBox.information(self, "알림", "이전 평가 기록이 없습니다. 수동으로 평가를 추가해주세요.")
            return
            
        # 현재 날짜와 이전 평가금액으로 자동 평가
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        current_amount = latest_valuation.evaluated_amount  # 이전 평가금액 유지
        
        reply = QMessageBox.question(
            self,
            "자동 평가",
            f"현재 날짜({current_date[:10]})로 평가 기록을 추가하시겠습니까?\n"
            f"평가금액: {format_currency(current_amount)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.service.add_valuation(self.account.id, current_amount, current_date, "자동 평가")
                self.update_chart()
                self.account = self.service.get_account(self.account.id)
                self.setup_account_info(self.layout())
                QMessageBox.information(self, "성공", "자동 평가가 완료되었습니다.")
            except Exception as e:
                QMessageBox.warning(self, "에러", f"자동 평가 실패: {str(e)}")
                
    def edit_account(self) -> None:
        """계좌 수정 다이얼로그 열기"""
        dlg = AccountEditDialog(self.account)
        if dlg.exec() == QDialog.Accepted:
            try:
                # Unpack all values, including new investment ones
                new_name, new_type, new_balance, new_color, new_image_path, new_purchase_amount, new_cash_holding, new_evaluated_amount, new_valuation_date = dlg.get_data()
                if not new_name:
                    QMessageBox.warning(self, "에러", "계좌명을 입력하세요.")
                    return
                
                # Calculate the difference to adjust opening_balance
                balance_diff = new_balance - self.account.balance()
                self.account.opening_balance += balance_diff
                self.account.name = new_name
                self.account.type = new_type
                self.account.color = new_color
                self.account.image_path = new_image_path # Update image path
                
                # Update investment specific fields
                if self.account.type == "투자":
                    self.account.purchase_amount = new_purchase_amount
                    self.account.cash_holding = new_cash_holding
                    self.account.evaluated_amount = new_evaluated_amount
                    self.account.last_valuation_date = new_valuation_date
                
                self.service.update_account(self.account)
                self.setWindowTitle(f"{new_name} 자산 평가 추이")
                self.update_chart()
                self.setup_account_info(self.layout())
                # Update parent UI if available
                if hasattr(self.parent(), 'update_ui'):
                    self.parent().update_ui()
                    
            except ValueError as e:
                QMessageBox.warning(self, "에러", str(e))
            except Exception as e:
                # Catching generic exception for cases where get_data returns less than 9 values (e.g. for non-investment accounts if not handled carefully)
                # However, get_data now always returns 9 values.
                QMessageBox.warning(self, "에러", f"계좌 수정 중 오류 발생: {str(e)}")

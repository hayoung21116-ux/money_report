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
from PySide6.QtCore import QRect, QRectF, Qt, QDate, QSize, Signal, QPointF
from PySide6.QtGui import QAction, QPalette, QColor, QPixmap, QPainter, QDoubleValidator, QCursor, QFont, QBrush, QPainterPath
from PySide6.QtWidgets import QGraphicsSimpleTextItem, QGraphicsScene
from PySide6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis, QStackedBarSeries

from domain import Account, Transaction
from services import format_currency, gen_id

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
        """Setup net income tab with chart"""
        layout = QVBoxLayout(self.net_income_tab)
        
        # Net income summary frame
        self.net_income_summary_frame = QFrame()
        summary_layout = QHBoxLayout(self.net_income_summary_frame)
        
        # Create summary labels (will be updated by update_net_income_tab_summary)
        self.net_income_total_label = QLabel("전체 순수익: -")
        self.net_income_year_label = QLabel("연도 순수익: -")
        
        self.net_income_total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.net_income_year_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        summary_layout.addWidget(self.net_income_total_label)
        summary_layout.addWidget(self.net_income_year_label)
        summary_layout.addStretch()
        
        layout.addWidget(self.net_income_summary_frame)
        
        # Chart
        self.net_income_chart = QChartView()
        self.net_income_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.net_income_chart)
        
    def update_net_income_tab_summary(self, year: str) -> None:
        """Update the net income summary labels for the selected year"""
        # Get all-time data for the "전체" label
        all_time_monthly_data = self.service.monthly_income_breakdown()
        total_net_all_time = sum(data["savings"] + data["interest"] - data["expense"] for data in all_time_monthly_data.values())

        # Get data for the selected year for the "연도" label
        yearly_monthly_data = self.service.monthly_income_breakdown(year=year)
        total_net_for_year = sum(data["savings"] + data["interest"] - data["expense"] for data in yearly_monthly_data.values())
        
        self.net_income_total_label.setText(f"전체 순수익: {format_currency(total_net_all_time)}")
        self.net_income_year_label.setText(f"{year} 순수익: {format_currency(total_net_for_year)}")
        
    def update_net_income_chart_for_year(self, year: str) -> None:
        """Update the net income chart for the selected year"""
        monthly_data = self.service.monthly_income_breakdown(year=year)
        chart = self.create_net_income_chart(monthly_data)
        self.net_income_chart.setChart(chart)
        
    def setup_savings_tab(self) -> None:
        """Setup savings tab with chart"""
        layout = QVBoxLayout(self.savings_tab)
        
        # Savings summary frame
        self.savings_summary_frame = QFrame()
        summary_layout = QHBoxLayout(self.savings_summary_frame)
        
        # Create summary labels (will be updated by update_savings_tab_summary)
        self.savings_total_label = QLabel("총 저축액: -")
        self.savings_interest_total_label = QLabel("총 이자액: -")
        self.savings_year_label = QLabel("연도 저축액: -")
        self.savings_interest_year_label = QLabel("연도 이자액: -")
        
        self.savings_total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.savings_interest_total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.savings_year_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.savings_interest_year_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        summary_layout.addWidget(self.savings_total_label)
        summary_layout.addWidget(self.savings_interest_total_label)
        summary_layout.addWidget(self.savings_year_label)
        summary_layout.addWidget(self.savings_interest_year_label)
        summary_layout.addStretch()
        
        layout.addWidget(self.savings_summary_frame)
        
        self.savings_chart = QChartView()
        self.savings_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.savings_chart)
        
    def update_savings_tab_summary(self, year: str) -> None:
        """Update the savings summary labels for the selected year"""
        # Get all-time data for the "총" labels
        all_time_monthly_data = self.service.monthly_income_breakdown()
        total_savings_all_time = sum(data["savings"] for data in all_time_monthly_data.values())
        total_interest_all_time = sum(data["interest"] for data in all_time_monthly_data.values())
        total_interest_rate_all_time = (total_interest_all_time / total_savings_all_time * 100) if total_savings_all_time > 0 else 0

        # Get data for the selected year for the "연도" labels
        yearly_monthly_data = self.service.monthly_income_breakdown(year=year)
        total_savings_for_year = sum(data["savings"] for data in yearly_monthly_data.values())
        total_interest_for_year = sum(data["interest"] for data in yearly_monthly_data.values())
        year_interest_rate = (total_interest_for_year / total_savings_for_year * 100) if total_savings_for_year > 0 else 0
        
        self.savings_total_label.setText(f"총 저축액: {format_currency(total_savings_all_time)}")
        self.savings_interest_total_label.setText(f"총 이자액: {format_currency(total_interest_all_time)} ({total_interest_rate_all_time:.1f}%)")
        self.savings_year_label.setText(f"{year} 저축액: {format_currency(total_savings_for_year)}")
        self.savings_interest_year_label.setText(f"{year} 이자액: {format_currency(total_interest_for_year)} ({year_interest_rate:.1f}%)")
        
    def update_savings_chart_for_year(self, year: str) -> None:
        """Update the savings chart for the selected year"""
        monthly_data = self.service.monthly_income_breakdown(year=year)
        chart = self.create_savings_chart(monthly_data)
        self.savings_chart.setChart(chart)
        

    def setup_salary_tab(self) -> None:
        """Setup salary tab with chart"""
        layout = QVBoxLayout(self.salary_tab)
        
        # Salary summary frame
        self.salary_summary_frame = QFrame()
        summary_layout = QHBoxLayout(self.salary_summary_frame)
        
        # Create summary labels (will be updated by update_salary_tab_summary)
        self.salary_mingyu_total_label = QLabel("민규 총합: -")
        self.salary_hayoung_total_label = QLabel("하영 총합: -")
        self.salary_mingyu_year_label = QLabel("연도 민규: -")
        self.salary_hayoung_year_label = QLabel("연도 하영: -")
        
        self.salary_mingyu_total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.salary_hayoung_total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.salary_mingyu_year_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.salary_hayoung_year_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        summary_layout.addWidget(self.salary_mingyu_total_label)
        summary_layout.addWidget(self.salary_hayoung_total_label)
        summary_layout.addWidget(self.salary_mingyu_year_label)
        summary_layout.addWidget(self.salary_hayoung_year_label)
        summary_layout.addStretch()
        
        layout.addWidget(self.salary_summary_frame)
        
        # Chart
        self.salary_chart = QChartView()
        self.salary_chart.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.salary_chart)
        
    def update_salary_tab_summary(self, year: str) -> None:
        """Update the salary summary labels for the selected year"""
        # Get all-time data for the "총합" labels
        all_time_salaries = self.service.get_salaries()
        total_mingyu_all_time = sum(s["amount"] for s in all_time_salaries if s["person"] == "민규")
        total_hayoung_all_time = sum(s["amount"] for s in all_time_salaries if s["person"] == "하영")

        # Get data for the selected year for the "연도" labels
        yearly_salaries = self.service.get_salaries(year=year)
        total_mingyu_for_year = sum(s["amount"] for s in yearly_salaries if s["person"] == "민규")
        total_hayoung_for_year = sum(s["amount"] for s in yearly_salaries if s["person"] == "하영")
        
        self.salary_mingyu_total_label.setText(f"민규 총합: {format_currency(total_mingyu_all_time)}")
        self.salary_hayoung_total_label.setText(f"하영 총합: {format_currency(total_hayoung_all_time)}")
        self.salary_mingyu_year_label.setText(f"{year} 민규: {format_currency(total_mingyu_for_year)}")
        self.salary_hayoung_year_label.setText(f"{year} 하영: {format_currency(total_hayoung_for_year)}")
        
    def update_salary_chart_for_year(self, year: str) -> None:
        """Update the salary chart for the selected year"""
        salaries = self.service.get_salaries(year=year)
        chart = self.create_salary_chart(salaries)
        self.salary_chart.setChart(chart)

    def update_salary_chart(self) -> None:
        """Update salary chart with current data"""
        salaries = self.service.get_salaries()
        chart = self.create_salary_chart(salaries)
        self.salary_chart.setChart(chart)

    def create_salary_chart(self, salaries: list[dict]) -> QChart:
        """Create chart showing monthly salaries"""
        chart = QChart()
        chart.setTitle("월별 월급")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Group salaries by month and person
        from collections import defaultdict
        monthly_data = defaultdict(lambda: {"민규": 0, "하영": 0})
        for salary in salaries:
            monthly_data[salary["month"]][salary["person"]] += salary["amount"]
        
        months = sorted(monthly_data.keys())
        mingyu_set = QBarSet("민규")
        hayoung_set = QBarSet("하영")
        
        for month in months:
            mingyu_set.append(monthly_data[month]["민규"])
            hayoung_set.append(monthly_data[month]["하영"])
        
        series = QBarSeries()
        series.append(mingyu_set)
        series.append(hayoung_set)
        chart.addSeries(series)
        
        # Configure axes
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        max_value = max(
            max(monthly_data[month]["민규"], monthly_data[month]["하영"])
            for month in months
        ) if months else 0
        max_value = ((int(max_value) // 1000000) + 1) * 1000000
        axis_y.setRange(0, max_value)
        axis_y.setTitleText("만 원")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        def handle_hover(status: bool, index: int, barset: QBarSet):
            if not status:
                QToolTip.hideText()
                return
            value = barset.at(index)
            pos = chart.mapToPosition(QPointF(index + 0.5, value), series)
            text = f"{int(value):,.0f}원"
            QToolTip.showText(QCursor.pos(), text)

        series.hovered.connect(handle_hover)
        
        return chart
        
    def update_net_income_chart(self) -> None:
        """Update net income chart with current data"""
        monthly_data = self.service.monthly_income_breakdown()
        chart = self.create_net_income_chart(monthly_data)
        self.net_income_chart.setChart(chart)
        
    def update_savings_chart(self) -> None:
        """Update savings chart with current data"""
        monthly_data = self.service.monthly_income_breakdown()
        chart = self.create_savings_chart(monthly_data)
        self.savings_chart.setChart(chart)
        
        
    def create_net_income_chart(self, monthly_data: dict[str, dict]) -> QChart:
        chart = QChart()
        chart.setTitle("월별 순수익")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        months = []
        net_incomes = []
        for month, data in monthly_data.items():
            months.append(month)
            net_income = data["savings"] + data["interest"] - data["expense"]
            net_incomes.append(net_income)
        
        positive_set = QBarSet("양의 순수익")
        negative_set = QBarSet("음의 순수익")
        positive_set.setColor(QColor("#4CAF50"))
        negative_set.setColor(QColor("#FF0000"))
        for value in net_incomes:
            if value >= 0:
                positive_set.append(value)
                negative_set.append(0)
            else:
                positive_set.append(0)
                negative_set.append(value)

        series = QBarSeries()
        series.append(positive_set)
        series.append(negative_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        max_value = max(abs(n) for n in net_incomes) if net_incomes else 0
        max_value = ((int(max_value) // 1000000) + 1) * 1000000
        axis_y.setRange(-max_value, max_value)
        axis_y.setTitleText("만 원")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(False)

        def handle_hover(status: bool, index: int, barset: QBarSet):
            if not status:
                QToolTip.hideText()
                return

            value = barset.at(index)
            pos = chart.mapToPosition(QPointF(index + 0.5, value), series)
            text = f"{int(value):,.0f}원"
            QToolTip.showText(QCursor.pos(), text)

        series.hovered.connect(handle_hover)
        
        return chart
    
    def create_savings_chart(self, monthly_data: dict[str, dict]) -> QChart:
        """Create chart showing savings and interest"""
        chart = QChart()
        chart.setTitle("월별 저축+이자")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        series = QStackedBarSeries()
        savings_set = QBarSet("저축")
        interest_set = QBarSet("이자")
        
        savings_set.setColor(QColor("#4CAF50"))  # Green
        interest_set.setColor(QColor("#FFC107"))  # Amber
        
        months = []
        savings = []
        interest = []
        
        for month, data in monthly_data.items():
            months.append(month)
            savings.append(data["savings"])
            interest.append(data["interest"])
            
        savings_set.append(savings)
        interest_set.append(interest)
        series.append(savings_set)
        series.append(interest_set)
        chart.addSeries(series)
        
        # Configure axes
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        max_value = max(s + i for s, i in zip(savings, interest)) if savings else 0
        max_value = ((int(max_value) // 1000000) + 1) * 1000000
        axis_y.setRange(0, max_value)
        axis_y.setTitleText("만 원")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        def handle_hover(status: bool, index: int, barset: QBarSet):
            if not status:
                QToolTip.hideText()
                return

            value = barset.at(index)
            pos = chart.mapToPosition(QPointF(index + 0.5, value), series)
            text = f"{int(value):,.0f}원"
            QToolTip.showText(QCursor.pos(), text)

        series.hovered.connect(handle_hover)
        
        return chart
        
    def create_expense_chart(self, monthly_data: dict[str, dict]) -> QChart:
        """Create chart showing expenses"""
        chart = QChart()
        chart.setTitle("월별 지출")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        series = QBarSeries()
        expense_set = QBarSet("지출")
        expense_set.setColor(QColor("#F44336"))  # Red
        
        months = []
        expenses = []
        
        for month, data in monthly_data.items():
            months.append(month)
            expenses.append(data["expense"])
            
        expense_set.append(expenses)
        series.append(expense_set)
        chart.addSeries(series)
        
        # Configure axes
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f")
        max_value = max(expenses) if expenses else 0
        max_value = ((int(max_value) // 1000000) + 1) * 1000000
        axis_y.setRange(0, max_value)
        axis_y.setTitleText("만 원")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        def handle_hover(status: bool, index: int, barset: QBarSet):
            if not status:
                QToolTip.hideText()
                return

            value = barset.at(index)
            pos = chart.mapToPosition(QPointF(index + 0.5, value), series)
            text = f"{int(value):,.0f}원"
            QToolTip.showText(QCursor.pos(), text)

        series.hovered.connect(handle_hover)
        
        return chart

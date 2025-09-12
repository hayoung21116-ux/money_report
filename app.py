from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QDialog, QMessageBox, QGraphicsScene, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction, QFont, QFontDatabase, QPixmap, QPainter

from services import LocalJSONDataSource, LedgerRepository, LedgerService, format_currency
from ui_components import (
    AccountCard, AccountDialog, TransactionTableDialog, TransactionDialog, 
    SalaryDialog, StatsDialog
)

class MainWindow(QMainWindow):
    """Main application window for the ledger system"""
    
    def __init__(self, service: LedgerService):
        """Initialize the main window with ledger service"""
        super().__init__()
        self.service = service
        self.setup_ui()
        self.setup_shortcuts()
        
    def setup_ui(self) -> None:
        """Setup the main window UI components"""
        self.setWindowTitle("가계부")
        self.resize(800, 600)
        self.setup_styles()
        self.setup_main_layout()
        self.setup_action_buttons()
        self.update_ui()
        
    def setup_styles(self) -> None:
        """Configure application-wide styles"""
        self.setStyleSheet("""
            * {
                font-family: 'NanumSquare', sans-serif;
                font-size: 15px;
            }
        """)
        
    def setup_main_layout(self) -> None:
        """Setup the main window layout"""
        # Total assets label
        self.total_label = QLabel()
        self.total_label.setStyleSheet("""
            font-size:20px; 
            padding:14px 14px 14px 0;
            font-weight:bold;
        """)
        
        # Accounts grid in scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.scroll.setWidget(self.grid_widget)
        
        # Main layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.total_label)
        vbox.addWidget(self.scroll)
        
        container = QWidget()
        container.setLayout(vbox)
        self.setCentralWidget(container)
        
    def setup_action_buttons(self) -> None:
        """Setup action buttons (add account, add transaction, stats)"""
        # Add account button
        self.add_account_btn = QPushButton("계좌 추가", self)
        self.add_account_btn.setStyleSheet("""
            padding: 8px 16px;
            font-weight: bold;
        """)
        self.add_account_btn.clicked.connect(self.add_account)
        
        # Floating action button for salary input
        self.fab = QPushButton("$", self)
        self.fab.setFixedSize(50, 50)
        self.fab.setStyleSheet("""
            border-radius:25px;
            background-color:#F44336;
            color:white;
            font-size:24px;
            font-family: 'NanumSquare', '맑은 고딕', 'Segoe UI';
        """)
        self.fab.clicked.connect(self.add_salary)

        # Stats button
        self.stats_btn = QPushButton("통계", self)
        self.stats_btn.setStyleSheet("""
            padding: 8px 16px;
            font-weight: bold;
            margin-left: 10px;
        """)
        self.stats_btn.clicked.connect(self.show_stats)
        
    def setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts"""
        # Add account shortcut
        act_new_acc = QAction(self)
        act_new_acc.setShortcut("Ctrl+N")
        act_new_acc.triggered.connect(self.add_account)
        self.addAction(act_new_acc)
        
        # Add transaction shortcut
        act_new_txn = QAction(self)
        act_new_txn.setShortcut("Ctrl+T")
        act_new_txn.triggered.connect(self.add_transaction)
        self.addAction(act_new_txn)
        
        # Save shortcut
        act_save = QAction(self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save)
        self.addAction(act_save)

        # Stats shortcut
        act_stats = QAction(self)
        act_stats.setShortcut("Ctrl+Shift+S")
        act_stats.triggered.connect(self.show_stats)
        self.addAction(act_stats)

    def resizeEvent(self, e) -> None:
        """Handle window resize events to position buttons"""
        super().resizeEvent(e)
        self.add_account_btn.move(self.width()-150, 10)
        self.stats_btn.move(self.width()-250, 10)
        self.fab.move(self.width()-70, self.height()-70)
        
    def update_ui(self):
        """Update the main UI with current data"""
        total_assets = self.service.total_assets()
        total_cash = self.service.total_cash()
        self.total_label.setText(f"총 자산: {format_currency(total_assets)} / 현금: {format_currency(total_cash)}")
        
        # Clear existing widgets
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            w.setParent(None)
            
        # Add account cards with custom sorting
        accounts = self.service.list_accounts()
        
        # Define type order
        type_order = {"현금": 0, "투자": 1, "소비": 2}
        
        # Sort accounts: first by status (active first), then by type order, then by name (민규 first)
        accounts = sorted(
            accounts,
            key=lambda acc: (
                acc.status == "dead",  # False(active) comes first, True(dead) comes last
                type_order.get(acc.type, 3),  # Use type_order, unknown types go last
                "민규" not in acc.name  # False(contains 민규) comes first, True(doesn't contain) comes after
            )
        )
        
        # Add account cards with type-based line breaks
        current_row = 0
        current_col = 0
        last_type = None
        
        for acc in accounts:
            # Add line break when type changes, considering both active and dead accounts
            if (last_type is not None and 
                acc.type != last_type):
                current_col = 0
                current_row += 1
            
            # Add account card
            card = AccountCard(acc)
            card.clicked.connect(self.open_transactions)
            self.grid_layout.addWidget(card, current_row, current_col)
            
            # Update position
            current_col += 1
            if current_col >= 3:
                current_col = 0
                current_row += 1
            
            # Update last type for the next iteration
            last_type = acc.type
            
    def add_account(self):
        """Open dialog to add new account"""
        dlg = AccountDialog()
        if dlg.exec() == QDialog.Accepted:
            try:
                name, type_, color, bal, image_path = dlg.get_data()
                self.service.add_account(name, type_, color, bal, image_path)
                self.update_ui()
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "에러", str(e))

    def add_salary(self):
        """Open dialog to add salary"""
        dlg = SalaryDialog(self.service)
        dlg.exec()
        self.update_ui()
        
    def add_transaction(self):
        """Open dialog to add transaction to first account"""
        accounts = self.service.list_accounts()
        if not accounts:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "에러", "계좌를 먼저 추가해주세요")
            return
            
        # 첫 번째 계좌로 바로 거래 추가 다이얼로그 열기
        dlg = TransactionDialog(accounts[0], self.service)
        dlg.exec()
        self.update_ui()

    def open_transactions(self, account_id: str):
        """Open transaction dialog for specific account"""
        acc = self.service.get_account(account_id)
        if acc:
            dlg = TransactionTableDialog(acc, self.service)
            dlg.exec()
            self.update_ui()

    def save(self):
        """Save current data"""
        # Service handles saving automatically, but we can add manual save feedback
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "저장", "저장되었습니다.")

    def show_stats(self):
        """Open statistics dialog"""
        stats_dialog = StatsDialog(self.service)
        stats_dialog.exec()

def load_fonts():
    """Load NanumSquare fonts"""
    fontDB = QFontDatabase()
    
    # Load all NanumSquare fonts
    font_files = [
        "fonts/NanumSquareR.ttf",
        "fonts/NanumSquareB.ttf", 
        "fonts/NanumSquareEB.ttf",
        "fonts/NanumSquareL.ttf",
        "fonts/NanumSquareacR.ttf",
        "fonts/NanumSquareacB.ttf",
        "fonts/NanumSquareacEB.ttf",
        "fonts/NanumSquareacL.ttf"
    ]
    
    loaded_fonts = []
    for font_file in font_files:
        font_id = fontDB.addApplicationFont(font_file)
        if font_id != -1:
            font_family = fontDB.applicationFontFamilies(font_id)[0]
            loaded_fonts.append(font_family)
    
    return loaded_fonts

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Load fonts
    loaded_fonts = load_fonts()
    if loaded_fonts:
        app.setFont(QFont(loaded_fonts[0], 10))
    
    # Initialize data layer
    ds = LocalJSONDataSource("ledger.json")
    repo = LedgerRepository(ds)
    service = LedgerService(repo)
    
    # Create and show main window
    win = MainWindow(service)
    win.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

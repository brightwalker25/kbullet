#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Kbullet - a bullet journal for the Linux desktop
# Copyright (C) 2026  brightwalker25
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Kbullet - a bullet journal for the Linux desktop.

Uses Ryder Carroll's Bullet Journal notation and stores entries as one
plain markdown file per day, so the journal outlives the app.

Features:
  - Morning / Afternoon / Evening sections
  - Drag and drop entries within and between sections
  - Sort by entry type
  - Full bullet journal notation support
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

__version__ = "2.1.0"
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel,
    QSystemTrayIcon, QMenu, QMessageBox, QDialog,
    QCalendarWidget, QListWidget, QListWidgetItem, QFileDialog,
    QGroupBox, QCheckBox, QInputDialog, QScrollArea, QComboBox,
    QAbstractItemView, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QDate, QSettings, QMimeData, pyqtSignal
from PyQt6.QtGui import (
    QIcon, QAction, QKeySequence, QShortcut, QFont, QTextCharFormat,
    QColor, QTextCursor, QTextDocument, QPageLayout, QDrag, QPainter,
    QBrush, QPen
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog


# ---------------------------------------------------------------------------
# Custom drag-and-drop list widget for journal sections
# ---------------------------------------------------------------------------

class SectionListWidget(QListWidget):
    """A list widget that supports drag-and-drop between sections and
    emits signals when entries change or are selected."""

    entries_changed = pyqtSignal()
    entry_selected = pyqtSignal(str, object)  # (entry_text, list_widget)

    SYMBOL_COLORS = {
        '•': '#3daee9',   # Task - blue
        '○': '#27ae60',   # Event - green
        '—': '#f39c12',   # Note - amber
        '=': '#e91e9b',   # Mood - pink
        '!': '#ff5555',   # Urgent - bright red
        '*': '#ffaa00',   # Priority - gold
        '×': '#7f8c8d',   # Complete - grey
        '>': '#8e44ad',   # Migrated - purple
        '<': '#e74c3c',   # Scheduled - red
        '\\': '#16a085',  # Delegated - teal
        '|': '#9b59b6',   # Waiting - violet
    }

    # All valid bullet symbols for parsing
    VALID_SYMBOLS = '•○—=!*×><\\|'

    def __init__(self, section_name, parent=None):
        super().__init__(parent)
        self.section_name = section_name
        self._pre_sort_order = None  # for undo-sort

        # Let Qt handle drag initiation, but use CopyAction to prevent auto-removal
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Word wrap for long entries
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)

        # Styling
        self.setFont(QFont("Monospace", 11))
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 2px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(61, 174, 233, 0.2);
            }
        """)

        # Connect selection signal
        self.currentItemChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self, current, _previous):
        if current:
            self.entry_selected.emit(current.text(), self)
        else:
            self.entry_selected.emit('', self)

    def contextMenuEvent(self, event):
        """Show right-click context menu on an entry."""
        item = self.itemAt(event.pos())
        if not item:
            return

        # Make sure this item is selected so the main window tracks it
        self.setCurrentItem(item)

        main = self.window()
        if not hasattr(main, 'edit_entry_text'):
            return

        menu = QMenu(self)

        # --- Modify Entry ---
        edit_action = menu.addAction("✏️ Edit Text")
        edit_action.triggered.connect(main.edit_entry_text)
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(main.delete_entry)

        menu.addSeparator()

        # --- Change Type ---
        type_menu = menu.addMenu("Change Type")
        type_menu.addAction("• Task").triggered.connect(lambda: main.change_symbol('•'))
        type_menu.addAction("○ Event").triggered.connect(lambda: main.change_symbol('○'))
        type_menu.addAction("— Note").triggered.connect(lambda: main.change_symbol('—'))
        type_menu.addAction("= Mood").triggered.connect(lambda: main.change_symbol('='))
        type_menu.addAction("! Urgent").triggered.connect(lambda: main.change_symbol('!'))
        type_menu.addAction("* Priority").triggered.connect(lambda: main.change_symbol('*'))

        # --- Mark Status ---
        status_menu = menu.addMenu("Mark Status")
        status_menu.addAction("× Done").triggered.connect(main.mark_complete)
        status_menu.addAction("• Un-done").triggered.connect(main.mark_undone)
        status_menu.addAction("> Migrate").triggered.connect(main.mark_migrated)
        status_menu.addAction("< Schedule").triggered.connect(main.show_master_task_list)
        status_menu.addAction("\\ Delegated").triggered.connect(main.mark_delegated)
        status_menu.addAction("| Waiting").triggered.connect(main.mark_waiting)

        menu.exec(event.globalPos())

    def dropEvent(self, event):
        """Handle drop — we do everything manually so nothing gets lost."""
        source = event.source()
        if not isinstance(source, SectionListWidget):
            event.ignore()
            return

        dragged_items = source.selectedItems()
        if not dragged_items:
            event.ignore()
            return

        # Snapshot text and row before touching anything
        entry_text = dragged_items[0].text()
        source_row = source.row(dragged_items[0])

        # Where to insert in this list
        drop_index = self.indexAt(event.position().toPoint())
        drop_row = drop_index.row() if drop_index.isValid() else self.count()

        if source is self:
            # Internal reorder
            if source_row == drop_row:
                event.ignore()
                return
            self.takeItem(source_row)
            if drop_row > source_row:
                drop_row -= 1
        else:
            # Cross-widget: remove from source
            source.takeItem(source_row)
            source.entries_changed.emit()

        # Insert at target
        new_item = QListWidgetItem(entry_text)
        self._style_item(new_item)
        self.insertItem(drop_row, new_item)
        self.setCurrentItem(new_item)

        self.entries_changed.emit()
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()

    def add_entry(self, text):
        """Add an entry and style it by symbol."""
        item = QListWidgetItem(text)
        self._style_item(item)
        self.addItem(item)

    def insert_entry(self, row, text):
        """Insert an entry at a specific row."""
        item = QListWidgetItem(text)
        self._style_item(item)
        self.insertItem(row, item)

    def _style_item(self, item):
        """Color-code the item based on its bullet symbol, strikethrough if done."""
        text = item.text().strip()
        if not text:
            return

        symbol = text[0]
        color = self.SYMBOL_COLORS.get(symbol)
        if color:
            item.setForeground(QColor(color))

        # Grey out status markers
        if symbol in ('×', '>', '<', '\\', '|'):
            item.setForeground(QColor(self.SYMBOL_COLORS.get(symbol, '#7f8c8d')))

        # Strikethrough for done entries, clear it for everything else
        font = item.font()
        font.setStrikeOut(symbol == '×')
        item.setFont(font)

    def get_entries(self):
        """Return all entry strings in order."""
        return [self.item(i).text() for i in range(self.count())]

    def sort_by_type(self):
        """Sort entries by symbol type: Tasks, Events, Notes, then status."""
        entries = self.get_entries()
        self._pre_sort_order = list(entries)  # save for undo
        order = {'!': 0, '*': 1, '•': 2, '○': 3, '—': 4, '=': 5,
                 '×': 6, '>': 7, '<': 8, '\\': 9, '|': 10}
        entries.sort(key=lambda e: (order.get(e[0] if e else '', 99), e))
        self.clear()
        for e in entries:
            self.add_entry(e)
        self.entries_changed.emit()

    def sort_alphabetical(self):
        """Sort entries alphabetically (with timestamps this is chronological)."""
        entries = self.get_entries()
        self._pre_sort_order = list(entries)  # save for undo
        # Strip the symbol for sorting so '• [09:00]' and '○ [09:00]' sort by content
        entries.sort(key=lambda e: e[2:] if len(e) > 2 else e)
        self.clear()
        for e in entries:
            self.add_entry(e)
        self.entries_changed.emit()

    def unsort(self):
        """Restore pre-sort order if available. Returns True if restored."""
        if self._pre_sort_order is not None:
            self.clear()
            for e in self._pre_sort_order:
                self.add_entry(e)
            self._pre_sort_order = None
            self.entries_changed.emit()
            return True
        return False

    def find_and_remove(self, entry_text):
        """Find and remove the first item matching entry_text. Returns True if found."""
        for i in range(self.count()):
            if self.item(i).text() == entry_text:
                self.takeItem(i)
                return True
        return False

    def find_and_replace(self, old_text, new_text):
        """Find entry matching old_text and replace with new_text. Returns True if found."""
        for i in range(self.count()):
            if self.item(i).text() == old_text:
                self.item(i).setText(new_text)
                self._style_item(self.item(i))
                return True
        return False


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class Kbullet(QMainWindow):
    """Main Kbullet application window"""

    # Bullet notation symbols
    NOTATION = {
        'task': '•',
        'event': '○',
        'note': '—',
        'mood': '=',
        'urgent': '!',
        'priority': '*',
        'complete': '×',
        'migrated': '>',
        'scheduled': '<',
        'delegated': '\\',
        'waiting': '|',
    }

    # All valid bullet symbols for parsing
    VALID_SYMBOLS = '•○—=!*×><\\|'

    SECTIONS = ['Morning', 'Afternoon', 'Evening']

    def __init__(self):
        super().__init__()

        # Settings
        self.settings = QSettings('Kbullet', 'Settings')

        # Default journal directory
        default_dir = Path.home() / 'Documents' / 'Kbullet'
        self.journal_dir = Path(self.settings.value('journal_dir', str(default_dir)))
        self.journal_dir.mkdir(parents=True, exist_ok=True)

        # Current date
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.current_date = datetime.now()

        # Current file path
        self.current_file = self.journal_dir / f"{self.today}.md"

        # Track if timestamps should be shown
        self.show_timestamps = self.settings.value('show_timestamps', True, type=bool)

        # Set by quit_app() so closeEvent lets a real quit through instead of
        # hiding to the tray.
        self._really_quit = False

        # Track selected entry for modifications
        self.selected_entry = None
        self.selected_section = None  # which SectionListWidget holds the selection

        # Initialize UI
        self.init_ui()

        # Load current day's entries
        self.load_current_day()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Kbullet - {self.today}")
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(400, 300)

        # Create menu bar
        menubar = self.menuBar()

        # --- File menu ---
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open File...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.setStatusTip("Open a specific journal file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        print_action = QAction("&Print...", self)
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.setStatusTip("Print current day's entries")
        print_action.triggered.connect(self.print_current_view)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.setStatusTip("Application settings")
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.quit_app)
        file_menu.addAction(quit_action)

        # --- View menu ---
        view_menu = menubar.addMenu("&View")

        today_action = QAction("Go to &Today", self)
        today_action.setShortcut(QKeySequence("Ctrl+H"))
        today_action.triggered.connect(self.go_to_today)
        view_menu.addAction(today_action)

        view_menu.addSeparator()

        week_action = QAction("&Week View", self)
        week_action.setShortcut(QKeySequence("Ctrl+W"))
        week_action.triggered.connect(self.show_week_view)
        view_menu.addAction(week_action)

        month_action = QAction("&Month View", self)
        month_action.setShortcut(QKeySequence("Ctrl+K"))
        month_action.triggered.connect(self.show_month_view)
        view_menu.addAction(month_action)

        view_menu.addSeparator()

        sort_type_action = QAction("Sort All by &Type", self)
        sort_type_action.setShortcut(QKeySequence("Ctrl+G"))
        sort_type_action.setStatusTip("Sort entries by type: tasks, events, notes")
        sort_type_action.triggered.connect(self.sort_all_by_type)
        view_menu.addAction(sort_type_action)

        sort_alpha_action = QAction("Sort All &Chronologically", self)
        sort_alpha_action.setShortcut(QKeySequence("Ctrl+Shift+G"))
        sort_alpha_action.setStatusTip("Sort entries by time / alphabetically")
        sort_alpha_action.triggered.connect(self.sort_all_alphabetical)
        view_menu.addAction(sort_alpha_action)

        unsort_action = QAction("&Undo Sort", self)
        unsort_action.setShortcut(QKeySequence("Ctrl+Z"))
        unsort_action.setStatusTip("Restore order before last sort")
        unsort_action.triggered.connect(self.unsort_all_sections)
        view_menu.addAction(unsort_action)

        view_menu.addSeparator()

        self.toggle_menubar_action = QAction("Toggle &Menubar", self)
        self.toggle_menubar_action.setCheckable(True)
        self.toggle_menubar_action.setChecked(True)
        self.toggle_menubar_action.triggered.connect(self.toggle_menubar)
        view_menu.addAction(self.toggle_menubar_action)

        # --- Search menu ---
        search_menu = menubar.addMenu("&Search")

        search_action = QAction("&Find in Journal...", self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self.show_search)
        search_menu.addAction(search_action)

        search_menu.addSeparator()

        unfinished_action = QAction("&Unfinished Tasks", self)
        unfinished_action.setShortcut(QKeySequence("Ctrl+U"))
        unfinished_action.triggered.connect(self.show_unfinished_tasks)
        search_menu.addAction(unfinished_action)

        master_list_action = QAction("&Master Task List", self)
        master_list_action.setShortcut(QKeySequence("Ctrl+S"))
        master_list_action.triggered.connect(self.show_master_task_list)
        search_menu.addAction(master_list_action)

        # --- Help menu ---
        help_menu = menubar.addMenu("&Help")

        notation_action = QAction("Bullet Journal &Notation", self)
        notation_action.triggered.connect(self.show_notation_help)
        help_menu.addAction(notation_action)

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self.show_shortcuts_help)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("&About Kbullet", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # ====== Central widget ======
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(4)

        # --- Navigation bar ---
        self.nav_widget = QWidget()
        nav_layout = QHBoxLayout(self.nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        prev_btn = QPushButton("◀ Previous Day")
        prev_btn.setToolTip("Go to previous day (Ctrl+Left)")
        prev_btn.clicked.connect(self.previous_day)
        nav_layout.addWidget(prev_btn)

        self.calendar_btn = QPushButton("📅 Calendar")
        self.calendar_btn.setToolTip("Open calendar to select date")
        self.calendar_btn.clicked.connect(self.show_calendar)
        nav_layout.addWidget(self.calendar_btn)

        today_btn = QPushButton("Today")
        today_btn.setToolTip("Go to today (Ctrl+H)")
        today_btn.clicked.connect(self.go_to_today)
        nav_layout.addWidget(today_btn)

        next_btn = QPushButton("Next Day ▶")
        next_btn.setToolTip("Go to next day (Ctrl+Right)")
        next_btn.clicked.connect(self.next_day)
        nav_layout.addWidget(next_btn)

        nav_layout.addStretch()

        sort_type_btn = QPushButton("⇅ Sort: Type")
        sort_type_btn.setToolTip("Sort all sections by entry type (Ctrl+G)")
        sort_type_btn.clicked.connect(self.sort_all_by_type)
        nav_layout.addWidget(sort_type_btn)

        sort_time_btn = QPushButton("⇅ Sort: Time")
        sort_time_btn.setToolTip("Sort all sections chronologically (Ctrl+Shift+G)")
        sort_time_btn.clicked.connect(self.sort_all_alphabetical)
        nav_layout.addWidget(sort_time_btn)

        unsort_btn = QPushButton("↩ Unsort")
        unsort_btn.setToolTip("Undo last sort (Ctrl+Z)")
        unsort_btn.clicked.connect(self.unsort_all_sections)
        nav_layout.addWidget(unsort_btn)

        week_btn = QPushButton("Week View")
        week_btn.setToolTip("Show week view (Ctrl+W)")
        week_btn.clicked.connect(self.show_week_view)
        nav_layout.addWidget(week_btn)

        month_btn = QPushButton("Month View")
        month_btn.setToolTip("Show month view (Ctrl+K)")
        month_btn.clicked.connect(self.show_month_view)
        nav_layout.addWidget(month_btn)

        main_layout.addWidget(self.nav_widget)

        # --- Header with date ---
        self.date_label = QLabel(f"📓 {datetime.now().strftime('%A, %B %d, %Y')}")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        self.date_label.setFont(header_font)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.date_label)

        # --- Entry input row ---
        self.input_widget = QWidget()
        input_layout = QHBoxLayout(self.input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)

        # Entry type selector (combobox - supports all types)
        type_label = QLabel("Type:")
        input_layout.addWidget(type_label)

        self.entry_type_combo = QComboBox()
        self.entry_type_combo.addItem("• Task", 'task')
        self.entry_type_combo.addItem("○ Event", 'event')
        self.entry_type_combo.addItem("— Note", 'note')
        self.entry_type_combo.addItem("= Mood", 'mood')
        self.entry_type_combo.addItem("! Urgent", 'urgent')
        self.entry_type_combo.addItem("* Priority", 'priority')
        self.entry_type_combo.setToolTip("Entry type")
        self.entry_type_combo.setMinimumWidth(110)
        input_layout.addWidget(self.entry_type_combo)

        # Keyboard shortcuts for entry types
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(lambda: self.set_entry_type('task'))
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(lambda: self.set_entry_type('event'))
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(lambda: self.set_entry_type('note'))

        # Section selector
        input_layout.addWidget(QLabel("  Section:"))
        self.section_combo = QComboBox()
        self.section_combo.addItems(self.SECTIONS)
        self._auto_select_section()
        self.section_combo.setToolTip("Which time-of-day section to add the entry to")
        input_layout.addWidget(self.section_combo)

        input_layout.addWidget(QLabel("  "))

        # Text input
        self.entry_input = QLineEdit()
        self.entry_input.setPlaceholderText("Type your entry and press Enter...")
        self.entry_input.returnPressed.connect(self.add_entry)
        input_layout.addWidget(self.entry_input, 1)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_entry)
        input_layout.addWidget(add_btn)

        main_layout.addWidget(self.input_widget)

        # ====== Three-section display area ======
        self.sections_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.section_widgets = {}  # name -> SectionListWidget

        for section_name in self.SECTIONS:
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(4, 4, 4, 4)
            frame_layout.setSpacing(2)

            # Section header with sort button
            header_row = QHBoxLayout()
            icon = {'Morning': '🌅', 'Afternoon': '☀️', 'Evening': '🌙'}[section_name]
            section_label = QLabel(f"{icon} {section_name}")
            section_label.setStyleSheet("font-weight: bold; font-size: 13px;")
            header_row.addWidget(section_label)
            header_row.addStretch()

            sort_sec_btn = QPushButton("⇅")
            sort_sec_btn.setToolTip(f"Sort {section_name}")
            sort_sec_btn.setFixedSize(36, 28)
            sort_menu = QMenu(sort_sec_btn)
            sort_menu.addAction(f"Sort by Type", lambda s=section_name: self.sort_section_by_type(s))
            sort_menu.addAction(f"Sort by Time", lambda s=section_name: self.sort_section_alphabetical(s))
            sort_menu.addSeparator()
            sort_menu.addAction(f"Undo Sort", lambda s=section_name: self.unsort_section(s))
            sort_sec_btn.setMenu(sort_menu)
            header_row.addWidget(sort_sec_btn)

            frame_layout.addLayout(header_row)

            # The list widget
            list_widget = SectionListWidget(section_name, self)
            list_widget.entries_changed.connect(self.save_current_day)
            list_widget.entry_selected.connect(self._on_entry_selected)
            self.section_widgets[section_name] = list_widget
            frame_layout.addWidget(list_widget)

            self.sections_splitter.addWidget(frame)

        main_layout.addWidget(self.sections_splitter, 1)

        # --- Action buttons section (compact, centered) ---
        self.action_widget = QWidget()
        action_main_layout = QVBoxLayout(self.action_widget)
        action_main_layout.setContentsMargins(0, 2, 0, 0)
        action_main_layout.setSpacing(2)

        # Selection info label
        self.selection_label = QLabel("Click on any entry to select it, or drag entries between sections")
        self.selection_label.setStyleSheet("color: gray; font-style: italic;")
        self.selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_main_layout.addWidget(self.selection_label)

        # Row 1: Modify Entry + Change Type — centered
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.addStretch()

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setFixedWidth(70)
        self.edit_btn.clicked.connect(self.edit_entry_text)
        self.edit_btn.setEnabled(False)
        row1.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Del")
        self.delete_btn.setFixedWidth(65)
        self.delete_btn.clicked.connect(self.delete_entry)
        self.delete_btn.setEnabled(False)
        row1.addWidget(self.delete_btn)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("color: #555;")
        row1.addWidget(sep1)

        self.action_buttons = []  # collect all type buttons for enable/disable

        for symbol, label in [('•', 'Task'), ('○', 'Event'), ('—', 'Note'),
                               ('=', 'Mood'), ('!', 'Urgent'), ('*', 'Priority')]:
            btn = QPushButton(f"{symbol} {label}")
            btn.setFixedWidth(80)
            btn.clicked.connect(lambda checked=False, s=symbol: self.change_symbol(s))
            btn.setEnabled(False)
            row1.addWidget(btn)
            self.action_buttons.append(btn)

        row1.addStretch()
        action_main_layout.addLayout(row1)

        # Row 2: Mark Status — centered
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addStretch()

        status_buttons_data = [
            ('complete_btn', '× Done', self.mark_complete),
            ('undone_btn', '• Un-done', self.mark_undone),
            ('migrate_btn', '> Migrate', self.mark_migrated),
            ('schedule_btn', '< Schedule', self.show_master_task_list),
            ('delegated_btn', '\\ Delegated', self.mark_delegated),
            ('waiting_btn', '| Waiting', self.mark_waiting),
        ]

        for attr, label, callback in status_buttons_data:
            btn = QPushButton(label)
            btn.setFixedWidth(95)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            row2.addWidget(btn)
            setattr(self, attr, btn)

        row2.addStretch()
        action_main_layout.addLayout(row2)

        main_layout.addWidget(self.action_widget)

        # --- Keyboard shortcuts ---
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.mark_complete)
        QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(self.mark_migrated)
        QShortcut(QKeySequence("Ctrl+Left"), self).activated.connect(self.previous_day)
        QShortcut(QKeySequence("Ctrl+Right"), self).activated.connect(self.next_day)

        # Setup system tray
        self.setup_tray()

        # Create status bar
        self.statusBar().showMessage("Ready — drag entries between Morning, Afternoon, and Evening")

        # Focus on input field
        self.entry_input.setFocus()

    # ------------------------------------------------------------------
    # Section helpers
    # ------------------------------------------------------------------

    def _auto_select_section(self):
        """Auto-select the section combo based on current wall-clock time."""
        hour = datetime.now().hour
        if hour < 12:
            self.section_combo.setCurrentIndex(0)  # Morning
        elif hour < 17:
            self.section_combo.setCurrentIndex(1)  # Afternoon
        else:
            self.section_combo.setCurrentIndex(2)  # Evening

    def _section_for_time(self, time_str):
        """Given a time string like '14:30', return the section name."""
        try:
            hour = int(time_str.split(':')[0])
            if hour < 12:
                return 'Morning'
            elif hour < 17:
                return 'Afternoon'
            else:
                return 'Evening'
        except (ValueError, IndexError):
            return 'Morning'

    def _on_entry_selected(self, entry_text, list_widget):
        """Handle selection from any of the three section lists."""
        # Deselect in the other two lists
        for name, lw in self.section_widgets.items():
            if lw is not list_widget:
                lw.clearSelection()

        if entry_text:
            self.selected_entry = entry_text
            self.selected_section = list_widget
            display = entry_text[:60] + ('...' if len(entry_text) > 60 else '')
            self.selection_label.setText(
                f"Selected ({list_widget.section_name}): {display}"
            )
            self.update_action_buttons(True)
        else:
            self.selected_entry = None
            self.selected_section = None
            self.selection_label.setText("Click on any entry to select it, or drag entries between sections")
            self.update_action_buttons(False)

    # ------------------------------------------------------------------
    # File I/O  — section-aware markdown format
    # ------------------------------------------------------------------

    def load_current_day(self):
        """Load entries for the current day, distributing into sections."""
        for lw in self.section_widgets.values():
            lw.blockSignals(True)
            lw.clear()
            lw.blockSignals(False)

        # Update window title and date label
        self.setWindowTitle(f"Kbullet - {self.current_date.strftime('%Y-%m-%d')}")
        self.date_label.setText(f"📓 {self.current_date.strftime('%A, %B %d, %Y')}")

        if not self.current_file.exists():
            self.selected_entry = None
            self.selected_section = None
            self.update_action_buttons(False)
            return

        with open(self.current_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse sectioned format
        sections = self._parse_sections(content)

        for section_name in self.SECTIONS:
            lw = self.section_widgets[section_name]
            lw.blockSignals(True)
            for entry in sections.get(section_name, []):
                lw.add_entry(entry)
            lw.blockSignals(False)

        # Reset selection
        self.selected_entry = None
        self.selected_section = None
        self.update_action_buttons(False)

    def _parse_sections(self, content):
        """Parse a markdown file into {section_name: [entries]}.

        Supports two formats:
          1. Sectioned: lines under ## Morning / ## Afternoon / ## Evening headers.
          2. Legacy (no headers): auto-assign by timestamp, fallback to Morning.
        """
        lines = content.splitlines()
        has_headers = any(
            line.strip().startswith('## ') and line.strip()[3:] in self.SECTIONS
            for line in lines
        )

        sections = {s: [] for s in self.SECTIONS}

        if has_headers:
            current_section = 'Morning'
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('## '):
                    name = stripped[3:].strip()
                    if name in self.SECTIONS:
                        current_section = name
                        continue
                if stripped and stripped[0] in '•○—=!*×><\\|':
                    sections[current_section].append(stripped)
        else:
            # Legacy format — auto-assign by timestamp
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped[0] not in '•○—=!*×><\\|':
                    continue
                # Try to extract time from [HH:MM]
                section = 'Morning'
                if '[' in stripped and ']' in stripped:
                    bracket_start = stripped.index('[')
                    bracket_end = stripped.index(']')
                    time_str = stripped[bracket_start + 1:bracket_end]
                    if ':' in time_str and len(time_str) <= 5:
                        section = self._section_for_time(time_str)
                sections[section].append(stripped)

        return sections

    def save_current_day(self):
        """Save all three sections back to the markdown file."""
        lines = []
        for section_name in self.SECTIONS:
            lw = self.section_widgets[section_name]
            entries = lw.get_entries()
            lines.append(f"## {section_name}")
            for entry in entries:
                lines.append(entry)
            lines.append('')  # blank line between sections

        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def _get_all_entries_flat(self):
        """Return all entries as a flat string for printing / legacy use."""
        lines = []
        for section_name in self.SECTIONS:
            lw = self.section_widgets[section_name]
            entries = lw.get_entries()
            if entries:
                lines.append(f"--- {section_name} ---")
                lines.extend(entries)
                lines.append('')
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Sort
    # ------------------------------------------------------------------

    def sort_section_by_type(self, section_name):
        """Sort a single section by entry type."""
        self.section_widgets[section_name].sort_by_type()
        self.statusBar().showMessage(f"Sorted {section_name} by entry type (Ctrl+Z to undo)", 2000)

    def sort_section_alphabetical(self, section_name):
        """Sort a single section chronologically/alphabetically."""
        self.section_widgets[section_name].sort_alphabetical()
        self.statusBar().showMessage(f"Sorted {section_name} by time (Ctrl+Z to undo)", 2000)

    def unsort_section(self, section_name):
        """Undo sort on a single section."""
        if self.section_widgets[section_name].unsort():
            self.statusBar().showMessage(f"{section_name} sort undone", 2000)
        else:
            self.statusBar().showMessage(f"Nothing to unsort in {section_name}", 2000)

    def sort_all_by_type(self):
        """Sort all three sections by entry type."""
        for lw in self.section_widgets.values():
            lw.sort_by_type()
        self.statusBar().showMessage("All sections sorted by entry type (Ctrl+Z to undo)", 3000)

    def sort_all_alphabetical(self):
        """Sort all three sections chronologically/alphabetically."""
        for lw in self.section_widgets.values():
            lw.sort_alphabetical()
        self.statusBar().showMessage("All sections sorted by time (Ctrl+Z to undo)", 3000)

    def unsort_all_sections(self):
        """Undo sort on all sections."""
        restored = False
        for lw in self.section_widgets.values():
            if lw.unsort():
                restored = True
        if restored:
            self.statusBar().showMessage("Sort undone — original order restored", 2000)
        else:
            self.statusBar().showMessage("Nothing to unsort", 2000)

    # ------------------------------------------------------------------
    # Entry CRUD
    # ------------------------------------------------------------------

    def set_entry_type(self, entry_type):
        """Set the current entry type"""
        index = self.entry_type_combo.findData(entry_type)
        if index >= 0:
            self.entry_type_combo.setCurrentIndex(index)
            self.statusBar().showMessage(f"Entry type: {entry_type.capitalize()}", 2000)

    def get_current_entry_type(self):
        """Get the currently selected entry type"""
        return self.entry_type_combo.currentData() or 'task'

    def add_entry(self):
        """Add a new entry to the selected section."""
        text = self.entry_input.text().strip()
        if not text:
            return

        entry_type = self.get_current_entry_type()
        section = self.section_combo.currentText()
        self._add_entry_to_section(text, entry_type, section)
        self.entry_input.clear()

    def _add_entry_to_section(self, text, entry_type, section_name):
        """Create a formatted entry and add it to a specific section."""
        symbol = self.NOTATION.get(entry_type, '•')
        timestamp = datetime.now().strftime('%H:%M')

        if self.show_timestamps:
            entry = f"{symbol} [{timestamp}] {text}"
        else:
            entry = f"{symbol} {text}"

        lw = self.section_widgets[section_name]
        lw.add_entry(entry)
        self.save_current_day()
        self.statusBar().showMessage(f"Added {entry_type} to {section_name}: {text}", 2000)

    def add_entry_with_type(self, text, entry_type):
        """Add entry with specific type, auto-selecting section by time."""
        hour = datetime.now().hour
        if hour < 12:
            section = 'Morning'
        elif hour < 17:
            section = 'Afternoon'
        else:
            section = 'Evening'
        self._add_entry_to_section(text, entry_type, section)

    def update_action_buttons(self, enabled):
        """Enable or disable action buttons"""
        self.edit_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        for btn in self.action_buttons:
            btn.setEnabled(enabled)
        self.complete_btn.setEnabled(enabled)
        self.undone_btn.setEnabled(enabled)
        self.migrate_btn.setEnabled(enabled)
        self.schedule_btn.setEnabled(enabled)
        self.delegated_btn.setEnabled(enabled)
        self.waiting_btn.setEnabled(enabled)

    def edit_entry_text(self):
        """Edit the text of selected entry"""
        if not self.selected_entry or not self.selected_section:
            return

        # Extract current text (remove symbol and timestamp)
        parts = self.selected_entry.split('] ', 1)
        if len(parts) > 1:
            current_text = parts[1]
        else:
            current_text = self.selected_entry[2:].strip()

        text, ok = QInputDialog.getText(self, "Edit Entry", "Edit entry text:", text=current_text)
        if ok and text:
            old_entry = self.selected_entry
            symbol = old_entry[0]
            if '] ' in old_entry:
                timestamp = old_entry.split(']')[0] + ']'
                new_entry = f"{symbol} {timestamp} {text}"
            else:
                new_entry = f"{symbol} {text}"

            self.selected_section.find_and_replace(old_entry, new_entry)
            self.selected_entry = new_entry
            self.save_current_day()
            self.statusBar().showMessage("Entry updated", 2000)

    def delete_entry(self):
        """Delete the selected entry"""
        if not self.selected_entry or not self.selected_section:
            return

        reply = QMessageBox.question(
            self, "Delete Entry",
            f"Delete this entry?\n\n{self.selected_entry}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.selected_section.find_and_remove(self.selected_entry)
            self.selected_entry = None
            self.selected_section = None
            self.update_action_buttons(False)
            self.save_current_day()
            self.statusBar().showMessage("Entry deleted", 2000)

    def change_symbol(self, new_symbol):
        """Change the symbol of selected entry"""
        if not self.selected_entry or not self.selected_section:
            return

        old_entry = self.selected_entry
        new_entry = new_symbol + old_entry[1:]
        self.selected_section.find_and_replace(old_entry, new_entry)
        self.selected_entry = new_entry
        self.save_current_day()
        self.statusBar().showMessage(f"Symbol changed to {new_symbol}", 2000)

    def mark_complete(self):
        """Mark selected entry as complete"""
        if not self.selected_entry:
            return
        self.change_symbol('×')

    def mark_undone(self):
        """Revert any entry back to a task"""
        if not self.selected_entry:
            return
        self.change_symbol('•')
        self.statusBar().showMessage("Entry reverted to task", 2000)

    def mark_delegated(self):
        """Mark selected entry as delegated"""
        if not self.selected_entry:
            return
        self.change_symbol('\\')
        self.statusBar().showMessage("Entry marked as delegated", 2000)

    def mark_waiting(self):
        """Mark selected entry as waiting for"""
        if not self.selected_entry:
            return
        self.change_symbol('|')
        self.statusBar().showMessage("Entry marked as waiting", 2000)

    def mark_migrated(self):
        """Mark selected entry as migrated to another date"""
        if not self.selected_entry or not self.selected_section:
            return

        entry_to_migrate = self.selected_entry
        section_widget = self.selected_section

        dialog = CalendarDialog(datetime.now(), self)
        dialog.setWindowTitle("Select Migration Date")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = dialog.get_selected_date()
            target_date = datetime(selected_date.year(), selected_date.month(), selected_date.day())
            target_file = self.journal_dir / f"{target_date.strftime('%Y-%m-%d')}.md"

            # Get entry text (remove symbol and timestamp if present)
            if '] ' in entry_to_migrate:
                entry_text = entry_to_migrate.split('] ', 1)[1]
            else:
                entry_text = entry_to_migrate[2:].strip()

            # Add to target date file (in Morning section by default)
            timestamp = datetime.now().strftime('%H:%M')
            if self.show_timestamps:
                new_entry = f"• [{timestamp}] {entry_text}"
            else:
                new_entry = f"• {entry_text}"

            self._append_entry_to_file(target_file, 'Morning', new_entry)

            # Mark original as migrated in current section
            migrated_entry = '>' + entry_to_migrate[1:] + f" → {target_date.strftime('%Y-%m-%d')}"
            section_widget.find_and_replace(entry_to_migrate, migrated_entry)
            self.selected_entry = migrated_entry
            self.save_current_day()
            self.statusBar().showMessage(f"Task migrated to {target_date.strftime('%Y-%m-%d')}", 2000)

    def _append_entry_to_file(self, file_path, section_name, entry_text):
        """Append an entry to a specific section in a date file, creating sections if needed."""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            sections = self._parse_sections(content)
        else:
            sections = {s: [] for s in self.SECTIONS}

        sections[section_name].append(entry_text)

        # Write back
        lines = []
        for sec in self.SECTIONS:
            lines.append(f"## {sec}")
            for e in sections.get(sec, []):
                lines.append(e)
            lines.append('')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def previous_day(self):
        """Go to previous day"""
        self.current_date -= timedelta(days=1)
        self.current_file = self.journal_dir / f"{self.current_date.strftime('%Y-%m-%d')}.md"
        self.load_current_day()

    def next_day(self):
        """Go to next day"""
        self.current_date += timedelta(days=1)
        self.current_file = self.journal_dir / f"{self.current_date.strftime('%Y-%m-%d')}.md"
        self.load_current_day()

    def go_to_today(self):
        """Go to today's journal"""
        self.current_date = datetime.now()
        self.today = self.current_date.strftime('%Y-%m-%d')
        self.current_file = self.journal_dir / f"{self.today}.md"
        self.load_current_day()
        self._auto_select_section()

    def show_calendar(self):
        """Show calendar dialog to select date"""
        dialog = CalendarDialog(self.current_date, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = dialog.get_selected_date()
            self.current_date = datetime(selected_date.year(), selected_date.month(), selected_date.day())
            self.current_file = self.journal_dir / f"{self.current_date.strftime('%Y-%m-%d')}.md"
            self.load_current_day()

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def show_master_task_list(self):
        """Show master task list dialog"""
        dialog = MasterTaskListDialog(self.journal_dir, self.show_timestamps, self)
        dialog.exec()
        self.load_current_day()

    def show_week_view(self):
        """Show week view dialog"""
        dialog = WeekViewDialog(self.journal_dir, self.current_date, self.show_timestamps, self)
        dialog.exec()

    def show_month_view(self):
        """Show month view dialog"""
        dialog = MonthViewDialog(self.journal_dir, self.current_date, self.show_timestamps, self)
        dialog.exec()

    def print_current_view(self):
        """Print current day's entries"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)

            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                document = QTextDocument()
                document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())

                date_text = self.date_label.text().replace('📓 ', '')

                html = f"""<!DOCTYPE html>
<html><head><style>
body {{ font-family: sans-serif; margin: 20px; }}
h1 {{ font-size: 16pt; margin-bottom: 10px; }}
h2 {{ font-size: 12pt; margin-top: 15px; color: #555; }}
hr {{ border: 1px solid #ccc; }}
pre {{ font-family: monospace; font-size: 10pt; white-space: pre-wrap; word-wrap: break-word; }}
</style></head><body>
<h1>{date_text}</h1><hr>"""

                for section_name in self.SECTIONS:
                    icon = {'Morning': '🌅', 'Afternoon': '☀️', 'Evening': '🌙'}[section_name]
                    entries = self.section_widgets[section_name].get_entries()
                    html += f"<h2>{icon} {section_name}</h2>"
                    if entries:
                        escaped = '\n'.join(entries).replace('<', '&lt;').replace('>', '&gt;')
                        html += f"<pre>{escaped}</pre>"
                    else:
                        html += "<p><i>No entries</i></p>"

                html += "</body></html>"
                document.setHtml(html)
                document.print(printer)
                self.statusBar().showMessage("Printed successfully", 2000)
        except Exception as e:
            QMessageBox.warning(self, "Print Error", f"Failed to print: {str(e)}")

    def show_search(self):
        """Show search dialog"""
        dialog = SearchDialog(self.journal_dir, self)
        dialog.exec()

    def show_unfinished_tasks(self):
        """Show unfinished tasks dialog"""
        dialog = UnfinishedTasksDialog(self.journal_dir, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_file = dialog.get_selected_file()
            if selected_file:
                self.current_date = datetime.strptime(selected_file.stem, '%Y-%m-%d')
                self.current_file = selected_file
                self.load_current_day()

    def open_file(self):
        """Open a specific journal file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Journal File",
            str(self.journal_dir),
            "Markdown Files (*.md);;All Files (*)"
        )
        if file_path:
            file_path = Path(file_path)
            try:
                date_str = file_path.stem
                self.current_date = datetime.strptime(date_str, '%Y-%m-%d')
                self.current_file = file_path
                self.load_current_day()
            except ValueError:
                QMessageBox.warning(
                    self, "Invalid File",
                    "File name must be in YYYY-MM-DD.md format."
                )

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.journal_dir, self.show_timestamps, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_dir, show_timestamps = dialog.get_settings()

            if new_dir != self.journal_dir:
                self.journal_dir = new_dir
                self.journal_dir.mkdir(parents=True, exist_ok=True)
                self.settings.setValue('journal_dir', str(self.journal_dir))
                self.current_file = self.journal_dir / f"{self.current_date.strftime('%Y-%m-%d')}.md"

            self.show_timestamps = show_timestamps
            self.settings.setValue('show_timestamps', show_timestamps)

            self.load_current_day()
            self.statusBar().showMessage("Settings saved", 2000)

    # ------------------------------------------------------------------
    # Help dialogs
    # ------------------------------------------------------------------

    def show_notation_help(self):
        """Show bullet journal notation help"""
        help_text = """
<h2>Bullet Journal Notation</h2>
<p>Kbullet uses Ryder Carroll's Bullet Journal notation with extensions:</p>
<h3>Entry Types</h3>
<table>
<tr><td><b>•</b></td><td>Task — something you need to do</td></tr>
<tr><td><b>○</b></td><td>Event — something scheduled or that happened</td></tr>
<tr><td><b>—</b></td><td>Note — information to remember</td></tr>
<tr><td><b>=</b></td><td>Mood — emotional state or feeling</td></tr>
<tr><td><b>!</b></td><td>Urgent — needs immediate attention</td></tr>
<tr><td><b>*</b></td><td>Priority — important but not urgent</td></tr>
</table>
<h3>Status Markers</h3>
<table>
<tr><td><b>×</b></td><td>Done — task is complete</td></tr>
<tr><td><b>&gt;</b></td><td>Migrated — moved to another day</td></tr>
<tr><td><b>&lt;</b></td><td>Scheduled — moved to a future date</td></tr>
<tr><td><b>\\</b></td><td>Delegated — handed off to someone else</td></tr>
<tr><td><b>|</b></td><td>Waiting — waiting for someone/something</td></tr>
</table>
<h3>Sections</h3>
<table>
<tr><td><b>🌅 Morning</b></td><td>Before noon</td></tr>
<tr><td><b>☀️ Afternoon</b></td><td>12:00 – 17:00</td></tr>
<tr><td><b>🌙 Evening</b></td><td>After 17:00</td></tr>
</table>
<p>Drag entries between sections to reorganise your day!<br>
Right-click any entry for quick actions.</p>
"""
        QMessageBox.about(self, "Notation Help", help_text)

    def show_shortcuts_help(self):
        """Show keyboard shortcuts help"""
        help_text = """
<h2>Keyboard Shortcuts</h2>
<table>
<tr><td><b>Ctrl+T</b></td><td>Select Task type</td></tr>
<tr><td><b>Ctrl+E</b></td><td>Select Event type</td></tr>
<tr><td><b>Ctrl+N</b></td><td>Select Note type</td></tr>
<tr><td><b>Ctrl+D</b></td><td>Mark selected as Done</td></tr>
<tr><td><b>Ctrl+M</b></td><td>Migrate selected task</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Show Master Task List</td></tr>
<tr><td><b>Ctrl+G</b></td><td>Sort all sections by type</td></tr>
<tr><td><b>Ctrl+Shift+G</b></td><td>Sort all sections by time</td></tr>
<tr><td><b>Ctrl+Z</b></td><td>Undo last sort</td></tr>
<tr><td><b>Ctrl+Left</b></td><td>Previous day</td></tr>
<tr><td><b>Ctrl+Right</b></td><td>Next day</td></tr>
<tr><td><b>Ctrl+H</b></td><td>Go to today</td></tr>
<tr><td><b>Ctrl+F</b></td><td>Search journal</td></tr>
<tr><td><b>Ctrl+U</b></td><td>Unfinished tasks</td></tr>
<tr><td><b>Ctrl+W</b></td><td>Week view</td></tr>
<tr><td><b>Ctrl+K</b></td><td>Month view</td></tr>
<tr><td><b>Ctrl+O</b></td><td>Open file</td></tr>
<tr><td><b>Ctrl+P</b></td><td>Print</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Quit</td></tr>
</table>
<p><b>Tip:</b> Right-click any entry for quick access to all actions!</p>
"""
        QMessageBox.about(self, "Keyboard Shortcuts", help_text)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Kbullet",
            "<h2>Kbullet</h2>"
            f"<p>Version {__version__}</p>"
            "<p>A bullet journal for the Linux desktop</p>"
            "<p>Uses Ryder Carroll's Bullet Journal notation with extensions</p>"
            "<p><b>Features:</b> Morning/Afternoon/Evening sections, "
            "drag-and-drop, sort by type or time, right-click context menus, "
            "11 entry symbols, colour-coded entries</p>"
            "<hr>"
            "<p>Copyright (C) 2026 brightwalker25</p>"
            "<p>This program comes with ABSOLUTELY NO WARRANTY. It is free "
            "software, and you are welcome to redistribute it under the terms "
            "of the GNU General Public License version 3 or later.</p>"
            "<p>See &lt;<a href='https://www.gnu.org/licenses/gpl-3.0.html'>"
            "gnu.org/licenses/gpl-3.0.html</a>&gt; for details.</p>"
        )

    # ------------------------------------------------------------------
    # System tray
    # ------------------------------------------------------------------

    def setup_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)

        icon = QIcon.fromTheme("accessories-text-editor")
        if icon.isNull():
            icon = QIcon.fromTheme("text-x-generic")
        if icon.isNull():
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#4a90d9"))
            icon = QIcon(pixmap)

        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)

        tray_menu = QMenu()

        show_action = QAction("Show Kbullet", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quick_task = QAction("Quick Task...", self)
        quick_task.triggered.connect(self.quick_add_task)
        tray_menu.addAction(quick_task)

        quick_event = QAction("Quick Event...", self)
        quick_event.triggered.connect(self.quick_add_event)
        tray_menu.addAction(quick_event)

        quick_note = QAction("Quick Note...", self)
        quick_note.triggered.connect(self.quick_add_note)
        tray_menu.addAction(quick_note)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_activated)

    def toggle_menubar(self):
        """Toggle menu bar visibility"""
        is_visible = self.menuBar().isVisible()
        self.menuBar().setVisible(not is_visible)
        self.toggle_menubar_action.setChecked(not is_visible)

    def tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def quick_add_task(self):
        text, ok = QInputDialog.getText(self, "Quick Task", "Enter task:")
        if ok and text:
            self.add_entry_with_type(text, 'task')

    def quick_add_event(self):
        text, ok = QInputDialog.getText(self, "Quick Event", "Enter event:")
        if ok and text:
            self.add_entry_with_type(text, 'event')

    def quick_add_note(self):
        text, ok = QInputDialog.getText(self, "Quick Note", "Enter note:")
        if ok and text:
            self.add_entry_with_type(text, 'note')

    def resizeEvent(self, event):
        """Auto-hide nav, input, date, and actions when the window is narrow."""
        super().resizeEvent(event)
        compact = event.size().width() < 700
        self.nav_widget.setVisible(not compact)
        self.date_label.setVisible(not compact)
        self.input_widget.setVisible(not compact)
        self.action_widget.setVisible(not compact)
        if compact:
            self.menuBar().setVisible(False)
        else:
            self.menuBar().setVisible(self.toggle_menubar_action.isChecked())

    def quit_app(self):
        """Actually exit, rather than hiding to the tray."""
        self._really_quit = True
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """Hide to tray on a window close, but let a real quit through."""
        if self._really_quit:
            event.accept()
            return
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Kbullet",
            "Running in system tray. Double-click to show.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )


# ===========================================================================
# Supporting dialogs (unchanged logic, section-aware where needed)
# ===========================================================================

class CalendarDialog(QDialog):
    """Calendar dialog for date selection"""

    def __init__(self, current_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setModal(True)

        layout = QVBoxLayout(self)

        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate(current_date.year, current_date.month, current_date.day))
        self.calendar.activated.connect(self.accept)
        layout.addWidget(self.calendar)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_selected_date(self):
        return self.calendar.selectedDate()


class SearchDialog(QDialog):
    """Search dialog for finding entries across all journal files"""

    def __init__(self, journal_dir, parent=None):
        super().__init__(parent)
        self.journal_dir = journal_dir

        self.setWindowTitle("Search Journal")
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")
        self.search_input.returnPressed.connect(self.do_search)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.do_search)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def do_search(self):
        term = self.search_input.text().strip().lower()
        if not term:
            return
        self.results_list.clear()
        for file_path in sorted(self.journal_dir.glob('*.md'), reverse=True):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if term in line.lower() and not line.strip().startswith('## '):
                        item = QListWidgetItem(f"[{file_path.stem}] {line.strip()}")
                        item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                        self.results_list.addItem(item)


class UnfinishedTasksDialog(QDialog):
    """Dialog showing all unfinished tasks"""

    def __init__(self, journal_dir, parent=None):
        super().__init__(parent)
        self.journal_dir = journal_dir
        self.selected_file = None

        self.setWindowTitle("Unfinished Tasks")
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        header = QLabel("All unfinished tasks (• symbol) across your journal:")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        self.task_list = QListWidget()
        self.task_list.itemDoubleClicked.connect(self.go_to_task)
        layout.addWidget(self.task_list)

        button_layout = QHBoxLayout()
        go_btn = QPushButton("Go to Date")
        go_btn.clicked.connect(self.go_to_selected)
        button_layout.addWidget(go_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.load_tasks()

    def load_tasks(self):
        self.task_list.clear()
        for file_path in sorted(self.journal_dir.glob('*.md'), reverse=True):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('•'):
                        item = QListWidgetItem(f"[{file_path.stem}] {line}")
                        item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                        self.task_list.addItem(item)

    def go_to_task(self, item):
        self.selected_file = Path(item.data(Qt.ItemDataRole.UserRole))
        self.accept()

    def go_to_selected(self):
        item = self.task_list.currentItem()
        if item:
            self.go_to_task(item)

    def get_selected_file(self):
        return self.selected_file


class MasterTaskListDialog(QDialog):
    """Master list of all uncompleted tasks across all dates"""

    SECTIONS = ['Morning', 'Afternoon', 'Evening']

    def __init__(self, journal_dir, show_timestamps, parent=None):
        super().__init__(parent)
        self.journal_dir = journal_dir
        self.show_timestamps = show_timestamps
        self.parent_window = parent
        self.tasks = []

        self.setWindowTitle("Master Task List - All Uncompleted Tasks")
        self.setModal(True)
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        header = QLabel("All uncompleted tasks (• symbol) from your entire journal")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        info = QLabel("Select a task and click 'Schedule' to move it to a specific date")
        info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info)

        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.task_list)

        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload all tasks")
        refresh_btn.clicked.connect(self.load_tasks)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        schedule_btn = QPushButton("📅 Schedule Selected Task")
        schedule_btn.setToolTip("Move selected task to a specific date")
        schedule_btn.clicked.connect(self.schedule_task)
        button_layout.addWidget(schedule_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.load_tasks()

    def _parse_sections(self, content):
        """Parse sections from file content."""
        lines = content.splitlines()
        has_headers = any(
            line.strip().startswith('## ') and line.strip()[3:] in self.SECTIONS
            for line in lines
        )
        sections = {s: [] for s in self.SECTIONS}
        if has_headers:
            current_section = 'Morning'
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('## ') and stripped[3:] in self.SECTIONS:
                    current_section = stripped[3:]
                    continue
                if stripped and stripped[0] in '•○—=!*×><\\|':
                    sections[current_section].append(stripped)
        else:
            for line in lines:
                stripped = line.strip()
                if stripped and stripped[0] in '•○—=!*×><\\|':
                    sections['Morning'].append(stripped)
        return sections

    def load_tasks(self):
        self.task_list.clear()
        self.tasks = []

        for file_path in sorted(self.journal_dir.glob('*.md'), reverse=True):
            date_str = file_path.stem
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            sections = self._parse_sections(content)
            for sec_name in self.SECTIONS:
                for line in sections[sec_name]:
                    if line.startswith('•'):
                        self.tasks.append({
                            'date': date_str,
                            'file': file_path,
                            'line': line,
                            'section': sec_name
                        })
                        item = QListWidgetItem(f"[{date_str}] ({sec_name}) {line}")
                        item.setData(Qt.ItemDataRole.UserRole, len(self.tasks) - 1)
                        self.task_list.addItem(item)

        self.stats_label.setText(f"Total uncompleted tasks: {len(self.tasks)}")

    def schedule_task(self):
        item = self.task_list.currentItem()
        if not item:
            QMessageBox.information(self, "Info", "Please select a task first.")
            return

        task_index = item.data(Qt.ItemDataRole.UserRole)
        task = self.tasks[task_index]

        dialog = CalendarDialog(datetime.now(), self)
        dialog.setWindowTitle("Select Schedule Date")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_date = dialog.get_selected_date()
            target_date = datetime(selected_date.year(), selected_date.month(), selected_date.day())
            target_file = self.journal_dir / f"{target_date.strftime('%Y-%m-%d')}.md"

            entry = task['line']
            if '] ' in entry:
                entry_text = entry.split('] ', 1)[1]
            else:
                entry_text = entry[2:].strip()

            timestamp = datetime.now().strftime('%H:%M')
            if self.show_timestamps:
                new_entry = f"• [{timestamp}] {entry_text}"
            else:
                new_entry = f"• {entry_text}"

            # Append to target file
            if self.parent_window:
                self.parent_window._append_entry_to_file(target_file, 'Morning', new_entry)
            else:
                with open(target_file, 'a', encoding='utf-8') as f:
                    f.write(new_entry + '\n')

            # Mark original as scheduled in its file
            original_file = task['file']
            with open(original_file, 'r', encoding='utf-8') as f:
                content = f.read()

            scheduled_entry = '<' + entry[1:] + f" → {target_date.strftime('%Y-%m-%d')}"
            content = content.replace(entry, scheduled_entry)

            with open(original_file, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(
                self, "Task Scheduled",
                f"Task scheduled to {target_date.strftime('%Y-%m-%d')}"
            )
            self.load_tasks()


class WeekViewDialog(QDialog):
    """Week view dialog"""

    SECTIONS = ['Morning', 'Afternoon', 'Evening']

    def __init__(self, journal_dir, current_date, show_timestamps, parent=None):
        super().__init__(parent)
        self.journal_dir = journal_dir
        self.current_date = current_date
        self.show_timestamps = show_timestamps

        self.setWindowTitle("Week View")
        self.setModal(True)
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        # Navigation
        nav_layout = QHBoxLayout()
        prev_btn = QPushButton("◀ Previous Week")
        prev_btn.clicked.connect(self.previous_week)
        nav_layout.addWidget(prev_btn)

        self.week_label = QLabel()
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        nav_layout.addWidget(self.week_label)

        next_btn = QPushButton("Next Week ▶")
        next_btn.clicked.connect(self.next_week)
        nav_layout.addWidget(next_btn)

        layout.addLayout(nav_layout)

        # Content
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_area.setWidget(self.content_widget)
        layout.addWidget(self.content_area)

        # Buttons
        button_layout = QHBoxLayout()
        print_btn = QPushButton("🖨️ Print Week")
        print_btn.clicked.connect(self.print_week)
        button_layout.addWidget(print_btn)
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.load_week()

    def _parse_sections(self, content):
        lines = content.splitlines()
        has_headers = any(
            line.strip().startswith('## ') and line.strip()[3:] in self.SECTIONS
            for line in lines
        )
        sections = {s: [] for s in self.SECTIONS}
        if has_headers:
            current_section = 'Morning'
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('## ') and stripped[3:] in self.SECTIONS:
                    current_section = stripped[3:]
                    continue
                if stripped and stripped[0] in '•○—=!*×><\\|':
                    sections[current_section].append(stripped)
        else:
            for line in lines:
                stripped = line.strip()
                if stripped and stripped[0] in '•○—=!*×><\\|':
                    sections['Morning'].append(stripped)
        return sections

    def load_week(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        day_of_week = self.current_date.weekday()
        week_start = self.current_date - timedelta(days=day_of_week)

        self.week_label.setText(
            f"Week of {week_start.strftime('%B %d, %Y')} - "
            f"{(week_start + timedelta(days=6)).strftime('%B %d, %Y')}"
        )

        for i in range(7):
            day = week_start + timedelta(days=i)
            day_file = self.journal_dir / f"{day.strftime('%Y-%m-%d')}.md"

            header = QLabel(f"📅 {day.strftime('%A, %B %d')}")
            header.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 10px;")
            self.content_layout.addWidget(header)

            content = QTextEdit()
            content.setReadOnly(True)
            content.setMaximumHeight(150)
            content.setFont(QFont("Monospace", 10))

            if day_file.exists():
                with open(day_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                sections = self._parse_sections(file_content)
                display_lines = []
                for sec in self.SECTIONS:
                    entries = sections.get(sec, [])
                    if entries:
                        display_lines.append(f"  [{sec}]")
                        display_lines.extend(f"    {e}" for e in entries)
                if display_lines:
                    content.setPlainText('\n'.join(display_lines))
                else:
                    content.setPlainText("No entries")
                    content.setStyleSheet("color: gray;")
            else:
                content.setPlainText("No entries")
                content.setStyleSheet("color: gray;")

            self.content_layout.addWidget(content)

        self.content_layout.addStretch()

    def previous_week(self):
        self.current_date -= timedelta(weeks=1)
        self.load_week()

    def next_week(self):
        self.current_date += timedelta(weeks=1)
        self.load_week()

    def print_week(self):
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            dialog = QPrintDialog(printer, self)

            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                document = QTextDocument()
                document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())

                day_of_week = self.current_date.weekday()
                week_start = self.current_date - timedelta(days=day_of_week)

                html = f"""<!DOCTYPE html>
<html><head><style>
body {{ font-family: sans-serif; margin: 20px; }}
h1 {{ font-size: 14pt; }}
h2 {{ font-size: 12pt; margin-top: 15px; }}
h3 {{ font-size: 10pt; color: #555; margin-top: 5px; margin-bottom: 2px; }}
hr {{ border: 1px solid #ccc; }}
pre {{ font-family: monospace; font-size: 9pt; white-space: pre-wrap; word-wrap: break-word; }}
</style></head><body>
<h1>{self.week_label.text()}</h1><hr>"""

                for i in range(7):
                    day = week_start + timedelta(days=i)
                    day_file = self.journal_dir / f"{day.strftime('%Y-%m-%d')}.md"

                    html += f"<h2>{day.strftime('%A, %B %d')}</h2>"

                    if day_file.exists():
                        with open(day_file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        sections = self._parse_sections(file_content)
                        for sec in self.SECTIONS:
                            entries = sections.get(sec, [])
                            if entries:
                                icon = {'Morning': '🌅', 'Afternoon': '☀️', 'Evening': '🌙'}[sec]
                                html += f"<h3>{icon} {sec}</h3>"
                                escaped = '\n'.join(entries).replace('<', '&lt;').replace('>', '&gt;')
                                html += f"<pre>{escaped}</pre>"
                    else:
                        html += "<p><i>No entries</i></p>"

                html += "</body></html>"
                document.setHtml(html)
                document.print(printer)
        except Exception as e:
            QMessageBox.warning(self, "Print Error", f"Failed to print: {str(e)}")


class MonthViewDialog(QDialog):
    """Month view dialog with statistics"""

    SECTIONS = ['Morning', 'Afternoon', 'Evening']

    def __init__(self, journal_dir, current_date, show_timestamps, parent=None):
        super().__init__(parent)
        self.journal_dir = journal_dir
        self.current_date = current_date
        self.show_timestamps = show_timestamps

        self.setWindowTitle("Month View")
        self.setModal(True)
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        # Navigation
        nav_layout = QHBoxLayout()
        prev_btn = QPushButton("◀ Previous Month")
        prev_btn.clicked.connect(self.previous_month)
        nav_layout.addWidget(prev_btn)

        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        nav_layout.addWidget(self.month_label)

        next_btn = QPushButton("Next Month ▶")
        next_btn.clicked.connect(self.next_month)
        nav_layout.addWidget(next_btn)

        layout.addLayout(nav_layout)

        # Stats
        self.stats_widget = QWidget()
        stats_layout = QHBoxLayout(self.stats_widget)
        self.total_entries_label = QLabel()
        stats_layout.addWidget(self.total_entries_label)
        self.tasks_label = QLabel()
        stats_layout.addWidget(self.tasks_label)
        self.completed_label = QLabel()
        stats_layout.addWidget(self.completed_label)
        self.completion_rate_label = QLabel()
        stats_layout.addWidget(self.completion_rate_label)
        layout.addWidget(self.stats_widget)

        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate(current_date.year, current_date.month, current_date.day))
        self.calendar.clicked.connect(self.date_clicked)
        layout.addWidget(self.calendar)

        # Day preview
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(200)
        self.preview.setFont(QFont("Monospace", 10))
        layout.addWidget(self.preview)

        # Buttons
        button_layout = QHBoxLayout()
        print_btn = QPushButton("🖨️ Print Month")
        print_btn.clicked.connect(self.print_month)
        button_layout.addWidget(print_btn)
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.load_month()

    def load_month(self):
        year = self.current_date.year
        month = self.current_date.month
        self.month_label.setText(f"{self.current_date.strftime('%B %Y')}")

        total_entries = 0
        total_tasks = 0
        completed_tasks = 0

        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - datetime(year, month, 1)).days

        for day in range(1, days_in_month + 1):
            day_file = self.journal_dir / f"{year}-{month:02d}-{day:02d}.md"
            if day_file.exists():
                with open(day_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line[0] in '•○—=!*×><\\|':
                            total_entries += 1
                            if line[0] == '•':
                                total_tasks += 1
                            elif line[0] == '×':
                                completed_tasks += 1

        all_tasks = total_tasks + completed_tasks
        rate = (completed_tasks / all_tasks * 100) if all_tasks > 0 else 0

        self.total_entries_label.setText(f"Total: {total_entries}")
        self.tasks_label.setText(f"Tasks: {all_tasks}")
        self.completed_label.setText(f"Completed: {completed_tasks}")
        self.completion_rate_label.setText(f"Rate: {rate:.1f}%")

    def previous_month(self):
        if self.current_date.month == 1:
            self.current_date = datetime(self.current_date.year - 1, 12, 1)
        else:
            self.current_date = datetime(self.current_date.year, self.current_date.month - 1, 1)
        self.calendar.setCurrentPage(self.current_date.year, self.current_date.month)
        self.load_month()

    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = datetime(self.current_date.year + 1, 1, 1)
        else:
            self.current_date = datetime(self.current_date.year, self.current_date.month + 1, 1)
        self.calendar.setCurrentPage(self.current_date.year, self.current_date.month)
        self.load_month()

    def _parse_sections(self, content):
        lines = content.splitlines()
        has_headers = any(
            line.strip().startswith('## ') and line.strip()[3:] in self.SECTIONS
            for line in lines
        )
        sections = {s: [] for s in self.SECTIONS}
        if has_headers:
            current_section = 'Morning'
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('## ') and stripped[3:] in self.SECTIONS:
                    current_section = stripped[3:]
                    continue
                if stripped and stripped[0] in '•○—=!*×><\\|':
                    sections[current_section].append(stripped)
        else:
            for line in lines:
                stripped = line.strip()
                if stripped and stripped[0] in '•○—=!*×><\\|':
                    sections['Morning'].append(stripped)
        return sections

    def date_clicked(self, date):
        day_file = self.journal_dir / f"{date.toString('yyyy-MM-dd')}.md"

        if day_file.exists():
            with open(day_file, 'r', encoding='utf-8') as f:
                content = f.read()
            sections = self._parse_sections(content)
            display_lines = []
            for sec in self.SECTIONS:
                entries = sections.get(sec, [])
                if entries:
                    icon = {'Morning': '🌅', 'Afternoon': '☀️', 'Evening': '🌙'}[sec]
                    display_lines.append(f"{icon} {sec}")
                    display_lines.extend(f"  {e}" for e in entries)
                    display_lines.append('')
            self.preview.setPlainText('\n'.join(display_lines) if display_lines else "No entries for this day")
        else:
            self.preview.setPlainText("No entries for this day")

    def print_month(self):
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            dialog = QPrintDialog(printer, self)

            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                document = QTextDocument()
                document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())

                year = self.current_date.year
                month = self.current_date.month

                html = f"""<!DOCTYPE html>
<html><head><style>
body {{ font-family: sans-serif; margin: 20px; }}
h1 {{ font-size: 14pt; }}
h3 {{ font-size: 11pt; margin-top: 10px; }}
h4 {{ font-size: 9pt; color: #555; margin-top: 4px; margin-bottom: 2px; }}
hr {{ border: 1px solid #ccc; }}
pre {{ font-family: monospace; font-size: 9pt; white-space: pre-wrap; word-wrap: break-word; }}
</style></head><body>
<h1>{self.current_date.strftime('%B %Y')}</h1>
<p>{self.total_entries_label.text()} | {self.tasks_label.text()} | {self.completed_label.text()} | {self.completion_rate_label.text()}</p>
<hr>"""

                if month == 12:
                    next_month = datetime(year + 1, 1, 1)
                else:
                    next_month = datetime(year, month + 1, 1)
                days_in_month = (next_month - datetime(year, month, 1)).days

                for day in range(1, days_in_month + 1):
                    day_file = self.journal_dir / f"{year}-{month:02d}-{day:02d}.md"
                    if day_file.exists():
                        day_date = datetime(year, month, day)
                        html += f"<h3>{day_date.strftime('%A, %B %d')}</h3>"
                        with open(day_file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        sections = self._parse_sections(file_content)
                        for sec in self.SECTIONS:
                            entries = sections.get(sec, [])
                            if entries:
                                icon = {'Morning': '🌅', 'Afternoon': '☀️', 'Evening': '🌙'}[sec]
                                html += f"<h4>{icon} {sec}</h4>"
                                escaped = '\n'.join(entries).replace('<', '&lt;').replace('>', '&gt;')
                                html += f"<pre>{escaped}</pre>"

                html += "</body></html>"
                document.setHtml(html)
                document.print(printer)
        except Exception as e:
            QMessageBox.warning(self, "Print Error", f"Failed to print: {str(e)}")


class SettingsDialog(QDialog):
    """Settings dialog"""

    def __init__(self, current_dir, show_timestamps, parent=None):
        super().__init__(parent)
        self.current_dir = current_dir
        self.show_timestamps = show_timestamps

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 300)

        layout = QVBoxLayout(self)

        # Journal directory
        dir_group = QGroupBox("Journal Location")
        dir_layout = QHBoxLayout(dir_group)
        self.dir_input = QLineEdit(str(current_dir))
        dir_layout.addWidget(self.dir_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        layout.addWidget(dir_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        self.timestamp_checkbox = QCheckBox("Show timestamps on entries")
        self.timestamp_checkbox.setChecked(show_timestamps)
        options_layout.addWidget(self.timestamp_checkbox)
        layout.addWidget(options_group)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Journal Directory", str(self.current_dir)
        )
        if directory:
            self.dir_input.setText(directory)

    def get_settings(self):
        return Path(self.dir_input.text()), self.timestamp_checkbox.isChecked()


# ===========================================================================
# Entry point
# ===========================================================================

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Kbullet")
    app.setOrganizationName("Kbullet")

    journal = Kbullet()
    journal.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

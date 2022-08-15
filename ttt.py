from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QDialog, \
    QLineEdit, QTabWidget, QStyle

import misc
from p2p import TTT_Conn


class TileState:
    EMPTY = -1
    PLAYER1 = 0
    PLAYER2 = 1


class GameType:
    LOCAL = 1
    REMOTE = 1 << 1


class TicTacToe:
    def __init__(self):
        self._board = [[TileState.EMPTY for _ in range(3)] for _ in range(3)]
        self.turn = 1

    def set(self, x: int, y: int) -> (bool, int | None):
        """Sets the board state, returns True if successful, else False."""
        if self._board[y][x] == TileState.EMPTY:
            self._board[y][x] = (self.turn + 1) % 2
            self.turn += 1
            return True, self._board[y][x]
        return False, None

    def clear(self):
        self._board = [[TileState.EMPTY for _ in range(3)] for _ in range(3)]
        self.turn = 0

    def is_win(self) -> int:
        """Returns the TileState id of the player that won."""
        # Check straight
        for row in self._board:
            # check players 
            if sum(row) == TileState.PLAYER2 * 3:
                return TileState.PLAYER2
            elif sum(row) == 0 and len(set(row)) == 1:
                return TileState.PLAYER1
        # Check col
        for c in range(3):
            col_items = list(map(lambda arr: arr[c], self._board))
            if sum(col_items) == 3:
                return TileState.PLAYER2
            elif sum(col_items) == 0 and len(set(col_items)) == 1:
                return TileState.PLAYER1
        # Check diagonal
        diag1 = [self._board[0][0], self._board[1][1], self._board[2][2]]
        if sum(diag1) == 3:
            return TileState.PLAYER2
        elif sum(diag1) == 0 and len(set(diag1)) == 1:
            return TileState.PLAYER1
        diag2 = [self._board[0][2], self._board[1][1], self._board[2][0]]
        if sum(diag2) == 3:
            return TileState.PLAYER2
        elif sum(diag2) == 0 and len(set(diag2)) == 1:
            return TileState.PLAYER1
        # Default return
        return TileState.EMPTY

    @property
    def board(self):
        return self._board

    def show(self):
        print(f"+++++++++")
        for row in self._board:
            print(f"+ {self.get_symbol(row[0])} {self.get_symbol(row[1])} {self.get_symbol(row[2])} +")
        print(f"+++++++++")

    @classmethod
    def get_symbol(cls, _x: int) -> chr:
        return {TileState.PLAYER1: 'o', TileState.PLAYER2: 'x'}.get(_x, ' ')


class TTT_Gui(QWidget):
    def __init__(self, port=2222, parent=None):
        super(TTT_Gui, self).__init__(parent)
        self.setup(port)

    def setup(self, port: int):
        self.games = []
        self.total_games = 0
        self.conn = TTT_Conn(port)

        self.setMinimumSize(400, 400)
        self.setLayout(QVBoxLayout())

        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.on_tab_close)
        self.tabs.tabBarClicked.connect(self.on_tab_change)

        self.conn.new_connection.connect(self.accept_remote)

        self.new_page = TTT_New_Game(self, port=port)
        self.new_page.new_local_sig.connect(self.create_local)
        self.new_page.new_remote_sig.connect(self.create_remote)
        self.tabs.addTab(self.new_page, "New Game (+)")
        self.setWindowTitle("New Game (+)")
        # Remove close button from add tab
        default_side = self.tabs.style().styleHint(QStyle.SH_TabBar_CloseButtonPosition, None, self.tabs.tabBar())
        self.tabs.tabBar().setTabButton(0, default_side, None)

        self.layout().addWidget(self.tabs)

    def create_local(self):
        self.games.append(TTT_Game())
        self.total_games += 1
        self.tabs.insertTab(self.tabs.count() - 1, self.games[-1], f"Local Game {self.total_games}")
        self.tabs.setCurrentWidget(self.games[-1])
        self.setWindowTitle(f"Game {self.total_games}")

    def create_remote(self, host: str, port: int):
        print(f"{host = }\n{port = }")
        self.new_page.new_remote.setEnabled(False)
        self.new_page.new_remote.setText("Attempting to connect...")
        if self.conn.node.connect_with_node(host, port):
            self.games.append(TTT_Game(GameType.REMOTE, conn=self.conn))
            self.total_games += 1
            self.tabs.insertTab(self.tabs.count() - 1, self.games[-1], f"Remote Game {self.total_games}")
            self.tabs.setCurrentWidget(self.games[-1])
            self.setWindowTitle(f"Remote Game {self.total_games}")
            self.conn.greet()
        self.new_page.new_remote.setEnabled(True)
        self.new_page.new_remote.setText("New LAN Game")

    def accept_remote(self):
        self.games.append(TTT_Game(GameType.REMOTE, conn=self.conn))
        self.total_games += 1
        self.tabs.insertTab(self.tabs.count() - 1, self.games[-1], f"Remote Game {self.total_games}")
        self.tabs.setCurrentWidget(self.games[-1])
        self.setWindowTitle(f"Remote Game {self.total_games}")

    def on_tab_change(self, index: int):
        self.setWindowTitle(f"{self.tabs.tabText(index)}")

    def on_tab_close(self, index: int):
        self.tabs.removeTab(index)
        self.games.pop(index)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.conn.stop_conn()
        self.conn.wait()


class TTT_New_Game(QWidget):
    new_local_sig = pyqtSignal()
    new_remote_sig = pyqtSignal(str, int)

    def __init__(self, parent=None, port=2222):
        super(TTT_New_Game, self).__init__(parent)
        self.port = port
        self.setup()

    def setup(self):
        self.setLayout(QHBoxLayout())

        self.center = QVBoxLayout()
        self.new_local = QPushButton("New Local Game", parent=self)
        self.new_local.clicked.connect(self.create_new_local)
        self.new_remote = QPushButton("New LAN Game", parent=self)
        self.new_remote.clicked.connect(self.create_new_remote)
        self.center.addStretch()
        self.center.addWidget(self.new_local)
        self.center.addStretch()
        self.center.addWidget(self.new_remote)
        self.center.addStretch()

        self.layout().addStretch()
        self.layout().addLayout(self.center)
        self.layout().addStretch()

    def create_new_remote(self):
        dial = TTT_Connect_Dialogue(port=self.port)
        if dial.exec_():
            print(f"Host: {dial.host_edit.text()} Port: {dial.port_edit.text()}")
            self.new_remote_sig.emit(dial.host_edit.text(), int(dial.port_edit.text()))

    def create_new_local(self):
        self.new_local_sig.emit()


class TTT_Game(QWidget):
    def __init__(self, game_type=GameType.LOCAL, port=2222, conn=None):
        super(TTT_Game, self).__init__()
        self.setWindowTitle(f"Tic Tac Toe (Port: {port})")
        self.game_type = game_type
        self.conn: TTT_Conn | None = conn
        self.setup()

    def setup(self):
        # Backend
        self.iboard = TicTacToe()

        # Frontend
        self.setLayout(QVBoxLayout())

        # Board
        self.board_layout = QGridLayout()
        self.btns = [[TTT_Button(r, c, parent=self) for r in range(3)] for c in range(3)]
        for r, row in enumerate(self.btns):
            for c, btn in enumerate(row):
                btn.clicked.connect(self.on_btn_click)
                self.board_layout.addWidget(btn, r, c)

        self.layout().addLayout(self.board_layout)

        if self.game_type == GameType.REMOTE:
            # todo :: remote - decide who goes first
            self.conn.set_received.connect(self.on_set_recv)

    def on_btn_click(self):
        row = vars(self.sender()).get("row")
        col = vars(self.sender()).get("col")
        self.board_set(row, col)
        if self.game_type == GameType.REMOTE:
            self.conn.send_set(row, col)
            self.disable_board()
        self.check_win()

    def on_set_recv(self, row, col):
        """Behavior of the board upon receiving a SET message from a remote connection."""
        print(f"Received set @ ({row},{col})")
        self.board_set(int(row), int(col))
        self.enable_board()
        self.check_win()

    def board_set(self, row, col) -> bool:
        """Sets the state of the target button and disables the target button, returning a bool for success of
        operation. """
        success, sym = self.iboard.set(row, col)
        if success:
            self.btns[col][row].setEnabled(False)
            self.btns[col][row].tile = sym
            self.update()
        return success

    def check_win(self):
        """Checks for a win on the board. If there is one, then it will disable the board."""
        if self.iboard.is_win() != TileState.EMPTY:
            print(f"Player {self.iboard.is_win() + 1} won!")
            self.disable_board()
            # todo :: display a win animation of some sort

    def disable_board(self):
        """Disables all buttons."""
        for row in self.btns:
            for btn in row:
                btn.setDisabled(True)

    def enable_board(self):
        """Enables all buttons that are in the EMPTY TileState."""
        for row in self.btns:
            for btn in row:
                btn.setEnabled(True) if btn.tile == TileState.EMPTY else 0


class TTT_Button(QPushButton):
    def __init__(self, row: int, col: int, parent=None):
        super(TTT_Button, self).__init__(parent)
        self.row = row
        self.col = col
        self.size_policy()
        self.tile = TileState.EMPTY

    def size_policy(self):
        p = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        p.setHeightForWidth(True)
        self.setSizePolicy(p)

    def heightForWidth(self, width: int) -> int:
        return width

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(150, 150)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        print(self.size())

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen()
        pen.setWidth(10)
        if self.tile == TileState.PLAYER2:
            pen.setColor(QColor(255, 0, 0))
            painter.setPen(pen)
            painter.drawEllipse(self.rect().center(), int(self.rect().width() / 2 * 0.8),
                                int(self.rect().height() / 2 * 0.8))
        elif self.tile == TileState.PLAYER1:
            pen.setColor(QColor(0, 0, 255))
            painter.setPen(pen)
            painter.drawLine(int(self.rect().width() * 0.2), int(self.rect().height() * 0.2),
                             int(self.rect().width() * 0.8), int(self.rect().height() * 0.8))
            painter.drawLine(int(self.rect().width() * 0.8), int(self.rect().height() * 0.2),
                             int(self.rect().width() * 0.2), int(self.rect().height() * 0.8))


class TTT_Connect_Dialogue(QDialog):
    def __init__(self, parent=None, port=2222):
        super(TTT_Connect_Dialogue, self).__init__(parent)
        self.setLayout(QVBoxLayout())
        self.port = port
        self.setup()

    def setup(self):
        self.setModal(True)
        self.setWindowFlag(Qt.FramelessWindowHint)

        self.my_info = QLabel(f"My Info: {misc.get_ip()}:{self.port}")
        self.layout().addWidget(self.my_info)
        self.accept_btn = QPushButton("Connect", parent=self)
        self.accept_btn.clicked.connect(self.on_accept_click)
        self.reject_btn = QPushButton("Cancel", parent=self)
        self.reject_btn.clicked.connect(self.on_reject_click)
        self.options_layout = QHBoxLayout()
        self.options_layout.addWidget(self.reject_btn)
        self.options_layout.addWidget(self.accept_btn)

        self.all_in_layout = QHBoxLayout()
        self.label_col = QVBoxLayout()
        self.input_col = QVBoxLayout()
        self.host_label = QLabel("Host", parent=self)
        self.host_edit = QLineEdit("127.0.0.1", parent=self)
        self.label_col.addWidget(self.host_label)
        self.input_col.addWidget(self.host_edit)
        self.port_label = QLabel("Port", parent=self)
        self.port_edit = QLineEdit("1234", parent=self)
        self.label_col.addWidget(self.port_label)
        self.input_col.addWidget(self.port_edit)
        self.all_in_layout.addLayout(self.label_col)
        self.all_in_layout.addLayout(self.input_col)

        self.layout().addLayout(self.all_in_layout)
        self.layout().addLayout(self.options_layout)

    def on_accept_click(self):
        self.accept()

    def on_reject_click(self):
        self.reject()

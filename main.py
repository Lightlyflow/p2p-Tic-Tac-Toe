from PyQt5.QtWidgets import QApplication
import sys

from ttt import TTT_Gui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = TTT_Gui(int(sys.argv[1]) if len(sys.argv) == 2 else 2222)
    widget.show()
    sys.exit(app.exec_())

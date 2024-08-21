from qtpy import QtCore
from qtpy import QtWidgets


class YAxisWidget(QtWidgets.QWidget):
    def __init__(self, units, parent=None):
        super().__init__(parent)
        top_label = QtWidgets.QLabel("1")
        top_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.top_label = top_label

        bottom_label = QtWidgets.QLabel("0")
        bottom_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.bottom_label = bottom_label

        units_label = QtWidgets.QLabel(units)
        units_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.units_label = units_label

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(top_label)
        layout.setStretch(0, 1)
        layout.addWidget(units_label)
        layout.setStretch(1, 10)
        layout.addWidget(bottom_label)
        layout.setStretch(2, 1)
        layout.setSpacing(1)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.setFixedWidth(70)
        # self.setStyleSheet("background-color: black; color: white; 1px solid white;")


def create_ylabels(chs: list):
    i = 0
    layout = QtWidgets.QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    for ch_num, val in enumerate(chs):
        if val is True:
            ch_label = QtWidgets.QLabel(f"Channel {ch_num}")
            ch_label.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Preferred,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
            layout.addWidget(ch_label)
            layout.setStretch(i, 11)
            i += 1
    return layout


def create_yaxes(chs, units):
    i = 0
    layout = QtWidgets.QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    for _ch_num, val in enumerate(chs):
        if val is True:
            y_axis = YAxisWidget(units)
            layout.addWidget(y_axis)
            layout.setStretch(i, 10)
            i += 1
    return layout

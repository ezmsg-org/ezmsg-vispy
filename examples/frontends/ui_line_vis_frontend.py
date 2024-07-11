################################################################################
## Form generated from reading UI file 'line_vis_frontend.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QMetaObject
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QDial
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget


class Ui_AppWindow:
    def setupUi(self, AppWindow):
        if not AppWindow.objectName():
            AppWindow.setObjectName("AppWindow")
        AppWindow.resize(400, 300)
        sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AppWindow.sizePolicy().hasHeightForWidth())
        AppWindow.setSizePolicy(sizePolicy)
        self.cantral = QWidget(AppWindow)
        self.cantral.setObjectName("cantral")
        sizePolicy.setHeightForWidth(self.cantral.sizePolicy().hasHeightForWidth())
        self.cantral.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.cantral)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(10, 10, 10, 10)
        self.verticalSpacer_2 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.frequency_dial_label = QLabel(self.cantral)
        self.frequency_dial_label.setObjectName("frequency_dial_label")
        self.frequency_dial_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.frequency_dial_label)

        self.ez_frequency_dial = QDial(self.cantral)
        self.ez_frequency_dial.setObjectName("ez_frequency_dial")
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.ez_frequency_dial.sizePolicy().hasHeightForWidth()
        )
        self.ez_frequency_dial.setSizePolicy(sizePolicy1)
        self.ez_frequency_dial.setMaximumSize(QSize(16777215, 50))
        self.ez_frequency_dial.setBaseSize(QSize(0, 0))
        self.ez_frequency_dial.setValue(0)

        self.verticalLayout_2.addWidget(self.ez_frequency_dial)

        self.waveform_type_label = QLabel(self.cantral)
        self.waveform_type_label.setObjectName("waveform_type_label")
        self.waveform_type_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.waveform_type_label)

        self.ez_waveform_type = QComboBox(self.cantral)
        self.ez_waveform_type.setObjectName("ez_waveform_type")

        self.verticalLayout_2.addWidget(self.ez_waveform_type)

        self.verticalSpacer_3 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.verticalLayout_2.addItem(self.verticalSpacer_3)

        self.ez_start_btn = QPushButton(self.cantral)
        self.ez_start_btn.setObjectName("ez_start_btn")
        sizePolicy1.setHeightForWidth(
            self.ez_start_btn.sizePolicy().hasHeightForWidth()
        )
        self.ez_start_btn.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.ez_start_btn)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.ez_ts_plot = QWidget(self.cantral)
        self.ez_ts_plot.setObjectName("ez_ts_plot")
        sizePolicy.setHeightForWidth(self.ez_ts_plot.sizePolicy().hasHeightForWidth())
        self.ez_ts_plot.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.ez_ts_plot)

        self.ez_fs_plot = QWidget(self.cantral)
        self.ez_fs_plot.setObjectName("ez_fs_plot")
        sizePolicy.setHeightForWidth(self.ez_fs_plot.sizePolicy().hasHeightForWidth())
        self.ez_fs_plot.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.ez_fs_plot)

        self.horizontalLayout.addLayout(self.verticalLayout)

        AppWindow.setCentralWidget(self.cantral)

        self.retranslateUi(AppWindow)

        QMetaObject.connectSlotsByName(AppWindow)

    # setupUi

    def retranslateUi(self, AppWindow):
        AppWindow.setWindowTitle(
            QCoreApplication.translate("AppWindow", "Application Example", None)
        )
        self.frequency_dial_label.setText(
            QCoreApplication.translate("AppWindow", "Frequency Select", None)
        )
        self.waveform_type_label.setText(
            QCoreApplication.translate("AppWindow", "Waveform Type", None)
        )
        self.ez_start_btn.setText(
            QCoreApplication.translate("AppWindow", "Start", None)
        )

    # retranslateUi

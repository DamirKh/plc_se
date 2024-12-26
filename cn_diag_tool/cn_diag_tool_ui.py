# Form implementation generated from reading ui file 'ui/cn_diag_tool.main.ui'
#
# Created by: PyQt6 UI code generator 6.7.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(817, 716)
        MainWindow.setMinimumSize(QtCore.QSize(665, 338))
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEditConnectionPath = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.lineEditConnectionPath.setObjectName("lineEditConnectionPath")
        self.horizontalLayout.addWidget(self.lineEditConnectionPath)
        self.pushButtonConnect = QtWidgets.QPushButton(parent=self.centralwidget)
        self.pushButtonConnect.setEnabled(True)
        self.pushButtonConnect.setObjectName("pushButtonConnect")
        self.horizontalLayout.addWidget(self.pushButtonConnect)
        self.labelProjectName = QtWidgets.QLabel(parent=self.centralwidget)
        self.labelProjectName.setObjectName("labelProjectName")
        self.horizontalLayout.addWidget(self.labelProjectName)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.progressBar = QtWidgets.QProgressBar(parent=self.centralwidget)
        self.progressBar.setProperty("value", 17)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout_2.addWidget(self.progressBar)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.tableWidget = QtWidgets.QTableWidget(parent=self.centralwidget)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout_3.addWidget(self.tableWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 817, 19))
        self.menubar.setObjectName("menubar")
        self.menuConfig = QtWidgets.QMenu(parent=self.menubar)
        self.menuConfig.setObjectName("menuConfig")
        self.menuConfig_2 = QtWidgets.QMenu(parent=self.menubar)
        self.menuConfig_2.setObjectName("menuConfig_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionLoad = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("document-open")
        self.actionLoad.setIcon(icon)
        self.actionLoad.setObjectName("actionLoad")
        self.actionSave = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("document-save")
        self.actionSave.setIcon(icon)
        self.actionSave.setObjectName("actionSave")
        self.actionRead_Timer = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("media-playlist-repeat")
        self.actionRead_Timer.setIcon(icon)
        self.actionRead_Timer.setObjectName("actionRead_Timer")
        self.actionEnable_writing_to_PLC = QtGui.QAction(parent=MainWindow)
        self.actionEnable_writing_to_PLC.setCheckable(True)
        icon = QtGui.QIcon.fromTheme("emblem-downloads")
        self.actionEnable_writing_to_PLC.setIcon(icon)
        self.actionEnable_writing_to_PLC.setObjectName("actionEnable_writing_to_PLC")
        self.actionOpen_config_folder = QtGui.QAction(parent=MainWindow)
        self.actionOpen_config_folder.setObjectName("actionOpen_config_folder")
        self.actionShow_log = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("utilities-system-monitor")
        self.actionShow_log.setIcon(icon)
        self.actionShow_log.setObjectName("actionShow_log")
        self.menuConfig.addAction(self.actionLoad)
        self.menuConfig.addAction(self.actionSave)
        self.menuConfig.addAction(self.actionOpen_config_folder)
        self.menuConfig.addAction(self.actionShow_log)
        self.menuConfig_2.addAction(self.actionRead_Timer)
        self.menuConfig_2.addAction(self.actionEnable_writing_to_PLC)
        self.menubar.addAction(self.menuConfig.menuAction())
        self.menubar.addAction(self.menuConfig_2.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ControlNet diagnostic tool"))
        self.label.setText(_translate("MainWindow", "PLC connection path:"))
        self.pushButtonConnect.setText(_translate("MainWindow", "Scan"))
        self.labelProjectName.setText(_translate("MainWindow", "Not connected"))
        self.label_2.setText(_translate("MainWindow", "Duty:"))
        self.menuConfig.setTitle(_translate("MainWindow", "File"))
        self.menuConfig_2.setTitle(_translate("MainWindow", "Config"))
        self.actionLoad.setText(_translate("MainWindow", "Load"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionRead_Timer.setText(_translate("MainWindow", "Read Timer"))
        self.actionEnable_writing_to_PLC.setText(_translate("MainWindow", "Enable writing to PLC"))
        self.actionOpen_config_folder.setText(_translate("MainWindow", "Open config folder"))
        self.actionShow_log.setText(_translate("MainWindow", "Show log"))

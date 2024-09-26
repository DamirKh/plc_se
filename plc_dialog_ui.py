# Form implementation generated from reading ui file 'ui/add_plc.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(580, 227)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton_2 = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 3, 3, 1, 1)
        self.lineEditSurname = QtWidgets.QLineEdit(parent=Dialog)
        self.lineEditSurname.setObjectName("lineEditSurname")
        self.gridLayout.addWidget(self.lineEditSurname, 0, 2, 1, 1)
        self.lineEditL5X = QtWidgets.QLineEdit(parent=Dialog)
        self.lineEditL5X.setObjectName("lineEditL5X")
        self.gridLayout.addWidget(self.lineEditL5X, 1, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 1, 3, 1, 1)
        self.label = QtWidgets.QLabel(parent=Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(parent=Dialog)
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 2, 2, 1, 1)
        self.lineEditConnectionPath = QtWidgets.QLineEdit(parent=Dialog)
        self.lineEditConnectionPath.setObjectName("lineEditConnectionPath")
        self.gridLayout.addWidget(self.lineEditConnectionPath, 3, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.pushButtonLoadPLCtags = QtWidgets.QPushButton(parent=Dialog)
        self.pushButtonLoadPLCtags.setObjectName("pushButtonLoadPLCtags")
        self.gridLayout.addWidget(self.pushButtonLoadPLCtags, 3, 4, 1, 1)
        self.pushButtonLoadProgram = QtWidgets.QPushButton(parent=Dialog)
        self.pushButtonLoadProgram.setEnabled(False)
        self.pushButtonLoadProgram.setObjectName("pushButtonLoadProgram")
        self.gridLayout.addWidget(self.pushButtonLoadProgram, 1, 4, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.ok_press) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        self.pushButton_2.clicked.connect(Dialog.CheckConnection) # type: ignore
        self.pushButton.clicked.connect(Dialog.selectL5X) # type: ignore
        self.pushButtonLoadProgram.clicked.connect(Dialog.LoadProgram) # type: ignore
        self.pushButtonLoadPLCtags.clicked.connect(Dialog.LoadPLCtags) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Add PLC"))
        self.pushButton_2.setText(_translate("Dialog", "Check"))
        self.label_2.setText(_translate("Dialog", "Connection path"))
        self.pushButton.setText(_translate("Dialog", "Select"))
        self.label.setText(_translate("Dialog", "L5X File"))
        self.checkBox.setText(_translate("Dialog", "Copy File to project directory"))
        self.label_3.setText(_translate("Dialog", "PLC surname"))
        self.pushButtonLoadPLCtags.setText(_translate("Dialog", "Load PLC tags"))
        self.pushButtonLoadProgram.setText(_translate("Dialog", "Load programm"))
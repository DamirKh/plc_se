# Form implementation generated from reading ui file 'ui/FormTab2.ui'
#
# Created by: PyQt6 UI code generator 6.7.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_FormTabWidget(object):
    def setupUi(self, FormTabWidget):
        FormTabWidget.setObjectName("FormTabWidget")
        FormTabWidget.resize(594, 361)
        self.verticalLayout = QtWidgets.QVBoxLayout(FormTabWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.tableView = QtWidgets.QTableView(parent=FormTabWidget)
        self.tableView.setObjectName("tableView")
        self.gridLayout.addWidget(self.tableView, 0, 0, 1, 1)
        self.pushButtonPlusColumn = QtWidgets.QPushButton(parent=FormTabWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.pushButtonPlusColumn.sizePolicy().hasHeightForWidth())
        self.pushButtonPlusColumn.setSizePolicy(sizePolicy)
        self.pushButtonPlusColumn.setText("")
        icon = QtGui.QIcon.fromTheme("list-add")
        self.pushButtonPlusColumn.setIcon(icon)
        self.pushButtonPlusColumn.setObjectName("pushButtonPlusColumn")
        self.gridLayout.addWidget(self.pushButtonPlusColumn, 0, 1, 1, 1)
        self.pushButtonPlusRow = QtWidgets.QPushButton(parent=FormTabWidget)
        self.pushButtonPlusRow.setObjectName("pushButtonPlusRow")
        self.gridLayout.addWidget(self.pushButtonPlusRow, 1, 0, 1, 1)
        self.checkBoxRead = QtWidgets.QCheckBox(parent=FormTabWidget)
        self.checkBoxRead.setObjectName("checkBoxRead")
        self.gridLayout.addWidget(self.checkBoxRead, 2, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(FormTabWidget)
        QtCore.QMetaObject.connectSlotsByName(FormTabWidget)

    def retranslateUi(self, FormTabWidget):
        _translate = QtCore.QCoreApplication.translate
        FormTabWidget.setWindowTitle(_translate("FormTabWidget", "Form"))
        self.pushButtonPlusRow.setText(_translate("FormTabWidget", "Add row"))
        self.checkBoxRead.setText(_translate("FormTabWidget", "Read Periodicaly"))

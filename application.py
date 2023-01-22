from PyQt5 import QtCore, QtGui, QtWidgets
from string import ascii_lowercase, ascii_uppercase, digits, ascii_letters
import sqlite3
import sys

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

db = sqlite3.connect('identifier.sqlite')
cations = ['NH4', 'K', 'Na', 'Ag', 'Ba', 'Ca', 'Co', 'Li', 'Mg', 'Mn', 'Zn', 'Ni', 'Sn', 'Pb', 'Cu', 'Hg', 'Fe2', 'Al', 'Cr', 'H', 'Fe3']
anions = ['OH', 'NO2', 'NO3', 'Cl', 'Br', 'I', 'SO3', 'SO4', 'CO3', 'SiO3', 'PO4', 'CH3COO', 'F', 'S', 'Si', 'N', 'P', 'C', 'O']


def no_index_element(sub):
    for i in sub:
        if i not in ascii_letters:
            sub.replace(i, '')
    return sub


def digit_list(iterator):
    dlist = list()
    for i in iterator:
        try:
            dlist.append(int(i))
        except Exception:
            pass
    return dlist


def define_elements(sub):
    elems = dict()
    elem = ''
    for i in sub:
        if i in ascii_uppercase and len(elem) == 0:
            elem = elem + i
        elif i in ascii_uppercase:
            elems[elem] = 1
            elem = i
        elif i in ascii_lowercase:
            elem = elem + i
        elif i in digits:
            elems[elem] = int(i)
            elem = ''
    if elem:
        elems[elem] = 1
    return elems


def define_cation(sub):
    for i in cations:
        if i in sub:
            return i


def define_anion(sub):
    if sub in anions:
        return sub
    else:
        for i in anions:
            if i in sub[1:]:
                return i


def define_anion_corrosion(sub):
    return list(db.execute(f"""SELECT * FROM AnionsCorrosion WHERE ELEM = '{define_anion(sub)}'"""))[0][1]


def define_flexible_corrosion(sub, corr1, corr2):
    index, i = 1, 1
    for i in digit_list(list(sub)):
        if i in digit_list(list(digits)):
            index *= int(i)
    if index // (index // int(i)) == corr1:
        return corr1
    if index // (index // int(i)) == corr2:
        return corr2
    else:
        return abs(define_anion_corrosion(sub))


def define_cation_corrosion(sub):
    if define_cation(sub) == 'Fe':
        return define_flexible_corrosion(sub, 2, 3)
    if define_cation(sub) == 'Cu':
        return define_flexible_corrosion(sub, 1, 2)
    if define_cation(sub) == 'Hg':
        return define_flexible_corrosion(sub, 1, 2)
    else:
        return list(db.execute(f"""SELECT * FROM CationsCorrosion WHERE ELEM = '{define_cation(sub)}'"""))[0][1]


def substance(cation, anion):
    index = define_cation_corrosion(cation) * abs(define_anion_corrosion(anion))
    index1 = abs(define_anion_corrosion(anion)) if index != define_cation_corrosion(cation) else ''
    index2 = define_cation_corrosion(cation) if index != abs(define_anion_corrosion(anion)) else ''
    anion = f'({anion})' if index2 and (len(anion) > 1 or anion[-1] in ascii_lowercase) else f'{anion}'
    return f'{cation}{index1}{anion}{index2}'


def define_substance(sub):
    if sub[0] == 'H':
        return 'Acid'
    elif define_anion(sub) == 'OH':
        return 'Base'
    elif define_anion(sub) == 'O':
        return 'Oxide'
    else:
        return 'Salt'


def define_solubility(sub):
    return list(db.execute(f"""SELECT * FROM Solubility WHERE ANION = '{define_anion(sub)}' AND CATION = '{define_cation(sub)}'"""))[0][2]


def molar_mass(sub):
    M = 0
    elem = define_elements(sub)
    for i in elem.keys():
        m = list(db.execute(f"""SELECT * FROM PerTable WHERE ELEM = '{i}'"""))[0][1]
        if m is not None:
            M += m * int(elem[i])
        else:
            return 0
    return M


def electron(elec):
    if 's' in elec:
        return 's'
    elif 'p' in elec:
        return 'p'
    elif 'd' in elec:
        return 'd'
    elif 'f' in elec:
        return 'f'


def electron_config(element):
    try:
        return db.execute(f'SELECT * FROM SpecialConfig WHERE ELEM = {element}')
    except Exception:
        config = ''
        order = ['1s', '2s', '2p', '3s', '3p', '4s', '3d', '4p', '5s', '4d', '5p', '6s', '4f', '5d', '6p', '7s', '5f',
                 '6d', '7p']
        max_elec = {'s': 2, 'p': 6, 'd': 10, 'f': 14}
        num = int(db.execute(f"""SELECT * FROM Numbers WHERE ELEM = '{element}'""").fetchall()[0][1])
        while True:
            typ = electron(order[0])
            if num >= max_elec[typ]:
                config = config + f'{order[0]}[{max_elec[typ]}]'
                order = order[1:]
                num -= max_elec[typ]
            elif num > 0:
                config = config + f'{order[0]}[{num}]'
                return config
            else:
                return config
            if not order:
                return config


def chemical_change_reaction(chem1, chem2):
    return f'{substance(define_cation(chem1), define_anion(chem2))} + {substance(define_cation(chem2), define_anion(chem1))}'


class Ui_Dialog(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi2()

    def setupUi2(self):
        self.setObjectName("Dialog")
        self.resize(400, 172)
        self.setStyleSheet("background-color: rgb(60, 60, 60);")
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setGeometry(QtCore.QRect(20, 20, 361, 51))
        self.lineEdit.setStyleSheet("color: rgb(255, 0, 255);\n"
                                    "background-color: rgb(0, 0, 0);\n"
                                    "border:2px solid rgb(255, 0, 255);\n"
                                    "border-color: rgb(255, 0, 255);")
        self.lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit.setObjectName("lineEdit")
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setGeometry(QtCore.QRect(20, 70, 361, 31))
        self.pushButton.setStyleSheet("color: rgb(0, 0, 255);\n"
                                      "background-color: rgb(0, 0, 0);\n"
                                      "border: 2px solid  rgb(0, 0, 255);")
        self.pushButton.setObjectName("pushButton")
        self.lineEdit_2 = QtWidgets.QLineEdit(self)
        self.lineEdit_2.setGeometry(QtCore.QRect(20, 100, 361, 51))
        self.lineEdit_2.setStyleSheet("color: rgb(255, 0, 0);\n"
                                      "background-color: rgb(0, 0, 0);\n"
                                      "border:2px solid rgb(255, 0, 0);\n"
                                      "border-color: rgb(255, 0, 0);")
        self.lineEdit_2.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.setWindowTitle("Database changer")
        self.pushButton.setText("EXECUTE")
        QtCore.QMetaObject.connectSlotsByName(self)

    def EXECUTE_EV(self):
        command = self.lineEdit.text()
        try:
            db.execute(command)
            self.lineEdit_2.setText('SUCCESS')
        except Exception as ex:
            self.lineEdit_2.setText('ERROR ' + str(ex))


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1126, 500)
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        MainWindow.setFont(font)
        MainWindow.setStyleSheet("background-color: rgb(60, 60, 60);")
        self.label = QtWidgets.QLabel(MainWindow)
        self.label.setGeometry(QtCore.QRect(10, 10, 131, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label.setFont(font)
        self.label.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                 "color: rgb(0, 255, 255);\n"
                                 "border: 2px solid rgb(0, 255, 255);")
        self.label.setScaledContents(False)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.Calc_in = QtWidgets.QLineEdit(MainWindow)
        self.Calc_in.setGeometry(QtCore.QRect(80, 50, 131, 31))
        self.Calc_in.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                   "color: rgb(0, 255, 255);")
        self.Calc_in.setObjectName("Calc_in")
        self.CALC_ACT = QtWidgets.QPushButton(MainWindow)
        self.CALC_ACT.setGeometry(QtCore.QRect(220, 50, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.CALC_ACT.setFont(font)
        self.CALC_ACT.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                    "border-radius: 0px rgb(0, 255, 255);\n"
                                    "background-color: rgb(0, 0, 0);\n"
                                    "color: rgb(0, 255, 255);")
        self.CALC_ACT.setObjectName("CALC_ACT")
        self.Calc_out = QtWidgets.QLineEdit(MainWindow)
        self.Calc_out.setGeometry(QtCore.QRect(310, 50, 131, 31))
        self.Calc_out.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                    "color: rgb(0, 255, 255);")
        self.Calc_out.setObjectName("Calc_out")
        self.label_2 = QtWidgets.QLabel(MainWindow)
        self.label_2.setGeometry(QtCore.QRect(80, 250, 131, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);\n"
                                   "border: 2px solid rgb(0, 255, 255);")
        self.label_2.setScaledContents(False)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.SUB_Mmass_in = QtWidgets.QLineEdit(MainWindow)
        self.SUB_Mmass_in.setGeometry(QtCore.QRect(220, 250, 131, 31))
        self.SUB_Mmass_in.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                        "color: rgb(0, 255, 255);")
        self.SUB_Mmass_in.setObjectName("SUB_Mmass_in")
        self.SUB_MMASS_ACT = QtWidgets.QPushButton(MainWindow)
        self.SUB_MMASS_ACT.setGeometry(QtCore.QRect(360, 250, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.SUB_MMASS_ACT.setFont(font)
        self.SUB_MMASS_ACT.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                         "border-radius: 0px rgb(0, 255, 255);\n"
                                         "background-color: rgb(0, 0, 0);\n"
                                         "color: rgb(0, 255, 255);")
        self.SUB_MMASS_ACT.setObjectName("SUB_MMASS_ACT")
        self.SUB_Mmass_out = QtWidgets.QLineEdit(MainWindow)
        self.SUB_Mmass_out.setGeometry(QtCore.QRect(450, 250, 131, 31))
        self.SUB_Mmass_out.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                         "color: rgb(0, 255, 255);")
        self.SUB_Mmass_out.setObjectName("SUB_Mmass_out")
        self.label_3 = QtWidgets.QLabel(MainWindow)
        self.label_3.setGeometry(QtCore.QRect(80, 290, 191, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_3.setFont(font)
        self.label_3.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);\n"
                                   "border: 2px solid rgb(0, 255, 255);")
        self.label_3.setScaledContents(False)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.SUB_ELCONF_ACT = QtWidgets.QPushButton(MainWindow)
        self.SUB_ELCONF_ACT.setGeometry(QtCore.QRect(420, 290, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.SUB_ELCONF_ACT.setFont(font)
        self.SUB_ELCONF_ACT.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                          "border-radius: 0px rgb(0, 255, 255);\n"
                                          "background-color: rgb(0, 0, 0);\n"
                                          "color: rgb(0, 255, 255);")
        self.SUB_ELCONF_ACT.setObjectName("SUB_ELCONF_ACT")
        self.SUB_elConf_in = QtWidgets.QLineEdit(MainWindow)
        self.SUB_elConf_in.setGeometry(QtCore.QRect(280, 290, 131, 31))
        self.SUB_elConf_in.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                         "color: rgb(0, 255, 255);")
        self.SUB_elConf_in.setObjectName("SUB_elConf_in")
        self.SUB_elConf_out = QtWidgets.QLineEdit(MainWindow)
        self.SUB_elConf_out.setGeometry(QtCore.QRect(510, 290, 231, 31))
        self.SUB_elConf_out.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                          "color: rgb(0, 255, 255);")
        self.SUB_elConf_out.setObjectName("SUB_elConf_out")
        self.label_4 = QtWidgets.QLabel(MainWindow)
        self.label_4.setGeometry(QtCore.QRect(10, 90, 191, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_4.setFont(font)
        self.label_4.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);\n"
                                   "border: 2px solid rgb(0, 255, 255);")
        self.label_4.setScaledContents(False)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(MainWindow)
        self.label_5.setGeometry(QtCore.QRect(80, 130, 191, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_5.setFont(font)
        self.label_5.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);\n"
                                   "border: 2px solid rgb(0, 255, 255);")
        self.label_5.setScaledContents(False)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.SUB_cation = QtWidgets.QLineEdit(MainWindow)
        self.SUB_cation.setGeometry(QtCore.QRect(280, 130, 81, 31))
        self.SUB_cation.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                      "color: rgb(0, 255, 255);")
        self.SUB_cation.setObjectName("SUB_cation")
        self.SUB_anion = QtWidgets.QLineEdit(MainWindow)
        self.SUB_anion.setGeometry(QtCore.QRect(400, 130, 81, 31))
        self.SUB_anion.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                     "color: rgb(0, 255, 255);")
        self.SUB_anion.setObjectName("SUB_anion")
        self.label_6 = QtWidgets.QLabel(MainWindow)
        self.label_6.setGeometry(QtCore.QRect(360, 130, 41, 31))
        self.label_6.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                   "border-radius: 0px rgb(0, 255, 255);\n"
                                   "background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);")
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.SUB_MAKE_ACT = QtWidgets.QPushButton(MainWindow)
        self.SUB_MAKE_ACT.setGeometry(QtCore.QRect(490, 130, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.SUB_MAKE_ACT.setFont(font)
        self.SUB_MAKE_ACT.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                        "border-radius: 0px rgb(0, 255, 255);\n"
                                        "background-color: rgb(0, 0, 0);\n"
                                        "color: rgb(0, 255, 255);")
        self.SUB_MAKE_ACT.setObjectName("SUB_MAKE_ACT")
        self.SUB_sub = QtWidgets.QLineEdit(MainWindow)
        self.SUB_sub.setGeometry(QtCore.QRect(580, 130, 121, 31))
        self.SUB_sub.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                   "color: rgb(0, 255, 255);")
        self.SUB_sub.setObjectName("SUB_sub")
        self.label_7 = QtWidgets.QLabel(MainWindow)
        self.label_7.setGeometry(QtCore.QRect(80, 170, 191, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_7.setFont(font)
        self.label_7.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);\n"
                                   "border: 2px solid rgb(0, 255, 255);")
        self.label_7.setScaledContents(False)
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName("label_7")
        self.SUB_SolSub_in = QtWidgets.QLineEdit(MainWindow)
        self.SUB_SolSub_in.setGeometry(QtCore.QRect(280, 170, 121, 31))
        self.SUB_SolSub_in.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                         "color: rgb(0, 255, 255);")
        self.SUB_SolSub_in.setObjectName("SUB_SolSub_in")
        self.SUB_SOL_ACT = QtWidgets.QPushButton(MainWindow)
        self.SUB_SOL_ACT.setGeometry(QtCore.QRect(410, 170, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.SUB_SOL_ACT.setFont(font)
        self.SUB_SOL_ACT.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                       "border-radius: 0px rgb(0, 255, 255);\n"
                                       "background-color: rgb(0, 0, 0);\n"
                                       "color: rgb(0, 255, 255);")
        self.SUB_SOL_ACT.setObjectName("SUB_SOL_ACT")
        self.SUB_SolSub_out = QtWidgets.QLineEdit(MainWindow)
        self.SUB_SolSub_out.setGeometry(QtCore.QRect(500, 170, 121, 31))
        self.SUB_SolSub_out.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                          "color: rgb(0, 255, 255);")
        self.SUB_SolSub_out.setObjectName("SUB_SolSub_out")
        self.label_8 = QtWidgets.QLabel(MainWindow)
        self.label_8.setGeometry(QtCore.QRect(80, 210, 221, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_8.setFont(font)
        self.label_8.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);\n"
                                   "border: 2px solid rgb(0, 255, 255);")
        self.label_8.setScaledContents(False)
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName("label_8")
        self.SUB_corr_in = QtWidgets.QLineEdit(MainWindow)
        self.SUB_corr_in.setGeometry(QtCore.QRect(310, 210, 121, 31))
        self.SUB_corr_in.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                       "color: rgb(0, 255, 255);")
        self.SUB_corr_in.setObjectName("SUB_corr_in")
        self.SUB_CORR_ACT = QtWidgets.QPushButton(MainWindow)
        self.SUB_CORR_ACT.setGeometry(QtCore.QRect(440, 210, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.SUB_CORR_ACT.setFont(font)
        self.SUB_CORR_ACT.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                        "border-radius: 0px rgb(0, 255, 255);\n"
                                        "background-color: rgb(0, 0, 0);\n"
                                        "color: rgb(0, 255, 255);")
        self.SUB_CORR_ACT.setObjectName("SUB_CORR_ACT")
        self.SUB_corrCat_out = QtWidgets.QLineEdit(MainWindow)
        self.SUB_corrCat_out.setGeometry(QtCore.QRect(600, 210, 31, 31))
        self.SUB_corrCat_out.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                           "color: rgb(0, 255, 255);")
        self.SUB_corrCat_out.setObjectName("SUB_corrCat_out")
        self.label_9 = QtWidgets.QLabel(MainWindow)
        self.label_9.setGeometry(QtCore.QRect(530, 210, 71, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_9.setFont(font)
        self.label_9.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                   "color: rgb(0, 255, 255);\n"
                                   "border: 2px solid rgb(0, 255, 255);")
        self.label_9.setScaledContents(False)
        self.label_9.setAlignment(QtCore.Qt.AlignCenter)
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(MainWindow)
        self.label_10.setGeometry(QtCore.QRect(640, 210, 71, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_10.setFont(font)
        self.label_10.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                    "color: rgb(0, 255, 255);\n"
                                    "border: 2px solid rgb(0, 255, 255);")
        self.label_10.setScaledContents(False)
        self.label_10.setAlignment(QtCore.Qt.AlignCenter)
        self.label_10.setObjectName("label_10")
        self.SUB_corrAn_out = QtWidgets.QLineEdit(MainWindow)
        self.SUB_corrAn_out.setGeometry(QtCore.QRect(710, 210, 31, 31))
        self.SUB_corrAn_out.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                          "color: rgb(0, 255, 255);")
        self.SUB_corrAn_out.setObjectName("SUB_corrAn_out")
        self.label_11 = QtWidgets.QLabel(MainWindow)
        self.label_11.setGeometry(QtCore.QRect(10, 330, 191, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_11.setFont(font)
        self.label_11.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                    "color: rgb(0, 255, 255);\n"
                                    "border: 2px solid rgb(0, 255, 255);")
        self.label_11.setScaledContents(False)
        self.label_11.setAlignment(QtCore.Qt.AlignCenter)
        self.label_11.setObjectName("label_11")
        self.REAC_in = QtWidgets.QLineEdit(MainWindow)
        self.REAC_in.setGeometry(QtCore.QRect(80, 370, 211, 31))
        self.REAC_in.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                   "color: rgb(0, 255, 255);")
        self.REAC_in.setObjectName("REAC_in")
        self.SUB_REAC_ACT = QtWidgets.QPushButton(MainWindow)
        self.SUB_REAC_ACT.setGeometry(QtCore.QRect(300, 370, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.SUB_REAC_ACT.setFont(font)
        self.SUB_REAC_ACT.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                        "border-radius: 0px rgb(0, 255, 255);\n"
                                        "background-color: rgb(0, 0, 0);\n"
                                        "color: rgb(0, 255, 255);")
        self.SUB_REAC_ACT.setObjectName("SUB_REAC_ACT")
        self.REAC_out = QtWidgets.QLineEdit(MainWindow)
        self.REAC_out.setGeometry(QtCore.QRect(390, 370, 211, 31))
        self.REAC_out.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                    "color: rgb(0, 255, 255);")
        self.REAC_out.setObjectName("REAC_out")
        self.label_12 = QtWidgets.QLabel(MainWindow)
        self.label_12.setGeometry(QtCore.QRect(80, 410, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_12.setFont(font)
        self.label_12.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                    "color: rgb(0, 255, 255);\n"
                                    "border: 2px solid rgb(0, 255, 255);")
        self.label_12.setScaledContents(False)
        self.label_12.setAlignment(QtCore.Qt.AlignCenter)
        self.label_12.setObjectName("label_12")
        self.REAC_reag1 = QtWidgets.QLabel(MainWindow)
        self.REAC_reag1.setGeometry(QtCore.QRect(170, 410, 161, 31))
        self.REAC_reag1.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                      "color: rgb(0, 255, 255);")
        self.REAC_reag1.setObjectName("REAC_reag1")
        self.REAC_reag2 = QtWidgets.QLabel(MainWindow)
        self.REAC_reag2.setGeometry(QtCore.QRect(440, 410, 161, 31))
        self.REAC_reag2.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                      "color: rgb(0, 255, 255);")
        self.REAC_reag2.setObjectName("REAC_reag2")
        self.label_15 = QtWidgets.QLabel(MainWindow)
        self.label_15.setGeometry(QtCore.QRect(350, 410, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_15.setFont(font)
        self.label_15.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                    "color: rgb(0, 255, 255);\n"
                                    "border: 2px solid rgb(0, 255, 255);")
        self.label_15.setScaledContents(False)
        self.label_15.setAlignment(QtCore.Qt.AlignCenter)
        self.label_15.setObjectName("label_15")
        self.REAC_prod1 = QtWidgets.QLabel(MainWindow)
        self.REAC_prod1.setGeometry(QtCore.QRect(170, 450, 161, 31))
        self.REAC_prod1.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                      "color: rgb(0, 255, 255);")
        self.REAC_prod1.setObjectName("REAC_prod1")
        self.label_17 = QtWidgets.QLabel(MainWindow)
        self.label_17.setGeometry(QtCore.QRect(80, 450, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_17.setFont(font)
        self.label_17.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                    "color: rgb(0, 255, 255);\n"
                                    "border: 2px solid rgb(0, 255, 255);")
        self.label_17.setScaledContents(False)
        self.label_17.setAlignment(QtCore.Qt.AlignCenter)
        self.label_17.setObjectName("label_17")
        self.REAC_prod2 = QtWidgets.QLabel(MainWindow)
        self.REAC_prod2.setGeometry(QtCore.QRect(440, 450, 161, 31))
        self.REAC_prod2.setStyleSheet("border: 2px solid rgb(0, 255, 255);\n"
                                      "color: rgb(0, 255, 255);")
        self.REAC_prod2.setObjectName("REAC_prod2")
        self.label_19 = QtWidgets.QLabel(MainWindow)
        self.label_19.setGeometry(QtCore.QRect(350, 450, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_19.setFont(font)
        self.label_19.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                    "color: rgb(0, 255, 255);\n"
                                    "border: 2px solid rgb(0, 255, 255);")
        self.label_19.setScaledContents(False)
        self.label_19.setAlignment(QtCore.Qt.AlignCenter)
        self.label_19.setObjectName("label_19")
        self.DATABASE_ACT = QtWidgets.QPushButton(MainWindow)
        self.DATABASE_ACT.setGeometry(QtCore.QRect(990, 10, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(10)
        self.DATABASE_ACT.setFont(font)
        self.DATABASE_ACT.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                        "color: rgb(255, 0, 0);\n"
                                        "border: 2px solid rgb(255, 0, 0);")
        self.DATABASE_ACT.setObjectName("DATABASE_ACT")
        self.DB_IN = QtWidgets.QLineEdit(MainWindow)
        self.DB_IN.setGeometry(QtCore.QRect(860, 60, 261, 51))
        self.DB_IN.setStyleSheet("border: 2px solid rgb(255, 0, 0);\n"
                                 "color: rgb(255, 0, 0);")
        self.DB_IN.setObjectName("Calc_in_2")
        self.DB_CHANGER = QtWidgets.QPushButton(MainWindow)
        self.DB_CHANGER.setGeometry(QtCore.QRect(860, 120, 261, 31))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift SemiBold")
        font.setPointSize(20)
        self.DB_CHANGER.setFont(font)
        self.DB_CHANGER.setStyleSheet("border: 2px solid rgb(255, 0, 0);\n"
                                      "background-color: rgb(0, 0, 0);\n"
                                      "color: rgb(255, 0, 0);")
        self.DB_CHANGER.setObjectName("SUB_CORR_ACT_2")
        self.DB_OUT = QtWidgets.QLineEdit(MainWindow)
        self.DB_OUT.setGeometry(QtCore.QRect(860, 160, 261, 51))
        self.DB_OUT.setStyleSheet("border: 2px solid rgb(255, 0, 0);\n"
                                  "color: rgb(255, 0, 0);")
        self.DB_OUT.setObjectName("Calc_in_3")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "CHEMISTRY CALCULATOR"))
        self.label.setText(_translate("MainWindow", "CALCULATOR"))
        self.CALC_ACT.setText(_translate("MainWindow", ">>"))
        self.label_2.setText(_translate("MainWindow", "MOLAR MASS"))
        self.SUB_MMASS_ACT.setText(_translate("MainWindow", ">>"))
        self.label_3.setText(_translate("MainWindow", "ELECTRONIC CONFIGURATION"))
        self.SUB_ELCONF_ACT.setText(_translate("MainWindow", ">>"))
        self.label_4.setText(_translate("MainWindow", "SUBSTANCE"))
        self.label_5.setText(_translate("MainWindow", "MAKE A SUBSTANCE"))
        self.label_6.setText(_translate("MainWindow", "+"))
        self.SUB_MAKE_ACT.setText(_translate("MainWindow", ">>"))
        self.label_7.setText(_translate("MainWindow", "DEFINE SOLUBILITY IN WATER"))
        self.SUB_SOL_ACT.setText(_translate("MainWindow", ">>"))
        self.label_8.setText(_translate("MainWindow", "DEFINE CATION/ANION CORROSION"))
        self.SUB_CORR_ACT.setText(_translate("MainWindow", ">>"))
        self.label_9.setText(_translate("MainWindow", "CATION:"))
        self.label_10.setText(_translate("MainWindow", "ANION:"))
        self.label_11.setText(_translate("MainWindow", "CHEMICAL REACTIONS"))
        self.SUB_REAC_ACT.setText(_translate("MainWindow", ">>"))
        self.label_12.setText(_translate("MainWindow", "REAGENT 1:"))
        self.REAC_reag1.setText(_translate("MainWindow", "NONE"))
        self.REAC_reag2.setText(_translate("MainWindow", "NONE"))
        self.label_15.setText(_translate("MainWindow", "REAGENT 2:"))
        self.REAC_prod1.setText(_translate("MainWindow", "NONE"))
        self.label_17.setText(_translate("MainWindow", "PRODUCT 1:"))
        self.REAC_prod2.setText(_translate("MainWindow", "NONE"))
        self.label_19.setText(_translate("MainWindow", "PRODUCT 2:"))
        self.DATABASE_ACT.setText(_translate("MainWindow", "CHANGE DATABASES"))
        self.DB_CHANGER.setText(_translate("MainWindow", "EXECUTE"))


class ChemApp(QtWidgets.QWidget, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setupUi(MainWindow=self)
        self.CALC_ACT.clicked.connect(self.CALC_EVENT)
        self.SUB_MAKE_ACT.clicked.connect(self.SUB_MAKE_EVENT)
        self.SUB_SOL_ACT.clicked.connect(self.SUB_SOL_EVENT)
        self.SUB_CORR_ACT.clicked.connect(self.SUB_CORR_EVENT)
        self.SUB_MMASS_ACT.clicked.connect(self.SUB_MMASS_EVENT)
        self.SUB_ELCONF_ACT.clicked.connect(self.SUB_ELCONF_EVENT)
        self.SUB_REAC_ACT.clicked.connect(self.REAC_ACT)
        self.DB_CHANGER.clicked.connect(self.DATABASE_EVENT)

    def CALC_EVENT(self):
        try:
            self.Calc_out.setText(str(eval(self.Calc_in.text())))
        except Exception as er:
            self.Calc_out.setText('ERROR')
            print(er)

    def SUB_MAKE_EVENT(self):
        try:
            self.SUB_sub.setText(substance(self.SUB_cation.text(), self.SUB_anion.text()))
        except Exception as er:
            self.SUB_sub.setText('ERROR')
            print(er)

    def SUB_SOL_EVENT(self):
        try:
            self.SUB_SolSub_out.setText(define_solubility(self.SUB_SolSub_in.text()))
        except Exception as er:
            self.SUB_SolSub_out.setText('ERROR')
            print(er)

    def SUB_CORR_EVENT(self):
        try:
            self.SUB_corrCat_out.setText(str(define_cation_corrosion(self.SUB_corr_in.text())))
            self.SUB_corrAn_out.setText(str(define_anion_corrosion(self.SUB_corr_in.text())))
        except Exception as er:
            self.SUB_corrCat_out.setText('E')
            self.SUB_corrAn_out.setText('E')
            print(er)

    def SUB_MMASS_EVENT(self):
        try:
            self.SUB_Mmass_out.setText(str(molar_mass(self.SUB_Mmass_in.text())))
        except Exception as er:
            self.SUB_Mmass_out.setText('ERROR')
            print(er)

    def SUB_ELCONF_EVENT(self):
        try:
            self.SUB_elConf_out.setText(electron_config(self.SUB_elConf_in.text()))
        except Exception as er:
            self.SUB_elConf_out.setText('ERROR')
            print(er)

    def REAC_ACT(self):
        try:
            c = self.REAC_in.text().split(' + ')
            a, b = c[0], c[1]
            self.REAC_out.setText(chemical_change_reaction(a, b))
        except Exception as er:
            self.REAC_out.setText('ERROR')
            print(er)

    def DATABASE_EVENT(self):
        command = self.DB_IN.text()
        try:
            db.execute(command)
            self.DB_OUT.setText('SUCCESS')
        except Exception as er:
            self.DB_OUT.setText('ERROR')
            print(er)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    exe = ChemApp()
    exe.show()
    sys.exit(app.exec())

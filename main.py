import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QSlider, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QFont

class Grzalka:
    def __init__(self, moc = 0.08):
        self.moc = moc # moc to tempo wzrostu temperatury w kazdym kroku symulacji
        self.wlaczona = False
    
    def step(self, zbiornik):
        if self.wlaczona:
            zbiornik.temperatura += self.moc
        else:
            zbiornik.temperatura -= 0.02
        #j esli grzalka grzeje to rosnie temperatura, a jesli nie grzeje to powoli stygnie
        
class RegulatorTemp:
    def __init__(self, zbiornik, T_zadana = 20):
        self.zbiornik = zbiornik
        self.T_zadana = T_zadana
    def step(self):
        self.zbiornik.grzalka.wlaczona = (
            self.zbiornik.temperatura < self.T_zadana
        )
        # true (czyli wlaczona) jesli temperatura w zbiorniku jest mniejsza niz zadana,
        # czyli musi grzac

class Rura:
    def __init__(self,punkty, grubosc = 12, kolor = Qt.gray):
        self.punkty = [QPointF(float(p[0]), float(p[1])) for p in punkty]
        self.grubosc = grubosc
        self.kolor_rury = kolor
        self.kolor_cieczy = Qt.white
        self.czy_plynie = False
        
    def draw(self, painter):
        if not self.punkty:
            return

        path = QPainterPath()
        path.moveTo(self.punkty[0])
        for p in self.punkty[1:]:
            path.lineTo(p)

        painter.setPen(QPen(
            self.kolor_rury, self.grubosc,
            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
        ))
        painter.drawPath(path)

        if self.czy_plynie:
            painter.setPen(QPen(
                self.kolor_cieczy, self.grubosc - 4,
                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
            ))
            painter.drawPath(path)

class Zbiornik:
    def __init__(self, x, y, width=80, height=120, nazwa=""):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.nazwa = nazwa

        self.poziom = 0.0
        self.temperatura = 20.0

        self.grzalka = Grzalka()
        
    def punkt_dol_srodek(self):
        return (self.x + self.width / 2, self.y + self.height)

    def punkt_gora_srodek(self):
        return (self.x + self.width / 2, self.y)
    
    def draw(self, painter):
        # ciecz w zbiorniku
        if self.poziom > 0:
            h = (self.height - 4) * self.poziom
            painter.setBrush(QColor(245, 245, 235))
            painter.setPen(Qt.NoPen)
            painter.drawRect(
                int(self.x + 2),
                int(self.y + self.height - h - 2),
                int(self.width - 4),
                int(h)
            )

        # obrys
        painter.setPen(QPen(Qt.white, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.x, self.y, self.width, self.height)

        # nazwa
        painter.setPen(Qt.white)
        painter.setFont(QFont('Arial', 9, QFont.Bold))
        painter.drawText(self.x, self.y - 12, self.nazwa)

        # podpisana temperatura
        painter.setFont(QFont('Arial', 8))
        painter.drawText(
            self.x,
            self.y + self.height + 14,
            f"T = {self.temperatura:.1f} °C"
        )
        
        # stan grzalki
        stan = "ON" if self.grzalka.wlaczona else "OFF"
        kolor = QColor(0, 255, 0) if self.grzalka.wlaczona else QColor(255, 80, 80)
        painter.setPen(kolor)
        painter.setFont(QFont('Arial', 8, QFont.Bold))
        painter.drawText(
            self.x,
            self.y - 26,
            f"Grzałka: {stan}"
        )
class EkranProcesu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.z1 = Zbiornik(50, 120, nazwa="Mleko surowe")
        self.z1.poziom = 1.0

        self.z2 = Zbiornik(250, 120, nazwa="Pasteryzator")
        self.z3 = Zbiornik(470, 120, nazwa="Fermentor")
        self.z4 = Zbiornik(690, 120, nazwa="Gotowa maślanka")

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4]
        
        self.reg_past = RegulatorTemp(self.z2, 72)
        self.reg_ferment = RegulatorTemp(self.z3, 22)
        
        self.czas_ferment = 0.0
        self.czas_ferment_wymagany = 2.0
        
        self.setup_rury()
        
    def setup_rury(self):
        p1 = self.z1.punkt_dol_srodek()
        p2 = self.z2.punkt_gora_srodek()
        self.r1 = Rura([p1,
                        (p1[0], p1[1] + 40),
                        ((p2[0] + p1[0])/2, p1[1] + 40),
                        ((p2[0] + p1[0])/2, p2[1] - 40),
                        (p2[0],p2[1] - 40),
                        p2])
        p3 = self.z2.punkt_dol_srodek()
        p4 = self.z3.punkt_gora_srodek()
        self.r2 = Rura([p3,
                        (p3[0], p3[1] + 40),
                        ((p4[0] + p3[0])/2, p3[1] + 40),
                        ((p4[0] + p3[0])/2, p4[1] - 40),
                        (p4[0],p4[1] - 40),
                        p4])
        p5 = self.z3.punkt_dol_srodek()
        p6 = self.z4.punkt_gora_srodek()
        self.r3 = Rura([p5,
                        (p5[0], p5[1] + 40),
                        ((p6[0] + p5[0])/2, p5[1] + 40),
                        ((p6[0] + p5[0])/2, p6[1] - 40),
                        (p6[0],p6[1] - 40),
                        p6])
        self.rury = [self.r1, self.r2, self.r3]
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for r in self.rury:
            r.draw(painter)

        for z in self.zbiorniki:
            z.draw(painter)
            
class EkranStatusu(QWidget):
    def __init__(self, ekran_procesu):
        super().__init__()

        self.ekran_procesu = ekran_procesu

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 22px;")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # timer odświeżający napis
        self.timer = QTimer()
        self.timer.timeout.connect(self.aktualizuj)
        self.timer.start(200)

    def aktualizuj(self):
        z4 = self.ekran_procesu.z4

        if z4.poziom > 0:
            self.label.setText(
                "<h2 style='color:#88ff88'>Maślanka jest GOTOWA do picia.</h2>"
            )
        else:
            self.label.setText(
                "<h2 style='color:#ffaaaa'>Maślanka jeszcze NIE jest gotowa.</h2>"
            )
            
class GlowneOkno(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Produkcja maslanki")
        self.setFixedSize(1000,640)
        self.setStyleSheet("background-color: #2b2b2b;")

        self.layout = QVBoxLayout()
        self.stack = QStackedWidget()

        self.widok_procesu = EkranProcesu()
        self.widok_statusu = EkranStatusu(self.widok_procesu)

        self.stack.addWidget(self.widok_procesu)
        self.stack.addWidget(self.widok_statusu)
        
        # panel z nastawianiem wartosci zadanych
        panel = QGroupBox("Wartosci zadane")
        panel.setStyleSheet("color: white")
        form = QFormLayout()

        self.slider_past = QSlider(Qt.Horizontal)
        self.slider_past.setRange(60, 95)
        self.slider_past.setValue(72)

        self.slider_ferment = QSlider(Qt.Horizontal)
        self.slider_ferment.setRange(18, 30)
        self.slider_ferment.setValue(22)

        form.addRow("Temperatura pasteryzacji (60 - 95 [°C])", self.slider_past)
        form.addRow("Temperatura fermentacji (18 - 30 [°C])", self.slider_ferment)

        panel.setLayout(form)
        
        # przyciski
        btns = QHBoxLayout()
        self.btn_start = QPushButton("START")
        self.btn_widok = QPushButton("WIDOK STATUSU")

        self.btn_start.setStyleSheet(
                "background:#444;color:white;height:36px;"
                )
        self.btn_widok.setStyleSheet(
                "background:#444;color:white;height:36px;"
                )
        btns.addWidget(self.btn_start)
        btns.addWidget(self.btn_widok)
        
        self.layout.addWidget(self.stack)
        self.layout.addWidget(panel)
        self.layout.addLayout(btns)
        self.setLayout(self.layout)
        
        # timer, odswiezanie
        self.timer = QTimer()
        self.timer.timeout.connect(self.logika)

        self.btn_start.clicked.connect(self.przelaczanie)
        self.btn_widok.clicked.connect(
            lambda: self.stack.setCurrentIndex(
                1 - self.stack.currentIndex()
            )
        )

        self.running = False
        
    def przelaczanie(self):
        self.running = not self.running
        if self.running:
            self.timer.start(50)
            self.btn_start.setText("STOP")
        else:
            self.timer.stop()
            self.btn_start.setText("START")
    
    def logika(self):
        v = self.widok_procesu
        speed = 0.004

        # aktualizacja wartosci zadanych
        v.reg_past.T_zadana = self.slider_past.value()
        v.reg_ferment.T_zadana = self.slider_ferment.value()

        # regulatory i grzalki
        v.reg_past.step()
        v.reg_ferment.step()

        v.z2.grzalka.step(v.z2)
        v.z3.grzalka.step(v.z3)

        # przeplyw z z1 do z2
        if v.z1.poziom > 0.01 and v.z2.poziom < 0.99:
            v.z1.poziom -= speed
            v.z2.poziom += speed
            v.r1.czy_plynie = True
        else:
            v.r1.czy_plynie = False

        # od z2 do z3
        if v.z2.temperatura > v.reg_past.T_zadana - 1 and v.z2.poziom > 0.01:
            v.z2.poziom -= speed
            v.z3.poziom += speed
            v.r2.czy_plynie = True
        else:
            v.r2.czy_plynie = False


        # fermentacja w czasie
        if v.z3.poziom > 0.2:
            v.czas_ferment += 0.05

        # po fermentacji przeplyw od z3 do z4
        if v.czas_ferment > v.czas_ferment_wymagany:
            if v.z3.poziom > 0.01:
                v.z3.poziom -= speed
                v.z4.poziom += speed
                v.r3.czy_plynie = True
        else:
            v.r3.czy_plynie = False

        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    okno = GlowneOkno()
    okno.show()
    sys.exit(app.exec_())
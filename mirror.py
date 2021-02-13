from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from forecastiopy import *
from datetime import datetime
import time, calendar, math, os, gapi
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

try:
    FORECASTIO_KEY = parser.get('FORECASTIO', 'Key')
    LATITUDE = parser.get('FORECASTIO', 'Lat')
    LONGITUDE = parser.get('FORECASTIO', 'Long')
    weather = ForecastIO.ForecastIO(FORECASTIO_KEY, latitude=LATITUDE, longitude=LONGITUDE)
except:
    print('update forecast io credentials')
    # display 'Update Forecast IO Credentials' warning
    # disable weather feature

try:
    CALENDAR_ID = parser.get('CALENDAR', 'ID')
    CALENDAR_SECRET = parser.get('CALENDAR', 'Secret')
    CALENDAR_API_KEY = parser.get('CALENDAR', 'APIKey')
    CALENDAR_DISCOVERY_DOCS = parser.get('CALENDAR', 'DiscoveryDocs')
    CALENDAR_SCOPES = parser.get('CALENDAR', 'Scopes')
except:
    print('update forecast io credentials')
    # display 'Update Google Calendar Credentials' warning
    # disable calendar feature

DEG = u'\N{DEGREE SIGN}'
UP_ARROW = u'\N{WIDE-HEADED UPWARDS LIGHT BARB ARROW}'
DOWN_ARROW = u'\N{WIDE-HEADED DOWNWARDS LIGHT BARB ARROW}'

FONT = 'Roboto'
FONT_PATH = 'Roboto-Light.ttf'

WHITE = QColor(255, 255, 255)
LIGHT_GRAY = QColor(136, 136, 136)
GRAY = QColor(85, 85, 85)
BLACK = QColor(0, 0, 0)

SMALL_FONT = 15
MEDIUM_FONT = 25
LARGE_FONT = 60

WIDGET_STYLE = lambda color, font_size: "background-color: %s; color: %s; font-size: %dpt; font-family: '%s';" % (BLACK.name(), color.name(), font_size, FONT)

ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(math.floor(n / 10) % 10 != 1)*(n % 10 < 4) * n % 10::4])
hh = lambda hh: "%d" % (12 if hh % 12 == 0 else hh % 12)
mm = lambda mm: ("0" + str(mm)) if mm < 10 else str(mm)
meridian = lambda h: "%s%sm" % (hh(h), "ap"[math.floor(h / 12) % 2])

path = os.path.dirname(os.path.abspath(__file__))

current = FIOCurrently.FIOCurrently(weather)
daily = FIODaily.FIODaily(weather).get_day(0)

class Mirror(QMainWindow):
    def __init__(self):
        super().__init__()
        shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut.activated.connect(self.exitGUI)
        self.timeTimer = QTimer(self)
        self.timeTimer.timeout.connect(self.updateTime)
        self.initUI()
        self.initWeather()
        self.updateTime()
        self.updateDate()
        self.setStyle()
    
    def initUI(self):
        self.day = QLabel('', self)
        self.day.setGeometry(100, 80, 541, 40)
        self.time = QLabel('', self)
        self.time.setGeometry(100, 130, 300, 100)
        self.temp = QLabel('', self)
        self.temp.setGeometry(1485, 90, 190, 90)
        self.icon = QLabel('', self)
        self.icon.setGeometry(1730, 99, 80, 80)
        self.upArrow = QLabel('', self)
        self.upArrow.setGeometry(1560, 182, 25, 25)
        self.high = QLabel('', self)
        self.high.setGeometry(1590, 185, 55, 25)
        self.downArrow = QLabel('', self)
        self.downArrow.setGeometry(1705, 185, 25, 25)
        self.low = QLabel('', self)
        self.low.setGeometry(1735, 185, 55, 25)
        self.apparent = QLabel('', self)
        self.apparent.setGeometry(1590, 220, 180, 25)
    
    def setStyle(self):
        QFontDatabase.addApplicationFont(os.path.join(path, FONT_PATH))
        self.setStyleSheet(WIDGET_STYLE(WHITE, SMALL_FONT))
        self.day.setStyleSheet(WIDGET_STYLE(LIGHT_GRAY, MEDIUM_FONT))
        self.time.setStyleSheet(WIDGET_STYLE(WHITE, LARGE_FONT))
        self.temp.setStyleSheet(WIDGET_STYLE(WHITE, LARGE_FONT))
        self.upArrow.setStyleSheet(WIDGET_STYLE(LIGHT_GRAY, SMALL_FONT))
        self.high.setStyleSheet(WIDGET_STYLE(LIGHT_GRAY, SMALL_FONT))
        self.downArrow.setStyleSheet(WIDGET_STYLE(LIGHT_GRAY, SMALL_FONT))
        self.low.setStyleSheet(WIDGET_STYLE(LIGHT_GRAY, SMALL_FONT))
        self.apparent.setStyleSheet(WIDGET_STYLE(GRAY, SMALL_FONT))
        for i in range(0, 3):
            self.times[i].setStyleSheet(WIDGET_STYLE(WHITE, SMALL_FONT))
            self.temps[i].setStyleSheet(WIDGET_STYLE(WHITE, SMALL_FONT))
        self.times[3].setStyleSheet(WIDGET_STYLE(LIGHT_GRAY, SMALL_FONT))
        self.temps[3].setStyleSheet(WIDGET_STYLE(LIGHT_GRAY, SMALL_FONT))
        self.times[4].setStyleSheet(WIDGET_STYLE(GRAY, SMALL_FONT))
        self.temps[4].setStyleSheet(WIDGET_STYLE(GRAY, SMALL_FONT))

    def change_color(self, icon, pixmap, color):
        mask = pixmap.createMaskFromColor(QColor('white'), Qt.MaskOutColor)
        pixmap.fill(color)
        pixmap.setMask(mask)
        icon.setIcon(QIcon(pixmap))

    def initWeather(self):
        self.times = []
        self.icons = []
        self.temps = []
        self.today = datetime.today()
        self.weatherTimer = QTimer(self)
        self.weatherTimer.timeout.connect(self.updateWeather)
        self.upArrow.setText(UP_ARROW)
        self.downArrow.setText(DOWN_ARROW)
        for i in range(0, 5):
            self.times.append(QLabel('', self))
            self.times[i].setFixedSize(70, 50)
            self.times[i].move(1525, (50 * (i + 1)) + 240)
            self.times[i].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.icons.append(QPushButton('', self))
            self.icons[i].setFixedSize(50, 50)
            self.icons[i].move(1650, (50 * (i + 1)) + 240)
            self.icons[i].setIconSize(QSize(50, 50))
            self.temps.append(QLabel('', self))
            self.temps[i].setFixedSize(50, 50)
            self.temps[i].move(1755, (50 * (i + 1)) + 240)
        self.updateWeather()

    def updateWeather(self):
        self.hourly = []
        self.temp.setText(str(round(current.temperature)) + DEG)
        self.icon.setPixmap(QPixmap(os.path.join(path, 'images/' + current.icon + '.png')).scaled(80, 80, QtCore.Qt.KeepAspectRatio))
        self.high.setText(str(round(daily['temperatureHigh'])) + DEG)
        self.low.setText(str(round(daily['temperatureLow'])) + DEG)
        self.apparent.setText('Feels like ' + str(round(current.apparentTemperature)) + DEG)
        self.hour = datetime.today().hour
        for i in range(0, 5):
            self.hourly.append(FIOHourly.FIOHourly(weather).get_hour(i + 1))
            self.times[i].setText(meridian(self.hour + i + 1))
            self.temps[i].setText(str(round(self.hourly[i]['temperature'])) + DEG)
        for i in range(0, 3):
            self.icons[i].setIcon(QIcon(os.path.join(path, 'images/' + self.hourly[i]['icon'] + '.png')))
        pixmap3 = QPixmap(os.path.join(path, 'images/' + self.hourly[3]['icon'] + '.png'))
        self.change_color(self.icons[3], pixmap3, LIGHT_GRAY)
        pixmap4 = QPixmap(os.path.join(path, 'images/' + self.hourly[4]['icon'] + '.png'))
        self.change_color(self.icons[4], pixmap4, GRAY)
        self.weatherTimer.start(1800000)

    def initCalendar(self):
        #gapi.client.init({apiKey=API_KEY, clientId=CLIENT_ID, discoveryDocs=DISCOVERY_DOCS, scope=SCOPES})
        gapi.auth2.getAuthInstance()

    def updateTime(self):
        self.time.setText(hh(self.today.hour) + ':' + mm(self.today.minute))
        self.timeTimer.start(60000)

    def updateDate(self):
        day = calendar.day_name[self.today.weekday()]
        month = calendar.month_name[self.today.month]
        date = ordinal(self.today.day)
        year = self.today.year
        self.day.setText("%s, %s %s, %d" % (day, month, date, year))

    def exitGUI(self):
        exit()

if __name__ == "__main__":
    mirror = QApplication([])
    window = Mirror()
    window.showFullScreen()
    mirror.exec()
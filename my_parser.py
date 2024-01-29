import sys
import os
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QButtonGroup, QVBoxLayout, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from settings import *
import settings
from pygame import mixer
from style import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import win10toast
from collections import deque
import requests
import json


bot_token = '6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4'
chat_id = '-4129523904'
message = 'Привет, это тестовое сообщение от моего бота!'


def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()

class ParserThread(QThread):
    live_signal = pyqtSignal(str)
    is_running = True
    live_status_changed = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super(ParserThread, self).__init__(parent)
        
    def run(self):
        with self.get_chromedriver(use_proxy=False, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36') as driver:
            driver.get('https://www.wrewards.com/')

            while self.is_running:
                try:
                    self.live_obj_parse(driver)
                    time.sleep(30)
                except WebDriverException as e:
                    print('Окно браузера было закрыто или принудительно остановленно.')
                    break
                except Exception as ex:
                    print('=====ERROR=====')
                    print(ex)
           
    def get_chromedriver(self, use_proxy=False, user_agent=None):
    
        chrome_options = webdriver.ChromeOptions()
        
        if use_proxy:
            chrome_options.add_argument('--proxy-server=193.32.155.4:8000')

        if user_agent:
            chrome_options.add_argument(f'--user-agent={user_agent}')
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
                
        s = Service(
            executable_path='chromdriver/chromedriver.exe'
        )
        
        driver = webdriver.Chrome(
            service= s,
            options=chrome_options
        )

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        '''
        })

        return driver
    
    
    def live_obj_parse(self, driver):
        live_streamers = []

        def count_direct_children(driver, parent_element):
            script = "return arguments[0].childElementCount;"
            return driver.execute_script(script, parent_element)
        
        if driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.hebpcf'):
            live_wrewards_obj = driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.hebpcf')
            child_elements = count_direct_children(driver, live_wrewards_obj)
            if child_elements > 3:
                #send_telegram_message(bot_token, chat_id, 'Wrewards стримит! Бородка дряхлая.')
                print('Найдена трансляция на канале Wrewards')
                live_streamers.append('wrewards')

        if driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.loEfmC'):
            live_pkle_obj = driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.loEfmC')
            child_elements = count_direct_children(driver, live_pkle_obj)
            if child_elements > 3:
                #send_telegram_message(bot_token, chat_id, 'PKLE стримит!')
                print('Найдена трансляция на канале PKLE')
                live_streamers.append('pkle')   

        if driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.hDkoy'):
            live_hyus_obj = driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.hDkoy')
            child_elements = count_direct_children(driver, live_hyus_obj)
            if child_elements > 3:
                #send_telegram_message(bot_token, chat_id, 'Hyus стримит!')
                print('Найдена трансляция на канале Hyus')
                live_streamers.append('hyus')

        if driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.hujkXc'):
            live_watchgamestv_obj = driver.find_element(By.CLASS_NAME, 'sc-8a9b0271-11.hujkXc')
            child_elements = count_direct_children(driver, live_watchgamestv_obj)
            if child_elements > 3:
                #send_telegram_message(bot_token, chat_id, 'Watchgamestv стримит!')
                print('Найдена трансляция на канале Watchgamestv')
                live_streamers.append('watchgamestv')

        if live_streamers:
            self.live_status_changed.emit(live_streamers)
            print('стримеры переданы дальше')
            print(live_streamers)
            #time.sleep(7200)
                 
    def stop(self):
        self.is_running = False
        
class ChatParserThread(QThread):
    def __init__(self, streamer=None, parent=None):
        super(ChatParserThread, self).__init__(parent)
        self.is_running = True
        self.streamer = streamer
        
    def run(self):            
        with self.get_chromedriver(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36') as driver:
            print('Окно браузера запущено.')
            driver.get(f'https://kick.com/{self.streamer}/chatroom')
            #driver.get(f'https://kick.com/')
            print('Сайт прогружен и готов к работе.')
            
            old_messages = deque(maxlen=200)
            
            while self.is_running:
                try:
                    self.message_parse(driver, old_messages)
                    
                    # print('Записываю куки.')
                    # cookies = driver.get_cookies()
                    # with open("cookies.json", "w") as file:
                    #     json.dump(cookies, file)
                    #     print('Куки записаны.')
                    
                except StaleElementReferenceException:
                    print('=====StaleElementReferenceException=====')
                except TimeoutException:
                    print('=====TimeoutException=====')
                except WebDriverException as e:
                    print(e)
                    print('Окно браузера было закрыто или принудительно остановленно.')
                    driver.close()
                except Exception as ex:
                    print('=====ERROR=====')
                    print(ex)
                    
    
    def get_chromedriver(self, user_agent=None):
    
        chrome_options = webdriver.ChromeOptions()
    
        if user_agent:
            chrome_options.add_argument(f'--user-agent={user_agent}')
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        #chrome_options.add_argument("--headless")
        #chrome_options.add_argument("--disable-gpu")
                
        s = Service(
            executable_path='chromdriver/chromedriver.exe'
        )
        
        driver = webdriver.Chrome(
            service= s,
            options=chrome_options
        )

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        '''
        })

        return driver

    def message_parse(self, driver, old_messages):
        messages = driver.find_elements(By.XPATH, '//*[@id="chatroom"]/div[2]/div[1]/div')
        for message in messages:
            message_id = message.get_attribute('data-chat-entry')
            
            if message_id in old_messages:
                continue
            else:
                old_messages.append(message_id)
                split_message = message.text.split(':')
                if len(split_message) > 1:
                    message_author = split_message[0]
                    message_msg = split_message[1]
                else:
                    message_author = split_message[0]
                    message_msg = ""
                
                if message_msg:
                    print(message.text)
            
                if 'WRewardsBot' in message_author:
                    if 'A Raffle Started' in message_msg:
                        send_telegram_message(bot_token, chat_id, 'Раздача поинтов началась.\nЗайдите на стрим и напишите "WG" в чат.')
                        #toast = win10toast.ToastNotifier()
                        #toast.show_toast(title='Раздача поинтов началась', msg='Зайдите на стрим и напишите "WG" в чат.', duration=10)
                        time.sleep(50)     
                        break
    
    def stop(self):
        self.is_running = False
                
class ParserApp(QWidget, settings.Ui_MainWindow):
    def __init__(self):
        super(ParserApp, self).__init__()   
        self.setupUi(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        normal_cursor_path = 'cursor/Glib Cur v3 (Rounded)/Normal Select.cur'
        normal_cursor_pixmap = QtGui.QPixmap(normal_cursor_path)
        normal_cursor = QtGui.QCursor(normal_cursor_pixmap, 0, 0)
        self.setCursor(normal_cursor)
        text_cursor_path = 'cursor/Glib Cur v3 (Rounded)/beam.cur'
        text_cursor_pixmap = QtGui.QPixmap(text_cursor_path )
        self.setupUi(self)
        self.setFixedSize(self.size())
        
        self.sound_mixer = mixer
        self.sound_mixer.init()
        
        self.stop_button.lower()
        self.stop_button.clicked.connect(self.stop_parser_update_page)
        self.in_progress.lower()
        
        self.live_hyus.lower()
        self.live_pkle.lower()
        self.live_watchgamestv.lower()
        self.live_wrewards.lower()
        
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.wrewards_radio, 1)
        self.button_group.addButton(self.pkle_radio, 2)
        self.button_group.addButton(self.watchgamestv_radio, 3)
        self.button_group.addButton(self.hyus_radio, 4)
        
        self.selected_button_id = self.button_group.checkedId()
        self.streamer = None
        
        self.login_button.clicked.connect(self.login_button_act)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: white; /* Исходный цвет */
                border: 1px solid #8f8f91; /* Граница, если нужно */
            }
            QPushButton:hover {
                background-color: #dcdcdc; /* Цвет при наведении */
            }
        """)
        self.close_button.clicked.connect(self.close_button_act)
        self.wrap_button.clicked.connect(self.wrap_button_act)
        
        self.start_live_parser_parserapp()
        self.parser_thread.live_status_changed.connect(self.update_live_icon)
        
    def start_live_parser_parserapp(self):
        self.parser_thread = ParserThread()
        self.parser_thread.live_signal.connect(self.update_live_icon)
        self.parser_thread.start()

    def update_live_icon(self, live_streamers):
        if 'hyus' in live_streamers:
            self.live_hyus.raise_()
            self.description.setText('Найдена трансляция! Выберите стримера чат которого будем парсить.')
        if 'wrewards' in live_streamers:
            self.live_wrewards.raise_()
            self.description.setText('Найдена трансляция! Выберите стримера чат которого будем парсить.')
        if 'watchgamestv' in live_streamers:
            self.live_watchgamestv.raise_()
            self.description.setText('Найдена трансляция! Выберите стримера чат которого будем парсить.')
        if 'pkle' in live_streamers:
            self.live_pkle.raise_()
            self.description.setText('Найдена трансляция! Выберите стримера чат которого будем парсить.')
                
    def login_button_act(self):
        self.sound_mixer.music.load('sound/main.mp3')
        self.sound_mixer.music.play()
        self.sound_mixer.music.set_volume(0.5)
        
        self.selected_button_id = self.button_group.checkedId()
        
        if self.selected_button_id == 1:
            self.streamer = 'wrewards'
        elif self.selected_button_id == 2:
            self.streamer = 'pkle'
        elif self.selected_button_id == 3:
            self.streamer = 'watchgamestv'
        elif self.selected_button_id == 4:
            self.streamer = 'hyuslive'

        self.parser_thread.stop()
        
        self.description.setText('Если парсер вдруг прекратит работу, просто перезапуститее его.')
                        
        print(self.selected_button_id)
        print(self.streamer)
        
        self.chat_parser_thread = ChatParserThread(self.streamer)
        self.chat_parser_thread.finished.connect(self.chat_parser_thread.deleteLater)
        self.chat_parser_thread.start()
        
        
        self.start_parser_update_page()

    def start_parser_update_page(self):
        self.login_button.lower()
        self.live_hyus.lower()
        self.live_pkle.lower()
        self.live_watchgamestv.lower()
        self.live_wrewards.lower()
        self.pkle.lower()
        self.pkle_radio.lower()
        self.wrewards.lower()
        self.wrewards_radio.lower()
        self.hyus.lower()
        self.hyus_radio.lower()
        self.watchgamestv.lower()
        self.watchgamestv_radio.lower()
        
        self.stop_button.raise_()
        self.in_progress.raise_()
        
    def stop_parser_update_page(self):
        self.sound_mixer.music.load('sound/main.mp3')
        self.sound_mixer.music.play()
        self.sound_mixer.music.set_volume(0.5)
        
        self.login_button.raise_()
        self.pkle.raise_()
        self.pkle_radio.raise_()
        self.wrewards.raise_()
        self.wrewards_radio.raise_()
        self.hyus.raise_()
        self.hyus_radio.raise_()
        self.watchgamestv.raise_()
        self.watchgamestv_radio.raise_()
        
        self.stop_button.lower()
        self.in_progress.lower()
        
        self.chat_parser_thread.stop()
        self.chat_parser_thread.wait()
        
        self.parser_thread.live_status_changed.connect(self.update_live_icon)
        
    def close_button_act(self):
        self.close()      

    def wrap_button_act(self):
        self.showMinimized()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self.oldPos is not None:
            delta = event.globalPos() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    parserapp = ParserApp()
    parserapp.show()
    sys.exit(app.exec_())
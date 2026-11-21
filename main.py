import os
import sys
import logging
from PyQt6 .QtCore import Qt ,QSettings
from PyQt6 .QtGui import QIcon
from PyQt6 .QtWidgets import (
QApplication ,QMainWindow ,QWidget ,QVBoxLayout ,QLabel ,QTabWidget
)
from image_tab import ImageTab
from video_tab import VideoTab
from about_tab import AboutTab
class WatermarkApp (QMainWindow ):
    def __init__ (self ):
        super ().__init__ ()
        self .settings =QSettings ("Magerko","WatermarkApp")
        self .init_logger ()
        self .init_ui ()
        self .setAcceptDrops (True )
    def init_logger (self ):
        logging .basicConfig (
        level =logging .DEBUG ,
        format ='[%(asctime)s] %(имя уровня)s: %(сообщение)s',
        datefmt ='%H:%M:%S'
        )
        logging .debug ("Логирование инициализировано.")
    def init_ui (self ):
        self .setWindowTitle ("ExMark | Пакетное наложение водяных знаков")
        icon_path =os .path .join ("resources","icon.png")
        if os .path .exists (icon_path ):
            self .setWindowIcon (QIcon (icon_path ))
        self .setGeometry (200 ,150 ,1280 ,800 )
        self .central_widget =QWidget ()
        self .central_widget .setObjectName ("centralWidget")
        self .setCentralWidget (self .central_widget )
        self .tabs =QTabWidget ()
        self .image_tab =ImageTab (self .settings )
        self .video_tab =VideoTab (self .settings )
        self .about_tab =AboutTab ()
        self .tabs .addTab (self .image_tab ,"Изображения")
        self .tabs .addTab (self .video_tab ,"Видео")
        self .tabs .addTab (self .about_tab ,"О программе")
        main_layout =QVBoxLayout (self .central_widget )
        main_layout .addWidget (self .tabs )
        self .footer_label =QLabel ("Разработано Магерко | ХГ: @magerkopython")
        self .footer_label .setAlignment (Qt .AlignmentFlag .AlignCenter )
        self .footer_label .setStyleSheet ("цвет: #95a5a6; размер шрифта: 12 пикселей; маржа сверху: 10 пикселей;")
        main_layout .addWidget (self .footer_label )
        self .central_widget .setLayout (main_layout )
        logging .debug ("UI инициализировано (PyQt6).")
    def dragEnterEvent (self ,event ):
        if event .mimeData ().hasUrls ():
            event .acceptProposedAction ()
            self .central_widget .setProperty ("draggedOver",True )
            self .style ().polish (self .central_widget )
    def dragLeaveEvent (self ,event ):
        self .central_widget .setProperty ("draggedOver",False )
        self .style ().polish (self .central_widget )
    def dropEvent (self ,event ):
        self .central_widget .setProperty ("draggedOver",False )
        self .style ().polish (self .central_widget )
        urls =event .mimeData ().urls ()
        if not urls :
            return
        file_paths =[url .toLocalFile ()for url in urls ]
        images ,videos =self .parse_dropped_paths (file_paths )
        if images :
            self .image_tab .add_files (images )
        if videos :
            self .video_tab .add_files (videos )
        if images and not videos :
            self .tabs .setCurrentWidget (self .image_tab )
        elif videos and not images :
            self .tabs .setCurrentWidget (self .video_tab )
    def parse_dropped_paths (self ,paths ):
        image_ext ={'.png','.jpg','.jpeg','.bmp','.gif'}
        video_ext ={'.mp4','.avi','.mov','.mkv','.webm'}
        found_images =[]
        found_videos =[]
        for p in paths :
            if not os .path .exists (p ):
                logging .warning (f"Путь не существует: {p }")
                continue
            if os .path .isdir (p ):
                for root ,_ ,files in os .walk (p ):
                    for f in files :
                        fp =os .path .join (root ,f )
                        ext =os .path .splitext (fp )[1 ].lower ()
                        if ext in image_ext :
                            found_images .append (fp )
                        elif ext in video_ext :
                            found_videos .append (fp )
            else :
                ext =os .path .splitext (p )[1 ].lower ()
                if ext in image_ext :
                    found_images .append (p )
                elif ext in video_ext :
                    found_videos .append (p )
                else :
                    logging .debug (f"Файл не является изображением или видео: {p }")
        return found_images ,found_videos
def load_stylesheet (app ):
    try :
        with open ("style.qss","r")as f :
            app .setStyleSheet (f .read ())
            logging .debug ("Стили успешно загружены из style.qss")
    except FileNotFoundError :
        logging .warning ("Файл style.qss не найден. Будут использованы стили по умолчанию.")
if __name__ =="__main__":
    app =QApplication (sys .argv )
    load_stylesheet (app )
    window =WatermarkApp ()
    window .show ()
    sys .exit (app .exec ())
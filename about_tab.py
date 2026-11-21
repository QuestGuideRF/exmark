import sys
import logging
from PyQt6 .QtCore import Qt ,QUrl
from PyQt6 .QtGui import QFont ,QDesktopServices
from PyQt6 .QtWidgets import (
QWidget ,QVBoxLayout ,QLabel ,QPushButton ,QTextEdit ,
QFrame ,QHBoxLayout
)
class AboutTab (QWidget ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .init_ui ()
    def init_ui (self ):
        layout =QVBoxLayout ()
        layout .setContentsMargins (15 ,15 ,15 ,15 )
        layout .setSpacing (10 )
        self .setLayout (layout )
        lbl_title =QLabel ("ExMark – О программе")
        lbl_title .setObjectName ("about_title_label")
        lbl_title .setFont (QFont ("Следуйте пользовательскому интерфейсу",20 ,QFont .Weight .Bold ))
        lbl_title .setAlignment (Qt .AlignmentFlag .AlignCenter )
        lbl_version =QLabel ("Версия: 1.0.0")
        lbl_version .setObjectName ("about_version_label")
        lbl_version .setFont (QFont ("Следуйте пользовательскому интерфейсу",14 ))
        lbl_version .setAlignment (Qt .AlignmentFlag .AlignCenter )
        lbl_author =QLabel ("Автор: Magerko | Дизайн: он же")
        lbl_author .setObjectName ("about_author_label")
        lbl_author .setFont (QFont ("Следуйте пользовательскому интерфейсу",14 ))
        lbl_author .setAlignment (Qt .AlignmentFlag .AlignCenter )
        lbl_desc =QLabel (
        "Добро пожаловать в приложение ExMark!\n\n"
        "Эта программа позволяет накладывать водяные знаки на изображения и видео. "
        "Вы можете работать пакетно, настраивать позицию, шрифт, прозрачность и видеть "
        "результат в реальном времени."
        )
        lbl_desc .setObjectName ("about_description_label")
        lbl_desc .setFont (QFont ("Следуйте пользовательскому интерфейсу",14 ))
        lbl_desc .setAlignment (Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop )
        lbl_desc .setWordWrap (True )
        layout .addWidget (lbl_title )
        layout .addWidget (lbl_version )
        layout .addWidget (lbl_author )
        layout .addWidget (lbl_desc )
        line =QFrame (self )
        line .setFrameShape (QFrame .Shape .HLine )
        line .setFrameShadow (QFrame .Shadow .Sunken )
        layout .addWidget (line )
        buttons_layout =QHBoxLayout ()
        contact_label =QLabel ("Контакты:")
        contact_label .setObjectName ("contact_author_label")
        contact_label .setFont (QFont ("Следуйте пользовательскому интерфейсу",14 ))
        buttons_layout .addWidget (contact_label )
        btn_telegram =QPushButton ("Telegram")
        btn_telegram .clicked .connect (lambda :QDesktopServices .openUrl (QUrl ("https://t.me/magerkopython")))
        buttons_layout .addWidget (btn_telegram )
        buttons_layout .addStretch ()
        layout .addLayout (buttons_layout )
        layout .addStretch ()
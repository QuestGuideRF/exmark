import os
import logging
from PyQt6 .QtCore import Qt ,pyqtSignal ,QThread ,pyqtSlot ,QSize
from PyQt6 .QtGui import QPixmap ,QFontDatabase ,QImage ,QIcon
from PyQt6 .QtWidgets import (
QWidget ,QVBoxLayout ,QLabel ,QLineEdit ,QPushButton ,QFileDialog ,QMessageBox ,
QHBoxLayout ,QComboBox ,QSlider ,QProgressBar ,QListWidget ,QListWidgetItem ,QMenu ,
QSpinBox ,QFrame ,QStackedWidget ,QRadioButton ,QGridLayout
)
from PIL import Image
from PIL .ImageQt import ImageQt
from utils import process_image_file ,WatermarkParams ,apply_watermark_to_pillow_image
class ImageProcessingThread (QThread ):
    finished_one =pyqtSignal (str )
    error =pyqtSignal (str )
    def __init__ (self ,image_file ,result_file ,params :WatermarkParams ):
        super ().__init__ ()
        self .image_file ,self .result_file ,self .params =image_file ,result_file ,params
        self ._is_running =True
    def run (self ):
        if not self ._is_running :return
        try :
            process_image_file (self .image_file ,self .result_file ,self .params )
            if self ._is_running :
                self .finished_one .emit (self .result_file )
        except Exception as e :
            if self ._is_running :
                self .error .emit (f"{os .path .basename (self .image_file )}: {e }")
    def stop (self ):
        self ._is_running =False
class ImageTab (QWidget ):
    def __init__ (self ,settings ):
        super ().__init__ ()
        self .settings =settings
        self .image_threads =[]
        self .processed_count =0
        self .current_preview_path =None
        self .current_base_pillow_image =None
        self .init_ui ()
        self .connect_signals ()
    def init_ui (self ):
        main_layout =QHBoxLayout (self )
        left_panel =QWidget ()
        left_layout =QVBoxLayout (left_panel )
        left_panel .setFixedWidth (450 )
        wm_type_layout =QHBoxLayout ()
        self .radio_text_wm =QRadioButton ("Текст");
        self .radio_text_wm .setChecked (True )
        self .radio_image_wm =QRadioButton ("Баннер")
        wm_type_layout .addWidget (QLabel ("Тип водяного знака:"));
        wm_type_layout .addWidget (self .radio_text_wm )
        wm_type_layout .addWidget (self .radio_image_wm );
        wm_type_layout .addStretch ()
        left_layout .addLayout (wm_type_layout )
        self .controls_stack =QStackedWidget ()
        self .init_text_controls ();
        self .init_image_controls ()
        self .controls_stack .addWidget (self .text_controls_widget )
        self .controls_stack .addWidget (self .image_controls_widget )
        left_layout .addWidget (self .controls_stack )
        common_controls_frame =QFrame ()
        common_controls_layout =QGridLayout (common_controls_frame )
        self .combo_position_img =QComboBox ();
        self .combo_position_img .addItems (
        ["Центр","Верхний левый угол","Верхний правый угол","Нижний левый угол","Нижний правый угол"])
        self .spin_offset_x =QSpinBox ();
        self .spin_offset_x .setRange (-2000 ,2000 )
        self .spin_offset_y =QSpinBox ();
        self .spin_offset_y .setRange (-2000 ,2000 )
        opacity_layout =QHBoxLayout ()
        self .slider_opacity_img =QSlider (Qt .Orientation .Horizontal );
        self .slider_opacity_img .setRange (0 ,255 );
        self .slider_opacity_img .setValue (128 )
        opacity_layout .addWidget (QLabel ("Непрозрачность (0-255):"));
        opacity_layout .addWidget (self .slider_opacity_img )
        common_controls_layout .addWidget (QLabel ("Позиция:"),0 ,0 );
        common_controls_layout .addWidget (self .combo_position_img ,0 ,1 ,1 ,3 )
        common_controls_layout .addWidget (QLabel ("Смещение X:"),1 ,0 );
        common_controls_layout .addWidget (self .spin_offset_x ,1 ,1 )
        common_controls_layout .addWidget (QLabel ("Смещение Y:"),1 ,2 );
        common_controls_layout .addWidget (self .spin_offset_y ,1 ,3 )
        common_controls_layout .addLayout (opacity_layout ,2 ,0 ,1 ,4 )
        left_layout .addWidget (common_controls_frame )
        self .image_button_img =QPushButton ("📁 Выбрать изображения")
        left_layout .addWidget (self .image_button_img )
        self .image_list_widget =QListWidget ()
        self .image_list_widget .setViewMode (QListWidget .ViewMode .IconMode )
        self .image_list_widget .setIconSize (QSize (100 ,100 ))
        self .image_list_widget .setResizeMode (QListWidget .ResizeMode .Adjust )
        self .image_list_widget .setMovement (QListWidget .Movement .Static )
        self .image_list_widget .setSpacing (10 )
        self .image_list_widget .setContextMenuPolicy (Qt .ContextMenuPolicy .CustomContextMenu )
        left_layout .addWidget (self .image_list_widget )
        self .progress_bar_img =QProgressBar ();
        self .progress_bar_img .setVisible (False )
        left_layout .addWidget (self .progress_bar_img )
        action_buttons_layout =QHBoxLayout ()
        self .watermark_button_img =QPushButton ("🖋️ Применить ко всем")
        self .cancel_button_img =QPushButton ("❌ Отмена")
        action_buttons_layout .addWidget (self .watermark_button_img );
        action_buttons_layout .addWidget (self .cancel_button_img )
        left_layout .addLayout (action_buttons_layout )
        right_panel =QFrame ();
        right_panel .setFrameShape (QFrame .Shape .StyledPanel )
        right_layout =QVBoxLayout (right_panel )
        self .preview_label =QLabel ();
        self .preview_label .setAlignment (Qt .AlignmentFlag .AlignCenter );
        self .preview_label .setMinimumSize (400 ,400 )
        self .preview_label_placeholder =QLabel ("Перетащите файлы в окно или выберите их,\nчтобы увидеть предпросмотр");
        self .preview_label_placeholder .setAlignment (Qt .AlignmentFlag .AlignCenter )
        self .preview_stack =QStackedWidget ();
        self .preview_stack .addWidget (self .preview_label_placeholder );
        self .preview_stack .addWidget (self .preview_label )
        right_layout .addWidget (self .preview_stack )
        main_layout .addWidget (left_panel );
        main_layout .addWidget (right_panel ,1 )
        self .reset_processing_state ();
        self .load_settings ()
    def init_text_controls (self ):
        self .text_controls_widget =QWidget ();
        layout =QVBoxLayout (self .text_controls_widget );
        layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .label_watermark_img =QLabel ("Текст водяного знака");
        self .label_watermark_img .setStyleSheet ("начертание шрифта: жирный; размер шрифта: 14 пикселей; поле внизу: 3 пикселя;")
        self .input_watermark_img =QLineEdit ();
        self .input_watermark_img .setPlaceholderText ("Ваш текст...")
        grid =QGridLayout ()
        self .combo_font_img =QComboBox ();
        self .populate_fonts ()
        self .spin_font_size_img =QSpinBox ();
        self .spin_font_size_img .setRange (1 ,50 );
        self .spin_font_size_img .setValue (10 )
        grid .addWidget (QLabel ("Шрифт:"),0 ,0 );
        grid .addWidget (self .combo_font_img ,0 ,1 )
        grid .addWidget (QLabel ("Отн. размер (%):"),0 ,2 );
        grid .addWidget (self .spin_font_size_img ,0 ,3 )
        layout .addWidget (self .label_watermark_img );
        layout .addWidget (self .input_watermark_img );
        layout .addLayout (grid )
    def init_image_controls (self ):
        self .image_controls_widget =QWidget ();
        layout =QVBoxLayout (self .image_controls_widget );
        layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .btn_select_banner =QPushButton ("Выбрать изображение баннера")
        self .label_banner_path =QLabel ("Файл не выбран");
        self .label_banner_path .setStyleSheet ("стиль шрифта: курсив;")
        scale_layout =QHBoxLayout ();
        self .spin_banner_scale =QSpinBox ();
        self .spin_banner_scale .setRange (1 ,100 );
        self .spin_banner_scale .setValue (25 )
        scale_layout .addWidget (QLabel ("Масштаб (% от ширины):"));
        scale_layout .addWidget (self .spin_banner_scale )
        layout .addWidget (self .btn_select_banner );
        layout .addWidget (self .label_banner_path );
        layout .addLayout (scale_layout )
        self .banner_path =""
    def populate_fonts (self ):
        self .combo_font_img .addItems (QFontDatabase .families ())
    def connect_signals (self ):
        self .radio_text_wm .toggled .connect (self .trigger_preview_update );
        self .radio_image_wm .toggled .connect (self .trigger_preview_update )
        self .btn_select_banner .clicked .connect (self .select_banner_image );
        self .image_button_img .clicked .connect (self .select_images )
        self .watermark_button_img .clicked .connect (self .apply_watermark_to_all );
        self .cancel_button_img .clicked .connect (self .cancel_image_processing )
        self .input_watermark_img .textChanged .connect (self .trigger_preview_update );
        self .combo_font_img .currentTextChanged .connect (self .trigger_preview_update )
        self .spin_font_size_img .valueChanged .connect (self .trigger_preview_update );
        self .spin_banner_scale .valueChanged .connect (self .trigger_preview_update )
        self .combo_position_img .currentTextChanged .connect (self .trigger_preview_update );
        self .spin_offset_x .valueChanged .connect (self .trigger_preview_update )
        self .spin_offset_y .valueChanged .connect (self .trigger_preview_update );
        self .slider_opacity_img .valueChanged .connect (self .trigger_preview_update )
        self .image_list_widget .itemClicked .connect (self .on_thumbnail_click )
        self .image_list_widget .customContextMenuRequested .connect (self .show_image_context_menu )
    def show_image_context_menu (self ,position ):
        item =self .image_list_widget .itemAt (position )
        if not item :return
        menu =QMenu ();
        delete_action =menu .addAction ("Удалить")
        action =menu .exec (self .image_list_widget .mapToGlobal (position ))
        if action ==delete_action :self .delete_selected_image (item )
    def delete_selected_image (self ,item_to_delete ):
        path_to_delete =item_to_delete .data (Qt .ItemDataRole .UserRole )
        self .image_list_widget .takeItem (self .image_list_widget .row (item_to_delete ))
        if path_to_delete ==self .current_preview_path :
            self .current_preview_path =None ;
            self .current_base_pillow_image =None
            if self .image_list_widget .count ()>0 :
                self .on_thumbnail_click (self .image_list_widget .item (0 ))
            else :
                self .preview_stack .setCurrentWidget (self .preview_label_placeholder )
        self .watermark_button_img .setEnabled (self .image_list_widget .count ()>0 )
    def select_banner_image (self ):
        file ,_ =QFileDialog .getOpenFileName (self ,"Выберите баннер","","Изображения (*.png *.jpg *.jpeg)")
        if file :self .banner_path =file ;self .label_banner_path .setText (
        os .path .basename (file ));self .trigger_preview_update ()
    def get_current_params (self ):
        return WatermarkParams (
        watermark_type ="image"if self .radio_image_wm .isChecked ()else "text",text =self .input_watermark_img .text (),
        position =self .combo_position_img .currentText (),opacity =self .slider_opacity_img .value (),
        font_name =self .combo_font_img .currentText (),
        font_size_relative =self .spin_font_size_img .value (),offset_x =self .spin_offset_x .value (),
        offset_y =self .spin_offset_y .value (),
        image_path =self .banner_path ,image_scale =self .spin_banner_scale .value ()
        )
    def trigger_preview_update (self ,_ =None ):
        if not self .current_base_pillow_image :return
        watermarked_pillow_image =apply_watermark_to_pillow_image (self .current_base_pillow_image ,
        self .get_current_params ())
        q_image =ImageQt (watermarked_pillow_image .convert ('RGBA'))
        self .preview_label .setPixmap (
        QPixmap .fromImage (q_image ).scaled (self .preview_label .size (),Qt .AspectRatioMode .KeepAspectRatio ,
        Qt .TransformationMode .SmoothTransformation ))
    def select_images (self ):
        files ,_ =QFileDialog .getOpenFileNames (self ,"Выберите изображения","",
        "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)")
        if files :self .add_files (files )
    def add_files (self ,file_list ):
        for file_path in file_list :
            if not any (self .image_list_widget .item (i ).data (Qt .ItemDataRole .UserRole )==file_path for i in
            range (self .image_list_widget .count ())):
                item =QListWidgetItem (QIcon (QPixmap (file_path )),os .path .basename (file_path ))
                item .setData (Qt .ItemDataRole .UserRole ,file_path )
                self .image_list_widget .addItem (item )
        if self .image_list_widget .count ()>0 and not self .current_preview_path :
            self .on_thumbnail_click (self .image_list_widget .item (0 ))
        self .watermark_button_img .setEnabled (self .image_list_widget .count ()>0 )
    def on_thumbnail_click (self ,item ):
        path =item .data (Qt .ItemDataRole .UserRole )
        try :
            self .current_preview_path =path ;
            self .current_base_pillow_image =Image .open (path )
            self .preview_stack .setCurrentWidget (self .preview_label );
            self .trigger_preview_update ()
        except Exception as e :
            QMessageBox .warning (self ,"Ошибка",f"Не удалось загрузить изображение: {e }")
            self .current_preview_path =None ;
            self .current_base_pillow_image =None
            self .preview_stack .setCurrentWidget (self .preview_label_placeholder )
    def apply_watermark_to_all (self ):
        if self .image_list_widget .count ()==0 :return
        params =self .get_current_params ()
        if params .watermark_type =="text"and not params .text :QMessageBox .warning (self ,"Ошибка",
        "Введите текст водяного знака.");return
        if params .watermark_type =="image"and not params .image_path :QMessageBox .warning (self ,"Ошибка",
        "Выберите файл изображения для водяного знака.");return
        output_dir =QFileDialog .getExistingDirectory (self ,"Выберите папку для сохранения")
        if not output_dir :return
        self .processed_count =0 ;
        self .progress_bar_img .setMaximum (self .image_list_widget .count ())
        self .reset_processing_state (is_processing =True );
        self .image_threads =[]
        for i in range (self .image_list_widget .count ()):
            image_file =self .image_list_widget .item (i ).data (Qt .ItemDataRole .UserRole )
            base_name ,ext =os .path .splitext (os .path .basename (image_file ))
            result_file =os .path .join (output_dir ,f"watermarked_{base_name }{ext }")
            thread =ImageProcessingThread (image_file ,result_file ,params )
            thread .finished_one .connect (self .on_image_finished );
            thread .error .connect (self .on_image_error )
            self .image_threads .append (thread );
            thread .start ()
    @pyqtSlot (str )
    def on_image_finished (self ,result_file ):
        self .processed_count +=1 ;
        self .progress_bar_img .setValue (self .processed_count )
        if self .processed_count ==len (self .image_threads ):
            QMessageBox .information (self ,"Успех","Все изображения успешно обработаны!")
            self .reset_processing_state ();
            self .save_settings ()
    @pyqtSlot (str )
    def on_image_error (self ,error_message ):
        QMessageBox .warning (self ,"Ошибка обработки",error_message );
        self .processed_count +=1 ;
        self .progress_bar_img .setValue (self .processed_count )
        if self .processed_count ==len (self .image_threads ):
            QMessageBox .information (self ,"Завершено","Обработка завершена с ошибками.");
            self .reset_processing_state ()
    def cancel_image_processing (self ):
        for t in self .image_threads :t .stop ()
        self .reset_processing_state ();
        QMessageBox .information (self ,"Отмена","Обработка была отменена.")
    def reset_processing_state (self ,is_processing =False ):
        self .progress_bar_img .setVisible (is_processing )
        self .watermark_button_img .setEnabled (not is_processing and self .image_list_widget .count ()>0 )
        self .cancel_button_img .setEnabled (is_processing )
        if not is_processing :self .processed_count =0 ;self .image_threads =[]
    def load_settings (self ):
        self .input_watermark_img .setText (self .settings .value ("image_watermark_text",""));
        self .combo_position_img .setCurrentText (self .settings .value ("image_position","Центр"))
        self .slider_opacity_img .setValue (int (self .settings .value ("image_opacity",128 )));
        self .combo_font_img .setCurrentText (self .settings .value ("image_font_name","Arial"))
        self .spin_font_size_img .setValue (int (self .settings .value ("image_font_size_relative",10 )));
        self .spin_offset_x .setValue (int (self .settings .value ("image_offset_x",0 )))
        self .spin_offset_y .setValue (int (self .settings .value ("image_offset_y",0 )));
        self .banner_path =self .settings .value ("image_banner_path","")
        if self .banner_path :self .label_banner_path .setText (os .path .basename (self .banner_path ))
        self .spin_banner_scale .setValue (int (self .settings .value ("image_banner_scale",25 )))
    def save_settings (self ):
        self .settings .setValue ("image_watermark_text",self .input_watermark_img .text ());
        self .settings .setValue ("image_position",self .combo_position_img .currentText ())
        self .settings .setValue ("image_opacity",self .slider_opacity_img .value ());
        self .settings .setValue ("image_font_name",self .combo_font_img .currentText ())
        self .settings .setValue ("image_font_size_relative",self .spin_font_size_img .value ());
        self .settings .setValue ("image_offset_x",self .spin_offset_x .value ())
        self .settings .setValue ("image_offset_y",self .spin_offset_y .value ());
        self .settings .setValue ("image_banner_path",self .banner_path )
        self .settings .setValue ("image_banner_scale",self .spin_banner_scale .value ())
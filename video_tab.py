import os
import logging
import cv2
from PIL import Image
from PIL .ImageQt import ImageQt
from PyQt6 .QtCore import Qt ,QThread ,pyqtSignal ,pyqtSlot ,QUrl ,QTimer
from PyQt6 .QtGui import QIcon ,QFontDatabase ,QImage ,QPixmap
from PyQt6 .QtWidgets import (
QWidget ,QVBoxLayout ,QLabel ,QLineEdit ,QPushButton ,QFileDialog ,QMessageBox ,
QListWidget ,QHBoxLayout ,QComboBox ,QProgressBar ,QSlider ,QSpinBox ,QMenu ,
QFrame ,QGridLayout ,QStyle ,QStackedWidget ,QRadioButton
)
from PyQt6 .QtMultimediaWidgets import QVideoWidget
from PyQt6 .QtMultimedia import QMediaPlayer
from utils import add_watermark_video ,WatermarkParams ,apply_watermark_to_pillow_image
class VideoProcessingThread (QThread ):
    progress =pyqtSignal (float );
    finished_one =pyqtSignal (str );
    error_signal =pyqtSignal (str )
    file_changed =pyqtSignal (str );
    all_finished =pyqtSignal ()
    def __init__ (self ,video_files ,output_dir ,params :WatermarkParams ):
        super ().__init__ ();
        self .video_files ,self .output_dir ,self .params =video_files ,output_dir ,params ;
        self ._is_running =True
    def run (self ):
        try :
            for i ,video_file in enumerate (self .video_files ):
                if not self ._is_running :break
                base_name ,ext =os .path .splitext (os .path .basename (video_file ))
                result_file =os .path .join (self .output_dir ,f"watermarked_{base_name }{ext }")
                self .file_changed .emit (f"({i +1 }/{len (self .video_files )}) {base_name }{ext }")
                add_watermark_video (video_file =video_file ,result_file =result_file ,params =self .params ,
                progress_callback =lambda p :self .progress .emit (p )if self ._is_running else None ,
                check_running_callback =lambda :self ._is_running )
                if self ._is_running :self .finished_one .emit (result_file )
            if self ._is_running :self .all_finished .emit ()
        except Exception as e :
            if "STOPPED"not in str (e ):self .error_signal .emit (str (e ))
    def stop (self ):
        self ._is_running =False
class VideoTab (QWidget ):
    def __init__ (self ,settings ):
        super ().__init__ ();
        self .settings =settings ;
        self .video_thread =None ;
        self .current_video_path =None
        self .media_player =QMediaPlayer ();
        self .init_ui ();
        self .connect_signals ()
        self .media_player .setVideoOutput (self .video_preview_widget );
        self .connect_player_signals ()
    def init_ui (self ):
        main_layout =QHBoxLayout (self );
        left_panel =QWidget ();
        left_layout =QVBoxLayout (left_panel );
        left_panel .setFixedWidth (450 )
        wm_type_layout =QHBoxLayout ()
        self .radio_text_wm =QRadioButton ("Текст");
        self .radio_text_wm .setChecked (True )
        self .radio_image_wm =QRadioButton ("Баннер")
        wm_type_layout .addWidget (QLabel ("Тип водяного знака:"));
        wm_type_layout .addWidget (self .radio_text_wm );
        wm_type_layout .addWidget (self .radio_image_wm );
        wm_type_layout .addStretch ()
        left_layout .addLayout (wm_type_layout )
        self .controls_stack =QStackedWidget ();
        self .init_text_controls ();
        self .init_image_controls ()
        self .controls_stack .addWidget (self .text_controls_widget );
        self .controls_stack .addWidget (self .image_controls_widget )
        left_layout .addWidget (self .controls_stack )
        common_controls_frame =QFrame ();
        common_controls_layout =QGridLayout (common_controls_frame )
        self .combo_position_vid =QComboBox ();
        self .combo_position_vid .addItems (
        ["Центр","Верхний левый угол","Верхний правый угол","Нижний левый угол","Нижний правый угол"])
        self .spin_offset_x =QSpinBox ();
        self .spin_offset_x .setRange (-2000 ,2000 )
        self .spin_offset_y =QSpinBox ();
        self .spin_offset_y .setRange (-2000 ,2000 )
        opacity_layout =QHBoxLayout ()
        self .slider_opacity_vid =QSlider (Qt .Orientation .Horizontal );
        self .slider_opacity_vid .setRange (0 ,100 );
        self .slider_opacity_vid .setValue (50 )
        opacity_layout .addWidget (QLabel ("Непрозрачность (%):"));
        opacity_layout .addWidget (self .slider_opacity_vid )
        common_controls_layout .addWidget (QLabel ("Позиция:"),0 ,0 );
        common_controls_layout .addWidget (self .combo_position_vid ,0 ,1 ,1 ,3 )
        common_controls_layout .addWidget (QLabel ("Смещение X:"),1 ,0 );
        common_controls_layout .addWidget (self .spin_offset_x ,1 ,1 )
        common_controls_layout .addWidget (QLabel ("Смещение Y:"),1 ,2 );
        common_controls_layout .addWidget (self .spin_offset_y ,1 ,3 )
        common_controls_layout .addLayout (opacity_layout ,2 ,0 ,1 ,4 )
        left_layout .addWidget (common_controls_frame )
        self .video_button =QPushButton ("📁 Выбрать видео");
        left_layout .addWidget (self .video_button )
        self .video_list_vid =QListWidget ();
        self .video_list_vid .setContextMenuPolicy (Qt .ContextMenuPolicy .CustomContextMenu )
        left_layout .addWidget (self .video_list_vid )
        self .progress_bar_processing =QProgressBar ();
        self .label_current_file =QLabel ("")
        left_layout .addWidget (self .progress_bar_processing );
        left_layout .addWidget (self .label_current_file )
        action_buttons_layout =QHBoxLayout ()
        self .watermark_button_vid =QPushButton ("🖋️ Применить ко всем");
        self .cancel_button_vid =QPushButton ("❌ Отмена")
        action_buttons_layout .addWidget (self .watermark_button_vid );
        action_buttons_layout .addWidget (self .cancel_button_vid )
        left_layout .addLayout (action_buttons_layout )
        right_panel =QFrame ();
        right_layout =QVBoxLayout (right_panel )
        self .preview_stack =QStackedWidget ()
        self .video_preview_widget =QVideoWidget ()
        self .video_still_label =QLabel ();
        self .video_still_label .setAlignment (Qt .AlignmentFlag .AlignCenter );
        self .video_still_label .setStyleSheet ("цвет фона: черный;")
        self .preview_stack .addWidget (self .video_preview_widget );
        self .preview_stack .addWidget (self .video_still_label )
        right_layout .addWidget (self .preview_stack ,1 )
        time_layout =QHBoxLayout ()
        self .current_time_label =QLabel ("00:00");
        self .progress_bar_playback =QSlider (Qt .Orientation .Horizontal );
        self .total_time_label =QLabel ("00:00")
        time_layout .addWidget (self .current_time_label );
        time_layout .addWidget (self .progress_bar_playback );
        time_layout .addWidget (self .total_time_label )
        right_layout .addLayout (time_layout )
        player_controls_layout =QHBoxLayout ()
        self .play_pause_button =QPushButton ();
        self .stop_button =QPushButton ()
        player_controls_layout .addStretch ();
        player_controls_layout .addWidget (self .play_pause_button );
        player_controls_layout .addWidget (self .stop_button );
        player_controls_layout .addStretch ()
        right_layout .addLayout (player_controls_layout )
        main_layout .addWidget (left_panel );
        main_layout .addWidget (right_panel ,1 )
        self .reset_processing_state (is_processing =False );
        self .reset_player_state ();
        self .load_settings ()
    def init_text_controls (self ):
        self .text_controls_widget =QWidget ();
        layout =QVBoxLayout (self .text_controls_widget );
        layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .label_watermark_vid =QLabel ("Текст водяного знака");
        self .label_watermark_vid .setStyleSheet ("начертание шрифта: жирный; размер шрифта: 14 пикселей; поле внизу: 3 пикселя;")
        self .input_watermark_vid =QLineEdit ();
        self .input_watermark_vid .setPlaceholderText ("Ваш текст...")
        grid =QGridLayout ();
        self .combo_font_vid =QComboBox ();
        self .combo_font_vid .addItems (QFontDatabase .families ())
        self .spin_font_size_vid =QSpinBox ();
        self .spin_font_size_vid .setRange (1 ,50 );
        self .spin_font_size_vid .setValue (8 )
        grid .addWidget (QLabel ("Шрифт:"),0 ,0 );
        grid .addWidget (self .combo_font_vid ,0 ,1 )
        grid .addWidget (QLabel ("Отн. размер (%):"),0 ,2 );
        grid .addWidget (self .spin_font_size_vid ,0 ,3 )
        layout .addWidget (self .label_watermark_vid );
        layout .addWidget (self .input_watermark_vid );
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
    def connect_signals (self ):
        self .radio_text_wm .toggled .connect (self .trigger_preview_update );
        self .radio_image_wm .toggled .connect (self .trigger_preview_update )
        self .btn_select_banner .clicked .connect (self .select_banner_image );
        self .video_button .clicked .connect (self .select_video )
        self .video_list_vid .itemDoubleClicked .connect (self .play_selected_video );
        self .video_list_vid .customContextMenuRequested .connect (self .show_video_context_menu )
        self .watermark_button_vid .clicked .connect (self .apply_watermark_vid );
        self .cancel_button_vid .clicked .connect (self .cancel_video_processing )
        self .input_watermark_vid .textChanged .connect (self .trigger_preview_update );
        self .combo_font_vid .currentTextChanged .connect (self .trigger_preview_update )
        self .spin_font_size_vid .valueChanged .connect (self .trigger_preview_update );
        self .spin_banner_scale .valueChanged .connect (self .trigger_preview_update )
        self .combo_position_vid .currentTextChanged .connect (self .trigger_preview_update );
        self .spin_offset_x .valueChanged .connect (self .trigger_preview_update )
        self .spin_offset_y .valueChanged .connect (self .trigger_preview_update );
        self .slider_opacity_vid .valueChanged .connect (self .trigger_preview_update )
    def connect_player_signals (self ):
        self .play_pause_button .clicked .connect (self .toggle_play_pause );
        self .stop_button .clicked .connect (self .stop_playback )
        self .progress_bar_playback .sliderReleased .connect (self .trigger_preview_update );
        self .progress_bar_playback .sliderMoved .connect (self .seek_video )
        self .media_player .positionChanged .connect (self .position_changed );
        self .media_player .durationChanged .connect (self .duration_changed )
        self .media_player .playbackStateChanged .connect (self .media_state_changed )
    def show_video_context_menu (self ,position ):
        item =self .video_list_vid .itemAt (position )
        if not item :return
        menu =QMenu ();
        delete_action =menu .addAction ("Удалить")
        action =menu .exec (self .video_list_vid .mapToGlobal (position ))
        if action ==delete_action :self .delete_selected_video ()
    def delete_selected_video (self ):
        current_item =self .video_list_vid .currentItem ()
        if not current_item :return
        row =self .video_list_vid .row (current_item )
        self .video_list_vid .takeItem (row )
        path_to_delete =self .current_video_path
        if 0 <=row <len (self .video_list_vid .findItems ("",Qt .MatchFlag .MatchContains )):
            path_to_delete =self .video_list_vid .item (row ).text ()if self .video_list_vid .item (row )else ""
        if self .current_video_path and os .path .basename (self .current_video_path )==current_item .text ():
            self .media_player .stop ();
            self .reset_player_state ()
            if self .video_list_vid .count ()>0 :self .play_selected_video (self .video_list_vid .item (0 ))
        self .watermark_button_vid .setEnabled (self .video_list_vid .count ()>0 )
    def select_banner_image (self ):
        file ,_ =QFileDialog .getOpenFileName (self ,"Выберите баннер","","Изображения (*.png *.jpg *.jpeg)")
        if file :self .banner_path =file ;self .label_banner_path .setText (
        os .path .basename (file ));self .trigger_preview_update ()
    def get_current_params (self ):
        return WatermarkParams (
        watermark_type ="image"if self .radio_image_wm .isChecked ()else "text",text =self .input_watermark_vid .text (),
        position =self .combo_position_vid .currentText (),
        opacity =self .slider_opacity_vid .value ()/100.0 ,font_name =self .combo_font_vid .currentText (),
        font_size_relative =self .spin_font_size_vid .value (),
        offset_x =self .spin_offset_x .value (),offset_y =self .spin_offset_y .value (),image_path =self .banner_path ,
        image_scale =self .spin_banner_scale .value ()
        )
    def trigger_preview_update (self ):
        if self .media_player .playbackState ()!=QMediaPlayer .PlaybackState .PlayingState :QTimer .singleShot (50 ,
        self .update_video_preview_frame )
    def update_video_preview_frame (self ):
        if not self .current_video_path :return
        try :
            cap =cv2 .VideoCapture (self .current_video_path )
            if not cap .isOpened ():return
            cap .set (cv2 .CAP_PROP_POS_MSEC ,self .media_player .position ())
            ret ,frame =cap .read ()
            cap .release ()
            if ret :
                pillow_frame =Image .fromarray (cv2 .cvtColor (frame ,cv2 .COLOR_BGR2RGB ))
                watermarked_frame =apply_watermark_to_pillow_image (pillow_frame ,self .get_current_params ())
                q_image =ImageQt (watermarked_frame .convert ('RGBA'))
                self .video_still_label .setPixmap (
                QPixmap .fromImage (q_image ).scaled (self .video_still_label .size (),Qt .AspectRatioMode .KeepAspectRatio ,
                Qt .TransformationMode .SmoothTransformation ))
        except Exception as e :
            logging .error (f"Failed to update video preview frame: {e }",exc_info =True )
    def select_video (self ):
        files ,_ =QFileDialog .getOpenFileNames (self ,"Выберите видео","","Видео (*.mp4 *.avi *.mov *.mkv *.webm)")
        if files :self .add_files (files )
    def add_files (self ,file_list ):
        current_files =[self .video_list_vid .item (i ).text ()for i in range (self .video_list_vid .count ())]
        for file_path in file_list :
            if os .path .basename (file_path )not in current_files :
                item =QListWidgetItem (os .path .basename (file_path ))
                item .setData (Qt .ItemDataRole .UserRole ,file_path )
                self .video_list_vid .addItem (item )
        if self .video_list_vid .count ()>0 and not self .current_video_path :self .play_selected_video (
        self .video_list_vid .item (0 ))
        self .watermark_button_vid .setEnabled (self .video_list_vid .count ()>0 )
    def play_selected_video (self ,item ):
        self .current_video_path =item .data (Qt .ItemDataRole .UserRole )
        self .media_player .setSource (QUrl .fromLocalFile (self .current_video_path ))
        self .media_player .play ()
        self .reset_player_state (enabled =True )
    def apply_watermark_vid (self ):
        if self .video_list_vid .count ()==0 :return
        params =self .get_current_params ()
        if params .watermark_type =="text"and not params .text :QMessageBox .warning (self ,"Ошибка",
        "Введите текст водяного знака.");return
        if params .watermark_type =="image"and not params .image_path :QMessageBox .warning (self ,"Ошибка",
        "Выберите файл изображения для водяного знака.");return
        output_dir =QFileDialog .getExistingDirectory (self ,"Выберите папку для сохранения")
        if not output_dir :return
        video_files =[self .video_list_vid .item (i ).data (Qt .ItemDataRole .UserRole )for i in
        range (self .video_list_vid .count ())]
        self .video_thread =VideoProcessingThread (video_files ,output_dir ,params )
        self .video_thread .progress .connect (self .on_video_progress );
        self .video_thread .finished_one .connect (lambda res :logging .info (f"Video saved: {res }"))
        self .video_thread .error_signal .connect (self .on_video_error );
        self .video_thread .file_changed .connect (self .on_file_changed )
        self .video_thread .all_finished .connect (self .on_all_finished )
        self .reset_processing_state (is_processing =True );
        self .video_thread .start ()
    def cancel_video_processing (self ):
        if self .video_thread :self .video_thread .stop ()
        self .reset_processing_state (is_processing =False );
        QMessageBox .information (self ,"Отмена","Обработка была отменена.")
    def on_video_progress (self ,p ):
        self .progress_bar_processing .setValue (int (p ))
    def on_file_changed (self ,filename ):
        self .label_current_file .setText (f"Обработка: {filename }")
    def on_all_finished (self ):
        QMessageBox .information (self ,"Успех","Все видео успешно обработаны!");
        self .reset_processing_state (is_processing =False );
        self .save_settings ()
    def on_video_error (self ,msg ):
        QMessageBox .critical (self ,"Ошибка",f"Не удалось обработать видео: {msg }");
        self .reset_processing_state (is_processing =False )
    def reset_processing_state (self ,is_processing ):
        self .progress_bar_processing .setVisible (is_processing );
        self .label_current_file .setVisible (is_processing )
        self .watermark_button_vid .setEnabled (not is_processing and self .video_list_vid .count ()>0 )
        self .cancel_button_vid .setEnabled (is_processing )
        if not is_processing :self .progress_bar_processing .setValue (0 );self .label_current_file .setText ("")
    def reset_player_state (self ,enabled =False ):
        self .play_pause_button .setEnabled (enabled );
        self .stop_button .setEnabled (enabled );
        self .progress_bar_playback .setEnabled (enabled )
        self .play_pause_button .setIcon (self .style ().standardIcon (QStyle .StandardPixmap .SP_MediaPlay ));
        self .stop_button .setIcon (self .style ().standardIcon (QStyle .StandardPixmap .SP_MediaStop ))
        self .progress_bar_playback .setValue (0 );
        self .current_time_label .setText ("00:00");
        self .total_time_label .setText ("00:00")
        if not enabled :self .media_player .setSource (
        QUrl ());self .current_video_path =None ;self .preview_stack .setCurrentWidget (self .video_preview_widget )
    def toggle_play_pause (self ):
        if self .media_player .playbackState ()==QMediaPlayer .PlaybackState .PlayingState :
            self .media_player .pause ()
        else :
            self .media_player .play ()
    def stop_playback (self ):
        self .media_player .stop ()
    def seek_video (self ,position ):
        self .media_player .setPosition (position )
    def position_changed (self ,pos ):
        if not self .progress_bar_playback .isSliderDown ():self .progress_bar_playback .setValue (pos )
        self .current_time_label .setText (f"{pos //60000 :02}:{pos //1000 %60 :02}")
    def duration_changed (self ,dur ):
        self .progress_bar_playback .setRange (0 ,dur );
        self .total_time_label .setText (f"{dur //60000 :02}:{dur //1000 %60 :02}")
    def media_state_changed (self ,state ):
        icon =self .style ().standardIcon (QStyle .StandardPixmap .SP_MediaPlay )
        if state ==QMediaPlayer .PlaybackState .PlayingState :
            icon =self .style ().standardIcon (QStyle .StandardPixmap .SP_MediaPause )
            self .preview_stack .setCurrentWidget (self .video_preview_widget )
        else :
            self .trigger_preview_update ();
            self .preview_stack .setCurrentWidget (self .video_still_label )
        self .play_pause_button .setIcon (icon )
    def load_settings (self ):
        self .input_watermark_vid .setText (self .settings .value ("video_watermark_text",""));
        self .combo_position_vid .setCurrentText (self .settings .value ("video_position","Центр"))
        self .slider_opacity_vid .setValue (int (self .settings .value ("video_opacity",50 )));
        self .combo_font_vid .setCurrentText (self .settings .value ("video_font_name","Arial"))
        self .spin_font_size_vid .setValue (int (self .settings .value ("video_font_size_relative",8 )));
        self .spin_offset_x .setValue (int (self .settings .value ("video_offset_x",0 )))
        self .spin_offset_y .setValue (int (self .settings .value ("video_offset_y",0 )));
        self .banner_path =self .settings .value ("video_banner_path","")
        if self .banner_path :self .label_banner_path .setText (os .path .basename (self .banner_path ))
        self .spin_banner_scale .setValue (int (self .settings .value ("video_banner_scale",25 )))
    def save_settings (self ):
        self .settings .setValue ("video_watermark_text",self .input_watermark_vid .text ());
        self .settings .setValue ("video_position",self .combo_position_vid .currentText ())
        self .settings .setValue ("video_opacity",self .slider_opacity_vid .value ());
        self .settings .setValue ("video_font_name",self .combo_font_vid .currentText ())
        self .settings .setValue ("video_font_size_relative",self .spin_font_size_vid .value ());
        self .settings .setValue ("video_offset_x",self .spin_offset_x .value ())
        self .settings .setValue ("video_offset_y",self .spin_offset_y .value ());
        self .settings .setValue ("video_banner_path",self .banner_path )
        self .settings .setValue ("video_banner_scale",self .spin_banner_scale .value ())
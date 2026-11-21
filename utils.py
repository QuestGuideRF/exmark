import shutil
import os
import logging
from collections import namedtuple
import platform
if platform .system ()=="Windows":
    import winreg
import numpy as np
from PIL import Image ,ImageDraw ,ImageFont
import moviepy .editor as mpy
import moviepy .config as mpy_config
from proglog import ProgressBarLogger
WatermarkParams =namedtuple (
"WatermarkParams",
[
"watermark_type","text","font_name","font_size_relative","position",
"opacity","offset_x","offset_y",
"image_path","image_scale"
]
)
logging .basicConfig (level =logging .DEBUG ,format ='%(asctime)s - %(имя уровня)s - %(сообщение)s')
def find_font_file_on_windows (font_name :str )->str |None :
    if platform .system ()!="Windows":
        return None
    try :
        with winreg .OpenKey (winreg .HKEY_LOCAL_MACHINE ,r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")as key :
            for i in range (winreg .QueryInfoKey (key )[1 ]):
                value_name ,file_name ,_ =winreg .EnumValue (key ,i )
                if font_name .lower ()in value_name .lower ():
                    fonts_folder =os .path .join (os .environ ["SystemRoot"],"Fonts")
                    font_path =os .path .join (fonts_folder ,file_name )
                    if os .path .exists (font_path ):
                        logging .debug (f"Found font '{font_name }' at '{font_path }' via registry.")
                        return font_path
    except Exception as e :
        logging .error (f"Error accessing registry for fonts: {e }")
    return None
def _get_font (font_name :str ,font_size :int )->ImageFont .FreeTypeFont :
    font_path =None
    if platform .system ()=="Windows":
        font_path =find_font_file_on_windows (font_name )
    if font_path :
        try :
            return ImageFont .truetype (font_path ,font_size )
        except IOError :
            logging .warning (f"Found font file {font_path } but failed to load. Falling back.")
    try :
        return ImageFont .truetype (f"{font_name }.ttf",font_size )
    except IOError :
        pass
    logging .warning (f"Could not find a file for '{font_name }'. Falling back to Arial.")
    try :
        return ImageFont .truetype ("arial.ttf",font_size )
    except IOError :
        logging .error ("ВАЖНО: резервный шрифт Arial также не найден. Использование крошечного шрифта по умолчанию.")
        return ImageFont .load_default ()
def get_watermark_position (img_w ,img_h ,wm_w ,wm_h ,position ,offset_x ,offset_y ):
    margin =10
    positions ={
    "Центр":((img_w -wm_w )/2 ,(img_h -wm_h )/2 ),
    "Верхний левый угол":(margin ,margin ),
    "Верхний правый угол":(img_w -wm_w -margin ,margin ),
    "Нижний левый угол":(margin ,img_h -wm_h -margin ),
    "Нижний правый угол":(img_w -wm_w -margin ,img_h -wm_h -margin )
    }
    x ,y =positions .get (position ,((img_w -wm_w )/2 ,(img_h -wm_h )/2 ))
    return int (x +offset_x ),int (y +offset_y )
def apply_watermark_to_pillow_image (base_image :Image .Image ,params :WatermarkParams )->Image .Image :
    if base_image .mode !='RGBA':
        base_image =base_image .convert ('RGBA')
    if params .watermark_type =="text"and params .text :
        txt_layer =Image .new ("RGBA",base_image .size ,(255 ,255 ,255 ,0 ))
        draw =ImageDraw .Draw (txt_layer )
        font_size_px =int (base_image .height *(params .font_size_relative /100.0 ))
        font =_get_font (params .font_name ,font_size_px )
        text_bbox =draw .textbbox ((0 ,0 ),params .text ,font =font )
        text_w ,text_h =text_bbox [2 ]-text_bbox [0 ],text_bbox [3 ]-text_bbox [1 ]
        x ,y =get_watermark_position (base_image .width ,base_image .height ,text_w ,text_h ,params .position ,
        params .offset_x ,params .offset_y )
        opacity_int =int (params .opacity if isinstance (params .opacity ,int )else params .opacity *255 )
        fill_color =(255 ,255 ,255 ,opacity_int )
        draw .text ((x ,y ),params .text ,font =font ,fill =fill_color )
        return Image .alpha_composite (base_image ,txt_layer )
    elif params .watermark_type =="image"and params .image_path and os .path .exists (params .image_path ):
        watermark =Image .open (params .image_path ).convert ("RGBA")
        scale =params .image_scale /100.0
        wm_w =int (base_image .width *scale )
        wm_h =int (watermark .height *(wm_w /watermark .width ))if watermark .width >0 else 0
        watermark =watermark .resize ((wm_w ,wm_h ),Image .Resampling .LANCZOS )
        opacity_int =int (params .opacity if isinstance (params .opacity ,int )else params .opacity *255 )
        if opacity_int <255 :
            alpha =watermark .split ()[3 ]
            alpha =alpha .point (lambda p :p *(opacity_int /255.0 ))
            watermark .putalpha (alpha )
        x ,y =get_watermark_position (base_image .width ,base_image .height ,wm_w ,wm_h ,params .position ,params .offset_x ,
        params .offset_y )
        img_layer =Image .new ("RGBA",base_image .size ,(255 ,255 ,255 ,0 ))
        img_layer .paste (watermark ,(x ,y ),watermark )
        return Image .alpha_composite (base_image ,img_layer )
    return base_image
def process_image_file (image_path :str ,result_path :str ,params :WatermarkParams ):
    try :
        base_image =Image .open (image_path )
        watermarked_image =apply_watermark_to_pillow_image (base_image ,params )
        watermarked_image .convert ("RGB").save (result_path ,
        "JPEG"if result_path .lower ().endswith ((".jpg",".jpeg"))else "PNG")
        logging .info (f"Watermark added to image: {result_path }")
    except Exception as e :
        logging .error (f"Error processing image file {image_path }: {e }",exc_info =True )
        raise e
class CustomProgressLogger (ProgressBarLogger ):
    def __init__ (self ,progress_callback ,check_running_callback ):
        super ().__init__ ();
        self .progress_callback =progress_callback ;
        self .check_running_callback =check_running_callback
    def callback (self ,**changes ):
        pass
    def bars_callback (self ,bar ,attr ,value ,old_value =None ):
        if not self .check_running_callback ():raise IOError ("ОСТАНОВЛЕНО пользователем")
        if bar =='t'and self .bars [bar ]['total']>0 :
            percentage =(value /self .bars [bar ]['total'])*100
            if self .progress_callback :self .progress_callback (percentage )
def apply_watermark_to_frame (frame ,params :WatermarkParams ):
    img =Image .fromarray (frame )
    watermarked_img =apply_watermark_to_pillow_image (img ,params )
    return np .array (watermarked_img .convert ("RGB"))
def add_watermark_video (video_file :str ,result_file :str ,params :WatermarkParams ,progress_callback =None ,
check_running_callback =lambda :True ):
    clip =None
    try :
        clip =mpy .VideoFileClip (video_file )
        watermarked_clip =clip .fl_image (lambda frame :apply_watermark_to_frame (frame ,params ))
        logger =CustomProgressLogger (progress_callback ,check_running_callback )
        watermarked_clip .write_videofile (result_file ,codec ='libx264',audio_codec ='aac',logger =logger ,threads =4 )
        logging .info (f"Watermark added to video: {result_file }")
    except Exception as e :
        logging .error (f"Error adding watermark to video {video_file }: {e }",exc_info =True )
        raise e
    finally :
        if clip :clip .close ()
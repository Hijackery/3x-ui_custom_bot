import qrcode
import io
import uuid
from datetime import datetime
from config import settings
from xui import XUIHelper

def generate_qr(config_text: str) -> io.BytesIO:
    """Генерирует QR-код из конфига"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(config_text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        byte_io = io.BytesIO()
        img.save(byte_io, 'PNG')
        byte_io.seek(0)
        return byte_io
    except Exception as e:
        raise Exception(f"Ошибка генерации QR: {str(e)}")

def generate_config(user_id: int, config_name: str = None) -> tuple:
    """Генерирует конфиг и добавляет его в X-UI"""
    try:
        xui = XUIHelper()
        config_uuid = str(uuid.uuid4())
        remark = config_name or f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        inbound_id = xui.add_inbound(config_uuid, remark)
        if not inbound_id:
            raise Exception("X-UI не вернул ID нового конфига")
        
        config_text = (
            f"vless://{config_uuid}@{settings.REALITY_CONFIG['address']}:{settings.REALITY_CONFIG['port']}?"
            f"type={settings.REALITY_CONFIG['type']}&security=reality&"
            f"pbk={settings.REALITY_CONFIG['pbk']}&fp={settings.REALITY_CONFIG['fp']}&"
            f"sni={settings.REALITY_CONFIG['sni']}&sid={settings.REALITY_CONFIG['sid']}&"
            f"spx={settings.REALITY_CONFIG['spx']}&flow={settings.REALITY_CONFIG['flow']}#{remark}"
        )
        
        return config_text, config_uuid, inbound_id
        
    except Exception as e:
        raise Exception(f"Ошибка генерации конфига: {str(e)}")

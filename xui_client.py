import httpx
import random
import json
from uuid import uuid4
from config import Config
import logging
import qrcode
import io

logger = logging.getLogger(__name__)

class XUIError(Exception):
    """Ошибки API 3X-UI"""
    pass

class XUIClient:
    def __init__(self):
        self.base_url = Config.XUI_URL.rstrip('/')
        self.session = httpx.AsyncClient(
            verify=False,
            timeout=30.0,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        
    async def _login(self) -> None:
        try:
            login_url = f"{self.base_url}/login"
            logger.info(f"Attempting login to: {login_url}")
            
            response = await self.session.post(
                login_url,
                data={
                    "username": Config.XUI_LOGIN,
                    "password": Config.XUI_PASSWORD
                },
                follow_redirects=True
            )
            
            if response.status_code != 200:
                logger.error(f"Login failed. Status: {response.status_code}, Response: {response.text[:200]}")
                raise XUIError("Ошибка аутентификации в 3X-UI")
                
        except Exception as e:
            logger.error(f"Connection error during login: {str(e)}")
            raise XUIError(f"Ошибка подключения: {str(e)}")

    async def create_inbound(self, port: int) -> dict:
        """Создание нового Reality inbound"""
        try:
            await self._login()
            
            email = f"user{random.randint(1000, 9999)}@{Config.DOMAIN}"
            uuid_str = str(uuid4())
            
            data = {
                "up": 0,
                "down": 0,
                "total": 0,
                "remark": f"VPN-{email[:10]}",
                "enable": True,
                "expiryTime": 0,
                "listen": "",
                "port": port,
                "protocol": "vless",
                "settings": json.dumps({
                    "clients": [{
                        "id": uuid_str,
                        "flow": Config.DEFAULT_FLOW,
                        "email": email,
                        "limitIp": 0,
                        "totalGB": 0
                    }],
                    "decryption": "none"
                }),
                "streamSettings": json.dumps({
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "show": False,
                        "dest": f"{random.choice(Config.SERVER_NAMES)}:443",
                        "serverNames": Config.SERVER_NAMES,
                        "privateKey": Config.PRIVATE_KEY,
                        "shortIds": [Config.SHORT_ID]
                    }
                })
            }
            
            api_url = f"{self.base_url}/panel/api/inbounds/add"
            logger.info(f"Creating inbound at: {api_url}")
            
            response = await self.session.post(
                api_url,
                data=data,
                follow_redirects=True
            )
            
            logger.debug(f"API Response: Status={response.status_code}, Text={response.text[:200]}")
            
            if response.status_code != 200:
                error_msg = f"Ошибка API ({response.status_code}): {response.text[:200]}"
                logger.error(error_msg)
                raise XUIError(error_msg)
                
            try:
                response_data = response.json()
                if not response_data.get("success", False):
                    error_msg = response_data.get("msg", "Unknown error from X-UI")
                    raise XUIError(f"API Error: {error_msg}")
                
                inbound_id = response_data.get("obj", {}).get("id")
                if not inbound_id:
                    raise XUIError("Не удалось получить ID созданного inbound")
                    
                config_data = self._generate_config(uuid_str, port, email)
                qr_code = self._generate_qr_code(config_data)
                    
                return {
                    "inbound_id": inbound_id,
                    "uuid": uuid_str,
                    "port": port,
                    "email": email,
                    "flow": Config.DEFAULT_FLOW,
                    "data": config_data,
                    "qr_code": qr_code
                }
                
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Invalid response format: {response.text[:200]}")
                raise XUIError("Неверный формат ответа от сервера X-UI")
            
        except Exception as e:
            logger.error(f"Error in create_inbound: {str(e)}", exc_info=True)
            raise XUIError(f"Ошибка создания inbound: {str(e)}")

    def _generate_config(self, uuid: str, port: int, email: str) -> str:
        """Генерация конфига VLESS Reality"""
        return (
            f"vless://{uuid}@{Config.SERVER_IP}:{port}?"
            f"type=tcp&security=reality&"
            f"pbk={Config.PUBLIC_KEY}&"
            f"sni={random.choice(Config.SERVER_NAMES)}&"
            f"sid={Config.SHORT_ID}&"
            f"flow={Config.DEFAULT_FLOW}#{email}"
        )

    def _generate_qr_code(self, config_text: str) -> io.BytesIO:
        """Генерация QR-кода из конфига"""
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
            logger.error(f"Ошибка генерации QR-кода: {str(e)}")
            raise XUIError(f"Ошибка генерации QR-кода: {str(e)}")

    async def delete_inbound(self, inbound_id: int) -> bool:
        """Удаление inbound"""
        try:
            await self._login()
            response = await self.session.post(
                f"{self.base_url}/panel/api/inbounds/del/{inbound_id}",
                follow_redirects=True
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting inbound: {str(e)}")
            raise XUIError(f"Ошибка удаления inbound: {str(e)}")

    async def close(self):
        """Закрытие сессии"""
        await self.session.aclose()
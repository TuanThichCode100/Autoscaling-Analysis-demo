import requests
import logging

logger = logging.getLogger("LocustService")

LOCUST_API_URL = "http://locust:8089/swarm"

class LocustService:
    @staticmethod
    def start_storm(user_count=2000, spawn_rate=200):
        """
        Kích hoạt Storm: Gửi lệnh POST đến Locust để start load test
        với số lượng user cực lớn.
        """
        try:
            payload = {
                "user_count": user_count,
                "spawn_rate": spawn_rate,
                "host": "http://api:8000" 
            }
            response = requests.post(LOCUST_API_URL, data=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"⚡ STORM STARTED! Users={user_count}, Rate={spawn_rate}")
                return True
            else:
                logger.error(f"❌ Failed to start storm: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Locust connection error: {e}")
            return False

    @staticmethod
    def stop_storm(user_count=50, spawn_rate=5):
        """
        Dừng Storm: Đưa Locust về trạng thái tải bình thường (50 users)
        """
        try:
            # Locust API logic: Sending a new POST overwrites the current swarm
            # So to "stop" storm and go back to normal, we just start a smaller swarm.
            # Alternatively, we could call /stop to stop completely, but user likely wants background load.
            payload = {
                "user_count": user_count,
                "spawn_rate": spawn_rate,
                "host": "http://api:8000"
            }
            response = requests.post(LOCUST_API_URL, data=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info("cloudy 🌥️ Storm stopped. Returning to normal load.")
                return True
            else:
                logger.error(f"❌ Failed to stop storm: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Locust connection error: {e}")
            return False

locust_service = LocustService()

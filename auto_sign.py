import requests
import json
from datetime import datetime
import logging
import os
from PIL import Image
import base64

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_sign.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoSign:
    def __init__(self, login_info):
        self.base_url = "http://sxsx.jxeduyun.com:7779"
        # 使用传入的登录信息
        self.login_info = {
            "loginAccount": login_info["loginAccount"],
            "password": login_info["password"],
            "rememberMe": True,
            "loginUserType": "student",
            "enrollmentYear": login_info["enrollmentYear"]
        }
        # 先登录获取token
        self.headers = self.get_headers()
        # 获取用户信息
        self.user_info = self.get_user_info()
        if not self.user_info:
            raise Exception("获取用户信息失败")
        logger.info(f"成功获取用户信息: {self.user_info}")

    def login(self):
        """登录获取token"""
        url = f"{self.base_url}/portal-api/login"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Request-Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            logger.info("开始登录...")
            response = requests.post(
                url, 
                headers=headers,
                json=self.login_info
            )
            
            logger.info(f"登录响应状态码: {response.status_code}")
            logger.info(f"登录响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    token = result.get("token")
                    logger.info("登录成功！")
                    return token
                else:
                    logger.error(f"登录失败: {result.get('msg')}")
                    return None
        except Exception as e:
            logger.error(f"登录异常: {str(e)}")
            return None

    def get_headers(self):
        """获取请求头"""
        token = self.login()
        if not token:
            raise Exception("登录失败，无法获取token")
            
        return {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 2407FRK8EC Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.6478.71 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/36.307693)",
            "Global-Year-Head": "2025",
            "Content-Type": "application/json;charset=utf-8"
        }

    def get_user_info(self):
        """获取用户信息"""
        url = f"{self.base_url}/portal-api/app/index/getStudentPlan"
        
        try:
            logger.info("开始获取用户信息...")
            response = requests.get(url, headers=self.headers)
            
            # 打印完整的响应内容
            logger.info(f"API响应状态码: {response.status_code}")
            logger.info(f"API完整响应: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    autonomy_plan = result.get("data", {}).get("autonomyPlan", {})
                    user_info = {
                        "autonomyId": autonomy_plan.get("id"),
                        "userId": autonomy_plan.get("userId"),
                        "nickName": autonomy_plan.get("nickName"),
                        "clockAddress": autonomy_plan.get("practicePlace")
                    }
                    logger.info(f"用户信息获取成功: {user_info}")
                    return user_info
                else:
                    logger.error(f"获取用户信息失败: {result.get('msg')}")
                    return None
        except Exception as e:
            logger.error(f"获取用户信息异常: {str(e)}")
            return None

    def upload_image(self, image_path):
        """上传图片获取fileId"""
        url = f"{self.base_url}/portal-api/common/uploadFileUrl"
        
        # 修改请求头，移除 Content-Type，让 requests 自动处理
        headers = {
            'Authorization': self.headers['Authorization'],
            'User-Agent': 'Mozilla/5.0 (Linux; Android 14; 2407FRK8EC Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.6478.71 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/36.307693)',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'com.ecom.renrentong'
        }
        
        try:
            logger.info("开始上传图片...")
            # 准备文件数据
            with open(image_path, 'rb') as f:
                # 使用原始文件名
                filename = os.path.basename(image_path)
                files = {
                    'file': (
                        filename,  # 使用原始文件名
                        f,
                        'image/jpeg'
                    )
                }
                
                response = requests.post(
                    url, 
                    headers=headers,
                    files=files
                )
            
            logger.info(f"图片上传响应状态码: {response.status_code}")
            logger.info(f"图片上传响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    # 服务器返回的文件信息
                    file_id = result.get("id")
                    file_name = result.get("fileName")
                    file_url = result.get("url")
                    logger.info(f"图片上传成功，fileId: {file_id}, fileName: {file_name}, url: {file_url}")
                    return file_id
                else:
                    logger.error(f"图片上传失败: {result.get('msg')}")
                    return None
        except Exception as e:
            logger.error(f"图片上传异常: {str(e)}")
            return None

    def sign_in(self, file_id):
        """执行签到"""
        url = f"{self.base_url}/portal-api/practice/autonomyClock/add"
        
        # 准备签到数据
        sign_data = {
            "autonomyId": self.user_info["autonomyId"],
            "userId": self.user_info["userId"],
            "clockAddress": self.user_info["clockAddress"],
            "fileId": file_id,
            "clockTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "clockType": "签到",
            "clockContent": ""
        }
        
        try:
            logger.info("开始签到...")
            response = requests.post(
                url, 
                headers=self.headers,
                json=sign_data
            )
            
            logger.info(f"签到响应状态码: {response.status_code}")
            logger.info(f"签到响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.info("签到成功！")
                    return True
                else:
                    logger.error(f"签到失败: {result.get('msg')}")
                    return False
        except Exception as e:
            logger.error(f"签到异常: {str(e)}")
            return False

def load_config():
    """从环境变量加载配置"""
    try:
        users_config = os.environ.get('USERS_CONFIG')
        if not users_config:
            raise ValueError("未找到 USERS_CONFIG 环境变量")
        
        config = json.loads(users_config)
        return config['users']
    except Exception as e:
        logging.error(f"加载配置失败: {str(e)}")
        raise

def sign_in(user):
    """签到函数 - 保持原有的签到逻辑"""
    try:
        logger.info(f"开始处理用户 {user['loginAccount']} 的签到...")
        auto_sign = AutoSign(user)
        # 上传图片并签到
        image_path = "img.jpg"  # 签到用的图片路径
        file_id = auto_sign.upload_image(image_path)
        if file_id:
            success = auto_sign.sign_in(file_id)
            if success:
                logger.info(f"用户 {user['loginAccount']} 定时签到成功完成")
            else:
                logger.error(f"用户 {user['loginAccount']} 定时签到失败")
        else:
            logger.error(f"用户 {user['loginAccount']} 图片上传失败，无法完成签到")
    except Exception as e:
        logger.error(f"用户 {user['loginAccount']} 签到过程发生异常: {str(e)}")
        return

def main():
    """直接执行签到"""
    logger.info("开始执行签到...")
    try:
        users = load_config()
        for user in users:
            sign_in(user)
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")

if __name__ == "__main__":
    main()
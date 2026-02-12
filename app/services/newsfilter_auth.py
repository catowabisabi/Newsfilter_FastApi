"""
NewsFilter JWT认证管理器
处理登录、token管理、自动刷新
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import os
from dotenv import load_dotenv
from app.database.sqlite_cache import SQLiteCacheManager

# 加载环境变量
load_dotenv()


class NewsFilterAuth:
    """NewsFilter JWT认证管理器"""
    
    def __init__(self):
        self.auth_url = os.getenv("NEWSFILTER_AUTH_URL", "https://login.newsfilter.io/co/authenticate")
        self.token_url = os.getenv("NEWSFILTER_TOKEN_URL", "https://api.newsfilter.io/public/actions")
        
        self.username = os.getenv("NEWSFILTER_USERNAME")
        self.password = os.getenv("NEWSFILTER_PASSWORD")
        self.client_id = os.getenv("NEWSFILTER_CLIENT_ID")
        
        if not all([self.username, self.password, self.client_id]):
            raise ValueError("Missing NewsFilter credentials in environment variables")
        
        self.cache_manager = SQLiteCacheManager()
        
        # 系统状态
        self.is_login_failed = False
        self.last_failure_time = None
        self.failure_sleep_duration = 30 * 60  # 30分钟
        
        print("🔐 NewsFilter Auth Manager initialized")
    
    def _check_login_failure_status(self) -> bool:
        """检查是否处于登录失败睡眠期"""
        failure_status = self.cache_manager.get_system_status("login_failure")
        
        if failure_status:
            failure_time = datetime.fromisoformat(failure_status)
            if datetime.now() - failure_time < timedelta(seconds=self.failure_sleep_duration):
                self.is_login_failed = True
                self.last_failure_time = failure_time
                return True
        
        self.is_login_failed = False
        return False
    
    def _set_login_failure(self):
        """设置登录失败状态"""
        self.is_login_failed = True
        self.last_failure_time = datetime.now()
        self.cache_manager.set_system_status("login_failure", self.last_failure_time.isoformat())
        print("❌ Login failed, entering 30-minute sleep mode")
    
    def _clear_login_failure(self):
        """清除登录失败状态"""
        self.is_login_failed = False
        self.last_failure_time = None  
        self.cache_manager.set_system_status("login_failure", "")
        print("✅ Login failure status cleared")
    
    def get_remaining_sleep_time(self) -> int:
        """获取剩余睡眠时间（秒）"""
        if not self.is_login_failed or not self.last_failure_time:
            return 0
        
        elapsed = datetime.now() - self.last_failure_time
        remaining = self.failure_sleep_duration - elapsed.total_seconds()
        
        return max(0, int(remaining))
    
    def is_token_valid(self) -> bool:
        """检查当前token是否有效"""
        # 不再检查登录失败状态，只要token有效就使用
        # if self._check_login_failure_status():
        #     return False
        
        token_info = self.cache_manager.get_jwt_token()
        if not token_info:
            return False
        
        try:
            expires_at = datetime.fromisoformat(token_info["expires_at"])
            # 提前1分钟过期，避免频繁重新登录
            return datetime.now() < expires_at - timedelta(minutes=1)
        except:
            return False
    
    def get_valid_token(self) -> Optional[str]:
        """获取有效的access token"""
        # 首先检查现有token是否有效
        if self.is_token_valid():
            token_info = self.cache_manager.get_jwt_token()
            return token_info["access_token"] if token_info else None
            
        # 即使处于失败状态，如果有token也优先尝试使用（可能上次失败是误报）
        token_info = self.cache_manager.get_jwt_token()
        if token_info:
             return token_info["access_token"]
             
        # 没有token或token过期，检查是否处于冷却期
        if self._check_login_failure_status():
             return None
        
        # Token无效且不在冷却期，尝试重新登录
        return self._login_and_get_token()
    
    def _login_and_get_token(self) -> Optional[str]:
        """执行登录并获取token"""
        print("🔑 Attempting NewsFilter login...")
        
        try:
            # 第一步：用户认证
            auth_result = self._authenticate_user()
            if not auth_result["success"]:
                self._set_login_failure()
                return None
            
            # 第二步：获取token (如果需要额外步骤)
            token = self._get_token_from_auth(auth_result)
            if token:
                self._clear_login_failure()
                return token
            else:
                self._set_login_failure()
                return None
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            self._set_login_failure()
            return None
    
    def _authenticate_user(self) -> Dict[str, Any]:
        """用户认证第一步"""
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-HK,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://newsfilter.io",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "auth0-client": "eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMi4xIn0="
        }
        
        payload = {
            "client_id": self.client_id,
            "username": self.username,
            "password": self.password,
            "credential_type": "http://auth0.com/oauth/grant-type/password-realm",
            "realm": "Username-Password-Authentication"
        }
        
        response = requests.post(self.auth_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User authentication successful")
            return {
                "success": True,
                "data": data
            }
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": response.text
            }
    
    def _get_token_from_auth(self, auth_result: Dict[str, Any]) -> Optional[str]:
        """从认证结果获取token"""
        auth_data = auth_result["data"]
        
        # 检查是否直接包含access_token
        if "access_token" in auth_data:
            access_token = auth_data["access_token"]
            refresh_token = auth_data.get("refresh_token")
            expires_in = auth_data.get("expires_in", 86400)
            
            self.cache_manager.save_jwt_token(access_token, refresh_token, expires_in)
            print("🔑 JWT token obtained and saved")
            return access_token
        
        # 如果需要通过public API获取token
        elif "login_ticket" in auth_data:
            return self._exchange_ticket_for_token(auth_data)
        
        print("❌ No token or ticket found in auth response")
        return None
    
    def _exchange_ticket_for_token(self, auth_data: Dict[str, Any]) -> Optional[str]:
        """使用ticket交换token"""
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://newsfilter.io",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # 这里需要根据实际的token exchange流程调整
        payload = {
            "isPublic": True,
            "type": "getTokens",
            "code": auth_data.get("login_ticket", ""),
            "redirectUri": "https://newsfilter.io/callback"
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                if "accessToken" in token_data:
                    access_token = token_data["accessToken"]
                    refresh_token = token_data.get("refreshToken")
                    expires_in = token_data.get("expiresIn", 86400)
                    
                    self.cache_manager.save_jwt_token(access_token, refresh_token, expires_in)
                    print("🔑 JWT token exchanged and saved")
                    return access_token
                
            print(f"❌ Token exchange failed: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"❌ Token exchange error: {e}")
            return None
    
    def force_refresh_token(self) -> bool:
        """强制刷新token"""
        print("🔄 Forcing token refresh...")
        
        # 清除现有token
        self.cache_manager.set_system_status("force_refresh", "true")
        
        # 尝试获取新token
        new_token = self._login_and_get_token()
        
        if new_token:
            print("✅ Token refresh successful")
            return True
        else:
            print("❌ Token refresh failed")
            return False
    
    def get_auth_headers(self) -> Optional[Dict[str, str]]:
        """获取包含认证信息的headers"""
        token = self.get_valid_token()
        
        if not token:
            return None
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://newsfilter.io",
            "Referer": "https://newsfilter.io/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "caching-key": "sfksmdmdg0aadsf224533130"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取认证状态"""
        return {
            "is_login_failed": self.is_login_failed,
            "remaining_sleep_time": self.get_remaining_sleep_time(),
            "has_valid_token": self.is_token_valid(),
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }
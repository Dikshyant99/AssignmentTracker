import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


#load mcp_server/.env(works no matter which folder u run from)
load_dotenv(Path(__file__).parent/".env")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_EMAIL = os.getenv("API_EMAIL")
API_PASSWORD = os.getenv("API_PASSWORD")

class APIError(Exception):
    "An error from the Assignment tracker api"

class AssignmentAPI:
    def __init__(self):
        #one client reused for every requests
        self.client = httpx.Client(base_url=API_BASE_URL,timeout=10.0)
        self.token:str | None=None
        
# ---------- Login ----------
    def login(self) -> None:
        response = self._send("POST", "/auth/login", auth=False,
                              data={"username": API_EMAIL, "password": API_PASSWORD})
        if response.status_code != 200:
            raise APIError(f"Login failed: {self._error_message(response)}")
        self.token = response.json()["access_token"]
        
    # ---------- Main method every tool will use ----------
    def request(self, method: str, path: str, **kwargs):
        if self.token is None:
            self.login()
        response = self._send(method, path, **kwargs)

        # Token expired? Log in again and retry once
        if response.status_code == 401:
            self.login()
            response = self._send(method, path, **kwargs)

        if response.status_code >= 400:
            raise APIError(self._error_message(response))

        if response.status_code == 204:  # DELETE returns no body
            return None
        return response.json()
     # ---------- Helpers ----------
    def _send(self, method: str, path: str, auth: bool = True, **kwargs) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self.token}"} if auth else {}
        try:
            return self.client.request(method, path, headers=headers, **kwargs)
        except httpx.ConnectError:
            raise APIError(
                f"Can't reach the API at {API_BASE_URL}. Is 'docker compose up' running?"
            )
    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            detail = response.json().get("detail")
        except ValueError:
            return f"HTTP {response.status_code}"
        # 422 validation errors come as a list
        if isinstance(detail, list):
            return "; ".join(f"{d['loc'][-1]}: {d['msg']}" for d in detail)
        return str(detail) if detail else f"HTTP {response.status_code}"
    


 
 
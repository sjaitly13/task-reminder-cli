"""
Authentication Handler Module

Handles OAuth 2.0 authentication with Auth0.
Provides secure user authentication and token management.
"""

import os
import json
import webbrowser
import http.server
import socketserver
import threading
import time
from typing import Dict, Optional, Any
from urllib.parse import urlparse, parse_qs
import requests
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class AuthHandler:
    """Handles OAuth 2.0 authentication with Auth0."""

    def __init__(self):
        self.auth0_domain = os.getenv('AUTH0_DOMAIN')
        self.client_id = os.getenv('AUTH0_CLIENT_ID')
        self.client_secret = os.getenv('AUTH0_CLIENT_SECRET')
        self.callback_url = os.getenv('AUTH0_CALLBACK_URL', 'http://localhost:3000/callback')
        self.token_file = '.auth_token.json'
        
        self.access_token = None
        self.user_info = None
        self._load_token()

    def _load_token(self) -> None:
        """Load saved authentication token."""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    self.access_token = token_data.get('access_token')
                    self.user_info = token_data.get('user_info')
                    logger.info("Loaded saved authentication token")
        except Exception as e:
            logger.warning(f"Could not load saved token: {e}")

    def _save_token(self) -> None:
        """Save authentication token to file."""
        try:
            token_data = {
                'access_token': self.access_token,
                'user_info': self.user_info
            }
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f)
            logger.info("Saved authentication token")
        except Exception as e:
            logger.error(f"Could not save token: {e}")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.access_token is not None

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information."""
        return self.user_info

    def authenticate(self) -> bool:
        """Perform OAuth 2.0 authentication flow."""
        if not all([self.auth0_domain, self.client_id, self.client_secret]):
            logger.error("Auth0 configuration incomplete")
            return False

        try:
            # Create OAuth session
            oauth = OAuth2Session(
                self.client_id,
                redirect_uri=self.callback_url,
                scope='openid profile email'
            )

            # Get authorization URL
            auth_url, state = oauth.create_authorization_url(
                f'https://{self.auth0_domain}/authorize'
            )

            # Start local server to handle callback
            callback_data = self._start_callback_server()

            # Open browser for authentication
            print(f"Opening browser for authentication...")
            webbrowser.open(auth_url)

            # Wait for callback
            if callback_data:
                code = callback_data.get('code')
                if code:
                    # Exchange code for token
                    token = oauth.fetch_token(
                        f'https://{self.auth0_domain}/oauth/token',
                        authorization_response=f"{self.callback_url}?{callback_data}",
                        client_secret=self.client_secret
                    )

                    self.access_token = token['access_token']
                    
                    # Get user info
                    self.user_info = self._get_user_info(token['access_token'])
                    
                    # Save token
                    self._save_token()
                    
                    logger.info("Authentication successful")
                    return True

            logger.error("Authentication failed")
            return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def _start_callback_server(self) -> Optional[Dict[str, str]]:
        """Start local server to handle OAuth callback."""
        callback_data = None

        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                nonlocal callback_data
                callback_data = parse_qs(urlparse(self.path).query)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                response = """
                <html>
                <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the CLI.</p>
                </body>
                </html>
                """
                self.wfile.write(response.encode())

        # Start server
        with socketserver.TCPServer(("localhost", 3000), CallbackHandler) as httpd:
            httpd.timeout = 60  # 60 second timeout
            httpd.handle_request()

        return callback_data

    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Auth0."""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                f'https://{self.auth0_domain}/userinfo',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    def logout(self) -> None:
        """Logout user and clear tokens."""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            self.access_token = None
            self.user_info = None
            logger.info("Logged out successfully")
        except Exception as e:
            logger.error(f"Error during logout: {e}")

    def refresh_token(self) -> bool:
        """Refresh access token if needed."""
        # This would implement token refresh logic
        # For now, we'll just return True if we have a token
        return self.access_token is not None

    def get_headers(self) -> Dict[str, str]:
        """Get headers for authenticated requests."""
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}

    def validate_token(self) -> bool:
        """Validate current token."""
        if not self.access_token:
            return False

        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f'https://{self.auth0_domain}/userinfo',
                headers=headers
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False


class SimpleAuthHandler:
    """Simple authentication handler for development/testing."""
    
    def __init__(self):
        self.user_id = "default_user"
        self.is_authenticated_flag = False

    def authenticate(self) -> bool:
        """Simple authentication for development."""
        print("Using simple authentication for development...")
        self.is_authenticated_flag = True
        return True

    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self.is_authenticated_flag

    def get_user_info(self) -> Dict[str, Any]:
        """Get user info."""
        return {
            "user_id": self.user_id,
            "name": "Development User",
            "email": "dev@example.com"
        }

    def logout(self) -> None:
        """Logout."""
        self.is_authenticated_flag = False

    def get_headers(self) -> Dict[str, str]:
        """Get headers."""
        return {"X-User-ID": self.user_id}


def get_auth_handler() -> AuthHandler:
    """Get appropriate authentication handler."""
    # Check if Auth0 is configured
    if all([
        os.getenv('AUTH0_DOMAIN'),
        os.getenv('AUTH0_CLIENT_ID'),
        os.getenv('AUTH0_CLIENT_SECRET')
    ]):
        return AuthHandler()
    else:
        logger.warning("Auth0 not configured, using simple authentication")
        return SimpleAuthHandler() 
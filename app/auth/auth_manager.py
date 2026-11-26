"""
CogniLoad - Authentication Manager
Handles session state and user context
"""
from app.auth.db import login_user, create_user, get_supervisor_users, init_db

class AuthManager:
    def __init__(self):
        init_db()
        self.current_user = None
        self.session_token = None

    def login(self, username: str, password: str) -> dict:
        result = login_user(username, password)
        if result['success']:
            self.current_user = result['user']
        return result

    def logout(self):
        self.current_user = None
        self.session_token = None

    def is_logged_in(self) -> bool:
        return self.current_user is not None

    def is_supervisor(self) -> bool:
        return self.current_user and self.current_user['account_type'] == 'supervisor'

    def get_current_user(self) -> dict:
        return self.current_user

    def register_single_user(self, username: str, password: str,
                              full_name: str = '', email: str = '') -> dict:
        return create_user(username, password, 'single', None, full_name, email, True)

    def register_supervisor(self, username: str, password: str,
                            full_name: str = '', email: str = '') -> dict:
        return create_user(username, password, 'supervisor', None, full_name, email, True)

    def add_sub_user(self, username: str, password: str,
                     full_name: str = '') -> dict:
        if not self.is_supervisor():
            return {'success': False, 'error': 'Only supervisors can add users'}
        return create_user(
            username, password, 'employee',
            supervisor_id=self.current_user['id'],
            full_name=full_name,
            can_change_password=False
        )

    def get_my_users(self) -> list:
        if not self.is_supervisor():
            return []
        return get_supervisor_users(self.current_user['id'])


# Global auth instance
auth = AuthManager()

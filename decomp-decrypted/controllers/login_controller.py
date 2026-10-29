from app.views.login_view import LoginView
from app.models.user import User
class LoginController:
    def __init__(self):
        self.view = LoginView()
        self.model = User()
        self.view.login_button.config(command=self._handle_login)
    def _handle_login(self):
        username = self.view.username_entry.get()
        password = self.view.password_entry.get()
        if not username or not password:
            self.view.show_error('Please fill in all fields!')
            return
        if self.model.validate_login(username, password):
            self.view.show_success('Login successful!')
            return
        self.view.show_error('Invalid username or password!')
    def run(self):
        self.view.mainloop()

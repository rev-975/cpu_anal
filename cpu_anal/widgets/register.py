from textual.app import ComposeResult
from textual.containers import Vertical, Center, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Static, Label, Checkbox
from textual.message import Message
from cpu_anal.auth import UserManager


class RegisterScreen(ModalScreen):

    CSS = """
    RegisterScreen {
        align: center middle;
    }

    #register-container {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 4;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    Input {
        margin-bottom: 1;
    }

    #admin-checkbox-container {
        margin-top: 1;
        margin-bottom: 1;
        height: auto;
    }

    Checkbox {
        margin-right: 1;
    }

    #button-row {
        layout: horizontal;
        width: 100%;
        height: auto;
        margin-top: 1;
    }

    Button {
        width: 1fr;
        margin: 0 1;
    }

    #success-msg {
        color: $success;
        text-align: center;
        height: 1;
        margin-top: 1;
    }

    #error-msg {
        color: $error;
        text-align: center;
        height: 1;
        margin-top: 1;
    }

    .label {
        color: $text;
        margin-bottom: 0;
    }
    """

    class RegisterSuccess(Message):
        def __init__(self, username: str):
            self.username = username
            super().__init__()

    def __init__(self, user_manager: UserManager):
        super().__init__()
        self.user_manager = user_manager

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="register-container"):
                yield Static("USER REGISTRATION", id="title")
                yield Static("create a new user account", id="subtitle")
                yield Label("username:", classes="label")
                yield Input(placeholder="enter username", id="username-input")
                yield Label("password:", classes="label")
                yield Input(
                    placeholder="enter password",
                    password=True,
                    id="password-input"
                )
                yield Label("confirm password:", classes="label")
                yield Input(
                    placeholder="confirm password",
                    password=True,
                    id="confirm-password-input"
                )
                with Horizontal(id="admin-checkbox-container"):
                    yield Checkbox("Grant admin privileges", id="admin-checkbox")
                with Horizontal(id="button-row"):
                    yield Button("Register", variant="primary", id="register-btn")
                    yield Button("Cancel", variant="default", id="cancel-btn")
                yield Static("", id="success-msg")
                yield Static("", id="error-msg")

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "register-btn":
            await self.attempt_register()
        elif event.button.id == "cancel-btn":
            self.dismiss()

    async def on_input_submitted(self, event: Input.Submitted):
        await self.attempt_register()

    async def attempt_register(self):
        # get all inputs
        username_input = self.query_one("#username-input", Input)
        password_input = self.query_one("#password-input", Input)
        confirm_password_input = self.query_one("#confirm-password-input", Input)
        admin_checkbox = self.query_one("#admin-checkbox", Checkbox)
        error_msg = self.query_one("#error-msg", Static)
        success_msg = self.query_one("#success-msg", Static)

        username = username_input.value.strip()
        password = password_input.value
        confirm_password = confirm_password_input.value
        is_admin = admin_checkbox.value

        error_msg.update("")
        success_msg.update("")

        # validate inputs
        if not username or not password:
            error_msg.update("username and password are required")
            return

        if len(username) < 3:
            error_msg.update("username must be at least 3 characters")
            return

        if len(password) < 4:
            error_msg.update("password must be at least 4 characters")
            return

        if password != confirm_password:
            error_msg.update("passwords do not match")
            confirm_password_input.value = ""
            return

        if await self.user_manager.db.user_exists(username):
            error_msg.update(f"user '{username}' already exists")
            return

        # create user
        try:
            await self.user_manager.create_user(username, password, is_admin=is_admin)
            success_msg.update(f"✓ user '{username}' created successfully!")

            username_input.value = ""
            password_input.value = ""
            confirm_password_input.value = ""
            admin_checkbox.value = False

            self.post_message(self.RegisterSuccess(username))

        except Exception as e:
            error_msg.update(f"failed to create user: {str(e)}")

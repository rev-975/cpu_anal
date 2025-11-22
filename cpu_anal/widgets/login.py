from textual.app import ComposeResult
from textual.containers import Container, Vertical, Center
from textual.screen import Screen
from textual.widgets import Input, Button, Static, Label
from textual.message import Message
from cpu_anal.auth import UserManager


class LoginScreen(Screen):

    CSS = """
    LoginScreen {
        align: center middle;
    }

    #login-container {
        width: 60;
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

    Button {
        width: 100%;
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

    class LoginSuccess(Message):
        def __init__(self, user: str, is_admin: bool):
            self.user = user
            self.is_admin = is_admin
            super().__init__()

    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()

    async def on_mount(self):
        await self.user_manager.initialize()

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="login-container"):
                yield Static("CPU ANALYSIS", id="title")
                yield Static("terminal system monitor", id="subtitle")
                yield Label("user:", classes="label")
                yield Input(placeholder="enter user", id="user-input")
                yield Label("pass:", classes="label")
                yield Input(
                    placeholder="enter pass",
                    password=True,
                    id="pass-input"
                )
                yield Button("login", variant="primary", id="login-btn")
                yield Static("", id="error-msg")

    async def on_button_pressed(self, event: Button.Pressed):
        # handle login button click 
        if event.button.id == "login-btn":
            await self.attempt_login()

    async def on_input_submitted(self, event: Input.Submitted):
        """handle enter key in input fields"""
        await self.attempt_login()

    async def attempt_login(self):
        # try to authenticate the user
        user_input = self.query_one("#user-input", Input)
        pass_input = self.query_one("#pass-input", Input)
        error_msg = self.query_one("#error-msg", Static)

        username = user_input.value.strip()
        pwd = pass_input.value

        if not username or not pwd:
            error_msg.update("please enter both user and pass")
            return

        user = await self.user_manager.authenticate(username, pwd)

        if user:
            error_msg.update("")
            self.post_message(self.LoginSuccess(user.user, user.is_admin))
        else:
            error_msg.update("invalid user or pass")
            pass_input.value = ""

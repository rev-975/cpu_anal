from textual.app import ComposeResult
from textual.containers import Vertical, Center, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Static, Label
from textual.message import Message
from cpu_anal.auth import UserManager


class ChangePasswordScreen(ModalScreen):

    CSS = """
    ChangePasswordScreen {
        align: center middle;
    }

    #change-password-container {
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

    class PasswordChanged(Message):
        pass

    def __init__(self, user_manager: UserManager, current_user: str):
        super().__init__()
        self.user_manager = user_manager
        self.current_user = current_user

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="change-password-container"):
                yield Static("CHANGE PASSWORD", id="title")
                yield Static(f"changing password for: {self.current_user}", id="subtitle")
                yield Label("current password:", classes="label")
                yield Input(
                    placeholder="enter current password",
                    password=True,
                    id="current-password-input"
                )
                yield Label("new password:", classes="label")
                yield Input(
                    placeholder="enter new password",
                    password=True,
                    id="new-password-input"
                )
                yield Label("confirm new password:", classes="label")
                yield Input(
                    placeholder="confirm new password",
                    password=True,
                    id="confirm-password-input"
                )
                with Horizontal(id="button-row"):
                    yield Button("Change Password", variant="primary", id="change-btn")
                    yield Button("Cancel", variant="default", id="cancel-btn")
                yield Static("", id="success-msg")
                yield Static("", id="error-msg")

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "change-btn":
            await self.attempt_change_password()
        elif event.button.id == "cancel-btn":
            self.dismiss()

    async def on_input_submitted(self, event: Input.Submitted):
        await self.attempt_change_password()

    async def attempt_change_password(self):
        current_password_input = self.query_one("#current-password-input", Input)
        new_password_input = self.query_one("#new-password-input", Input)
        confirm_password_input = self.query_one("#confirm-password-input", Input)
        error_msg = self.query_one("#error-msg", Static)
        success_msg = self.query_one("#success-msg", Static)

        current_password = current_password_input.value
        new_password = new_password_input.value
        confirm_password = confirm_password_input.value

        error_msg.update("")
        success_msg.update("")

        # validate inputs
        if not current_password or not new_password:
            error_msg.update("all fields are required")
            return

        if len(new_password) < 4:
            error_msg.update("new password must be at least 4 characters")
            return

        if new_password != confirm_password:
            error_msg.update("new passwords do not match")
            confirm_password_input.value = ""
            return

        # verify current password
        user = await self.user_manager.authenticate(self.current_user, current_password)
        if not user:
            error_msg.update("current password is incorrect")
            current_password_input.value = ""
            return

        # update password
        try:
            new_hash = self.user_manager.hash_pass(new_password)
            await self.user_manager.db.update_password(self.current_user, new_hash)

            success_msg.update("✓ password changed successfully!")
            current_password_input.value = ""
            new_password_input.value = ""
            confirm_password_input.value = ""

            self.post_message(self.PasswordChanged())
            self.set_timer(1.5, self.dismiss)

        except Exception as e:
            error_msg.update(f"failed to change password: {str(e)}")

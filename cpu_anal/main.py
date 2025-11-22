from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer
from cpu_anal.widgets.login import LoginScreen
from cpu_anal.widgets.register import RegisterScreen
from cpu_anal.panels.cpu import CPUPanel
from cpu_anal.panels.mem import MemoryPanel
from cpu_anal.panels.proc import ProcessPanel
from cpu_anal.panels.network import NetworkPanel
from cpu_anal.auth import UserManager


class CPUAnalysisApp(App):

    CSS = """
    Screen {
        layout: vertical;
        background: #161616;
    }

    Header {
        background: #262626;
        color: #ffffff;
        border-bottom: heavy #393939;
    }

    Footer {
        background: #262626;
        border-top: heavy #393939;
        color: #ffffff;
    }

    #main-container {
        layout: vertical;
        height: 1fr;
        background: #161616;
        padding: 0 1;
    }

    #top-row {
        layout: horizontal;
        height: 25%;
        margin-bottom: 1;
    }

    #middle-row {
        layout: horizontal;
        height: 65%;
        margin-bottom: 1;
    }

    #bottom-row {
        layout: horizontal;
        height: 10%;
    }

    CPUPanel {
        width: 50%;
        margin-right: 1;
    }

    MemoryPanel {
        width: 50%;
    }

    ProcessPanel {
        width: 1fr;
    }

    NetworkPanel {
        width: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "quit"),
        ("r", "register", "register user"),
    ]

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.is_admin = False
        self.user_manager = UserManager()

    def on_mount(self):
        self.push_screen(LoginScreen())

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            pass
        yield Footer()

    def on_login_screen_login_success(self, message: LoginScreen.LoginSuccess):
        self.current_user = message.user
        self.is_admin = message.is_admin
        self.pop_screen()

        container = self.query_one("#main-container")
        container.remove_children()

        if self.is_admin:
            top_row = Horizontal(id="top-row")
            container.mount(top_row)
            top_row.mount(CPUPanel())
            top_row.mount(MemoryPanel())

            middle_row = Horizontal(id="middle-row")
            container.mount(middle_row)
            middle_row.mount(ProcessPanel(is_admin=True))

            bottom_row = Horizontal(id="bottom-row")
            container.mount(bottom_row)
            bottom_row.mount(NetworkPanel())
        else:
            top_row = Horizontal(id="top-row")
            container.mount(top_row)
            top_row.mount(CPUPanel())

            middle_row = Horizontal(id="middle-row")
            container.mount(middle_row)
            middle_row.mount(ProcessPanel(is_admin=False))

            bottom_row = Horizontal(id="bottom-row")
            container.mount(bottom_row)
            bottom_row.mount(NetworkPanel())

        self.title = f"CPU Analysis  •  {self.current_user}"
        if not self.is_admin:
            self.title += " (read-only)"

    def action_register(self):
        # only admin can register users
        if not self.is_admin:
            self.notify("only admins can register users", severity="error", timeout=3)
            return
        self.push_screen(RegisterScreen(self.user_manager))

    def on_register_screen_register_success(self, message: RegisterScreen.RegisterSuccess):
        # notify that user was created
        self.notify(f"user '{message.username}' registered successfully", timeout=3)


def run():
    app = CPUAnalysisApp()
    app.run()


if __name__ == "__main__":
    run()

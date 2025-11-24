from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer
from cpu_anal.widgets.login import LoginScreen
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
        ("x", "change_password", "change password"),
        ("u", "manage_users", "manage users"),
    ]

    def __init__(self):
        super().__init__()
        self.current_user_obj = None
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
        self.current_user_obj = message.user_obj
        self.current_user = message.user_obj.user
        self.is_admin = message.user_obj.is_admin
        self.pop_screen()

        container = self.query_one("#main-container")
        container.remove_children()

        # Build layout based on permissions
        has_top_row = self.current_user_obj.can_view_cpu or self.current_user_obj.can_view_memory
        has_bottom_row = self.current_user_obj.can_view_network

        if has_top_row:
            top_row = Horizontal(id="top-row")
            container.mount(top_row)
            if self.current_user_obj.can_view_cpu:
                top_row.mount(CPUPanel())
            if self.current_user_obj.can_view_memory:
                top_row.mount(MemoryPanel())

        if self.current_user_obj.can_view_processes:
            middle_row = Horizontal(id="middle-row")
            container.mount(middle_row)
            middle_row.mount(ProcessPanel(
                is_admin=self.current_user_obj.can_kill_processes,
                can_manage_users=self.current_user_obj.can_manage_users
            ))

        if has_bottom_row:
            bottom_row = Horizontal(id="bottom-row")
            container.mount(bottom_row)
            bottom_row.mount(NetworkPanel())

        # Build title with permissions info
        self.title = f"CPU Analysis  •  {self.current_user}"
        perms = []
        if self.current_user_obj.is_admin:
            perms.append("admin")
        if self.current_user_obj.can_kill_processes:
            perms.append("can kill")
        if self.current_user_obj.can_manage_users:
            perms.append("can manage users")
        if perms:
            self.title += f" ({', '.join(perms)})"

    def action_change_password(self):
        from cpu_anal.widgets.change_password import ChangePasswordScreen
        self.push_screen(ChangePasswordScreen(self.user_manager, self.current_user))

    def action_manage_users(self):
        if not self.current_user_obj or not self.current_user_obj.can_manage_users:
            self.notify("permission denied - user management requires can_manage_users permission", severity="error", timeout=3)
            return
        from cpu_anal.widgets.manage_users import ManageUsersScreen
        self.push_screen(ManageUsersScreen(self.user_manager, self.current_user))

    def on_change_password_screen_password_changed(self, message):
        self.notify("password changed successfully", timeout=3)


def run():
    app = CPUAnalysisApp()
    app.run()


if __name__ == "__main__":
    run()

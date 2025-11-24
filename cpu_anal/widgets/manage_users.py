from textual.app import ComposeResult
from textual.containers import Vertical, Center, Horizontal, Container, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Checkbox, DataTable, Label
from textual.message import Message
from textual.binding import Binding
from cpu_anal.auth import UserManager


class ManageUsersScreen(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss_screen", "close", show=False),
        Binding("q", "dismiss_screen", "close", show=False),
    ]

    CSS = """
    ManageUsersScreen {
        align: center middle;
    }

    #manage-container {
        width: 100;
        height: 40;
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

    #users-table {
        width: 100%;
        height: 10;
        margin-bottom: 2;
    }

    #permissions-container {
        border: solid $primary;
        padding: 1 2;
        margin-bottom: 2;
        height: auto;
        background: #161616;
    }

    #permissions-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    #perm-grid {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 2;
        height: auto;
    }

    Checkbox {
        margin: 0;
    }

    #button-row {
        layout: horizontal;
        width: 100%;
        height: auto;
    }

    Button {
        width: 1fr;
        margin: 0 1;
    }

    #error-msg {
        color: $error;
        text-align: center;
        height: 1;
        margin-top: 1;
    }

    #info-msg {
        color: $text-muted;
        text-align: center;
        height: 1;
        margin-top: 1;
    }
    """

    def __init__(self, user_manager: UserManager, current_user: str):
        super().__init__()
        self.user_manager = user_manager
        self.current_user = current_user
        self.selected_user = None
        self.users_data = []

    def compose(self) -> ComposeResult:
        with Center():
            with ScrollableContainer(id="manage-container"):
                yield Static("USER MANAGEMENT", id="title")
                yield Static("manage users and permissions", id="subtitle")
                yield DataTable(id="users-table", zebra_stripes=True, show_header=True)

                with Container(id="permissions-container"):
                    yield Static("", id="permissions-title")
                    with Vertical(id="perm-grid"):
                        yield Checkbox("View CPU", id="perm-cpu")
                        yield Checkbox("View Memory", id="perm-memory")
                        yield Checkbox("View Processes", id="perm-processes")
                        yield Checkbox("View Network", id="perm-network")
                        yield Checkbox("Kill Processes", id="perm-kill")
                        yield Checkbox("Manage Users", id="perm-manage")
                        yield Checkbox("Admin", id="perm-admin")

                with Horizontal(id="button-row"):
                    yield Button("Save Changes", variant="primary", id="save-btn")
                    yield Button("Close", variant="default", id="close-btn")
                yield Static("", id="error-msg")
                yield Static("select a user to edit permissions", id="info-msg")

    async def on_mount(self):
        table = self.query_one(DataTable)
        table.add_column("User", key="user", width=20)
        table.add_column("Admin", key="admin", width=8)
        table.add_column("CPU", key="cpu", width=6)
        table.add_column("Memory", key="memory", width=8)
        table.add_column("Proc", key="proc", width=6)
        table.add_column("Net", key="net", width=6)
        table.add_column("Kill", key="kill", width=6)
        table.add_column("Manage", key="manage", width=8)

        table.cursor_type = "row"
        table.focus()

        await self.load_users()

    async def load_users(self):
        self.users_data = await self.user_manager.db.get_all_users()
        table = self.query_one(DataTable)
        table.clear()

        for user in self.users_data:
            table.add_row(
                f"[#82cfff]{user['user']}[/]",
                "[#42be65]✓[/]" if user['is_admin'] else "[#6272a4]✗[/]",
                "[#42be65]✓[/]" if user.get('can_view_cpu', 1) else "[#6272a4]✗[/]",
                "[#42be65]✓[/]" if user.get('can_view_memory', 0) else "[#6272a4]✗[/]",
                "[#42be65]✓[/]" if user.get('can_view_processes', 1) else "[#6272a4]✗[/]",
                "[#42be65]✓[/]" if user.get('can_view_network', 1) else "[#6272a4]✗[/]",
                "[#42be65]✓[/]" if user.get('can_kill_processes', 0) else "[#6272a4]✗[/]",
                "[#42be65]✓[/]" if user.get('can_manage_users', 0) else "[#6272a4]✗[/]",
                key=user['user']
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.cursor_row >= len(self.users_data):
            return

        user_data = self.users_data[event.cursor_row]
        self.selected_user = user_data['user']

        # Update permissions title
        self.query_one("#permissions-title", Static).update(
            f"Permissions for: {self.selected_user}"
        )

        # Update checkboxes
        self.query_one("#perm-cpu", Checkbox).value = bool(user_data.get('can_view_cpu', 1))
        self.query_one("#perm-memory", Checkbox).value = bool(user_data.get('can_view_memory', 0))
        self.query_one("#perm-processes", Checkbox).value = bool(user_data.get('can_view_processes', 1))
        self.query_one("#perm-network", Checkbox).value = bool(user_data.get('can_view_network', 1))
        self.query_one("#perm-kill", Checkbox).value = bool(user_data.get('can_kill_processes', 0))
        self.query_one("#perm-manage", Checkbox).value = bool(user_data.get('can_manage_users', 0))
        self.query_one("#perm-admin", Checkbox).value = bool(user_data.get('is_admin', 0))

        self.query_one("#error-msg", Static).update("")
        self.query_one("#info-msg", Static).update(
            "[#82cfff]modify permissions and click 'Save Changes'[/]"
        )

    def action_dismiss_screen(self):
        self.dismiss()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save-btn":
            await self.save_permissions()
        elif event.button.id == "close-btn":
            self.dismiss()

    async def save_permissions(self):
        error_msg = self.query_one("#error-msg", Static)
        info_msg = self.query_one("#info-msg", Static)

        if not self.selected_user:
            error_msg.update("please select a user first")
            return

        # Get checkbox values
        permissions = {
            'can_view_cpu': self.query_one("#perm-cpu", Checkbox).value,
            'can_view_memory': self.query_one("#perm-memory", Checkbox).value,
            'can_view_processes': self.query_one("#perm-processes", Checkbox).value,
            'can_view_network': self.query_one("#perm-network", Checkbox).value,
            'can_kill_processes': self.query_one("#perm-kill", Checkbox).value,
            'can_manage_users': self.query_one("#perm-manage", Checkbox).value,
            'is_admin': self.query_one("#perm-admin", Checkbox).value
        }

        # If user is admin, force all permissions to be enabled
        if permissions['is_admin']:
            permissions['can_view_cpu'] = True
            permissions['can_view_memory'] = True
            permissions['can_view_processes'] = True
            permissions['can_view_network'] = True
            permissions['can_kill_processes'] = True
            permissions['can_manage_users'] = True

        # Prevent removing your own manage_users permission
        if self.selected_user == self.current_user and not permissions['can_manage_users']:
            error_msg.update("cannot remove your own user management permission")
            return

        try:
            await self.user_manager.db.update_user_permissions(
                self.selected_user, **permissions
            )
            await self.load_users()
            error_msg.update("")
            if permissions['is_admin']:
                info_msg.update(f"[#42be65]✓ permissions updated for {self.selected_user} (admin has all permissions)[/]")
            else:
                info_msg.update(f"[#42be65]✓ permissions updated for {self.selected_user}[/]")
        except Exception as e:
            error_msg.update(f"failed to update permissions: {str(e)}")

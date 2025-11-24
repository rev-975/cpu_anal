import psutil
from typing import Literal
from textual.app import ComposeResult
from textual.containers import Vertical, Container, ScrollableContainer
from textual.widgets import Static, Input, DataTable
from textual.reactive import reactive
from textual.binding import Binding
from cpu_anal.models import ProcInfo


class ProcessPanel(Static):
    CSS = """
    ProcessPanel {
        border: heavy #be95ff;
        border-title-color: #be95ff;
        border-title-style: bold;
        height: 100%;
        padding: 1 2;
        background: #262626;
    }

    ProcessPanel > Vertical {
        height: 100%;
    }

    ProcessPanel > Vertical > * {
        margin: 0;
    }

    #proc-info {
        color: #ffffff;
        height: auto;
        margin-bottom: 1;
    }

    #search-container {
        height: 1;
        margin-bottom: 0;
        padding: 0;
        background: #161616;
    }

    #search-input {
        width: 100%;
        height: 1;
        border: none;
        background: #161616;
        color: #ffffff;
        padding: 0;
        margin: 0;
    }

    #proc-table {
        width: 100%;
        height: 100%;
        background: #262626;
    }

    #table-container {
        height: 1fr;
    }

    #help-text {
        color: #82cfff;
        height: 1;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("c", "sort_cpu", "cpu", show=False),
        Binding("m", "sort_mem", "mem", show=False),
        Binding("p", "sort_pid", "pid", show=False),
        Binding("k", "kill_proc", "kill", show=False),
        Binding("/", "search", "search", show=False),
        Binding("escape", "clear_search", "clear", show=False),
    ]

    processes = reactive([])
    sort_by: Literal["pid", "cpu", "mem"] = reactive("cpu")
    search_query = reactive("")

    def __init__(self, is_admin: bool = False, can_manage_users: bool = False):
        super().__init__()
        self.is_admin = is_admin
        self.can_manage_users = can_manage_users
        self._ready = False

    def compose(self) -> ComposeResult:
        self.border_title = "  PROCESSES  "
        with Vertical():
            yield Static("", id="proc-info")
            yield Input(placeholder="search processes", id="search-input")
            with Container(id="table-container"):
                yield DataTable(id="proc-table", zebra_stripes=False, show_header=True)

            help_text = "[#42be65][[q]][/]quit [#42be65][[x]][/]pass [#42be65][[c]][/]cpu [#42be65][[m]][/]mem [#42be65][[p]][/]pid [#42be65][[/]][/]search [#42be65][[esc]][/]clear"
            if self.is_admin:
                help_text += " [#ee5396][[k]][/]kill"
            if self.can_manage_users:
                help_text += " [#82cfff][[u]][/]users"
            yield Static(help_text, id="help-text")

    def on_mount(self):
        table = self.query_one(DataTable)

        table.add_column("PID", key="pid", width=8)
        table.add_column("NAME", key="name", width=25)
        table.add_column("CPU%", key="cpu", width=9)
        table.add_column("MEM%", key="mem", width=9)
        table.add_column("MEM", key="mem_mb", width=10)
        table.add_column("STATE", key="status", width=10)
        table.add_column("USER", key="user", width=15)

        table.cursor_type = "row"
        table.focus()

        self._ready = True
        self.set_interval(2.0, self.update_processes)

    async def update_processes(self):
        if not self._ready:
            return
        try:
            procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', "status", "username"]):
                try:
                    info = proc.info
                    if self.search_query and self.search_query.lower() not in info['name'].lower():
                        continue

                    procs.append(
                        ProcInfo(
                            pid=info['pid'],
                            name=info['name'][:23],
                            cpu_percent=info['cpu_percent'] or 0.0,
                            memory_percent=info['memory_percent'] or 0.0,
                            memory_mb=(info['memory_info'].rss / 1024 / 1024) if info['memory_info'] else 0.0,
                            status=info['status'],
                            user=info['username'] or 'N/A'
                        )
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if self.sort_by == "cpu":
                procs.sort(key=lambda p: p.cpu_percent, reverse=True)
            elif self.sort_by == "mem":
                procs.sort(key=lambda p: p.memory_percent, reverse=True)
            elif self.sort_by == "pid":
                procs.sort(key=lambda p: p.pid)

            self.processes = procs
            self.refresh_table()

            info_text = f"[#42be65]●[/] [#ffffff]{len(procs)} processes[/] [#6272a4]│[/] [#82cfff]sort:[/] [#ffffff]{self.sort_by.upper()}[/]"
            if self.search_query:
                info_text += f" [#6272a4]│[/] [#ff7eb6]filter:[/] [#ffffff]{self.search_query}[/]"
            self.query_one("#proc-info", Static).update(info_text)

        except Exception:
            pass

    def refresh_table(self):
        try:
            table = self.query_one(DataTable)
            search_input = self.query_one("#search-input", Input)

            # Preserve cursor position
            cursor_row = table.cursor_row
            if cursor_row >= len(self.processes):
                cursor_row = max(0, len(self.processes) - 1)

            table.clear()

            for proc in self.processes:
                if proc.cpu_percent >= 80:
                    cpu_color = "#ee5396"
                elif proc.cpu_percent >= 50:
                    cpu_color = "#ff7eb6"
                elif proc.cpu_percent >= 10:
                    cpu_color = "#82cfff"
                else:
                    cpu_color = "#ffffff"

                if proc.memory_percent >= 80:
                    mem_color = "#ee5396"
                elif proc.memory_percent >= 50:
                    mem_color = "#ff7eb6"
                elif proc.memory_percent >= 10:
                    mem_color = "#82cfff"
                else:
                    mem_color = "#ffffff"

                table.add_row(
                    f"[#82cfff]{proc.pid}[/]",
                    f"[#ffffff]{proc.name}[/]",
                    f"[{cpu_color}]{proc.cpu_percent:6.1f}[/]",
                    f"[{mem_color}]{proc.memory_percent:6.1f}[/]",
                    f"[#ffffff]{proc.memory_mb:7.1f}M[/]",
                    f"[#6272a4]{proc.status[:8]}[/]",
                    f"[#82cfff]{proc.user[:13]}[/]",
                    key=str(proc.pid)
                )

            if len(self.processes) > 0 and cursor_row >= 0:
                table.move_cursor(row=cursor_row)
                # Only focus table if search input doesn't have focus
                if not search_input.has_focus:
                    table.focus()

        except Exception:
            pass

    def action_sort_cpu(self):
        self.sort_by = "cpu"
        self.run_worker(self.update_processes())

    def action_sort_mem(self):
        self.sort_by = "mem"
        self.run_worker(self.update_processes())

    def action_sort_pid(self):
        self.sort_by = "pid"
        self.run_worker(self.update_processes())

    def action_search(self):
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self):
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.search_query = ""
        self.query_one(DataTable).focus()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search-input":
            self.search_query = event.value
            self.run_worker(self.update_processes())

    async def action_kill_proc(self):
        if not self.is_admin:
            self.notify("[#ee5396]✗[/] permission denied", severity="error", timeout=3)
            return

        table = self.query_one(DataTable)
        if table.cursor_row >= len(self.processes):
            return

        proc = self.processes[table.cursor_row]

        try:
            process = psutil.Process(proc.pid)
            process.terminate()
            self.notify(f"[#42be65]✓[/] killed {proc.pid} ({proc.name})", timeout=3)
            await self.app.sleep(0.5)
            await self.update_processes()
        except psutil.NoSuchProcess:
            self.notify(f"[#ff7eb6]⚠[/] process {proc.pid} not found", severity="warning", timeout=3)
        except psutil.AccessDenied:
            self.notify(f"[#ee5396]✗[/] permission denied for {proc.pid}", severity="error", timeout=3)
        except Exception as e:
            self.notify(f"[#ee5396]✗[/] error: {str(e)}", severity="error", timeout=3)

    def notify(self, message: str, severity: str = "info", timeout: float = 2.0):
        if hasattr(self.app, "notify"):
            self.app.notify(message, severity=severity, timeout=timeout)

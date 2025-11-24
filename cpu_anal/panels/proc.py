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
        Binding("a", "toggle_show_all", "show all", show=False),
        Binding("n", "next_page", "next page", show=False),
        Binding("b", "prev_page", "prev page", show=False),
    ]

    # constants for performance optimization
    top_n_limit = 50  # number of processes to show in fast mode
    processes_per_page = 50  # processes per page in show all mode

    processes = reactive([])
    sort_by: Literal["pid", "cpu", "mem"] = reactive("cpu")
    search_query = reactive("")
    show_all = reactive(False)  # toggle between fast mode (top n) and show all mode
    current_page = reactive(0)  # current page in show all mode

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

            help_text = "[#42be65][[c]][/]cpu [#42be65][[m]][/]mem [#42be65][[p]][/]pid [#ff7eb6][[a]][/]mode [#be95ff][[n/b]][/]page [#42be65][[/]][/]search [#42be65][[esc]][/]clear"
            if self.is_admin:
                help_text += " [#ee5396][[k]][/]kill"
            if self.can_manage_users:
                help_text += " [#82cfff][[u]][/]users"
            help_text += " [#42be65][[q]][/]quit [#42be65][[x]][/]change pass"
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
            # in fast mode with no search, we can optimize by limiting early
            limit = None if (self.show_all or self.search_query) else self.top_n_limit * 3  # 3x buffer for sorting

            count = 0
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
                    count += 1

                    # early exit in fast mode to avoid scanning all processes
                    if limit and count >= limit:
                        break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # sort all collected processes
            if self.sort_by == "cpu":
                procs.sort(key=lambda p: p.cpu_percent, reverse=True)
            elif self.sort_by == "mem":
                procs.sort(key=lambda p: p.memory_percent, reverse=True)
            elif self.sort_by == "pid":
                procs.sort(key=lambda p: p.pid)

            # in fast mode, limit to top n after sorting
            if not self.show_all and not self.search_query:
                procs = procs[:self.top_n_limit]

            self.processes = procs
            self.refresh_table()
            self.update_info_text()

        except Exception:
            pass

    def update_info_text(self):
        try:
            # update info text with mode and pagination info
            mode_text = "[#ff7eb6]FAST[/]" if not self.show_all else "[#82cfff]ALL[/]"
            info_text = f"[#42be65]●[/] {mode_text} [#ffffff]{len(self.processes)} processes[/] [#6272a4]│[/] [#82cfff]sort:[/] [#ffffff]{self.sort_by.upper()}[/]"

            if self.show_all and len(self.processes) > self.processes_per_page:
                total_pages = (len(self.processes) + self.processes_per_page - 1) // self.processes_per_page
                info_text += f" [#6272a4]│[/] [#be95ff]page:[/] [#ffffff]{self.current_page + 1}/{total_pages}[/]"

            if self.search_query:
                info_text += f" [#6272a4]│[/] [#ff7eb6]filter:[/] [#ffffff]{self.search_query}[/]"

            self.query_one("#proc-info", Static).update(info_text)
        except Exception:
            pass

    def refresh_table(self):
        try:
            table = self.query_one(DataTable)
            search_input = self.query_one("#search-input", Input)

            # remember which PID the cursor was on (not just the row number)
            cursor_row = table.cursor_row
            selected_pid = None

            # determine which processes to display based on pagination
            if self.show_all and len(self.processes) > self.processes_per_page:
                # ensure current_page is valid
                total_pages = (len(self.processes) + self.processes_per_page - 1) // self.processes_per_page
                if self.current_page >= total_pages:
                    self.current_page = total_pages - 1
                if self.current_page < 0:
                    self.current_page = 0

                start_idx = self.current_page * self.processes_per_page
                end_idx = min(start_idx + self.processes_per_page, len(self.processes))
                display_procs = self.processes[start_idx:end_idx]
            else:
                display_procs = self.processes

            # get the PID of the currently selected process before clearing
            if 0 <= cursor_row < len(display_procs):
                selected_pid = display_procs[cursor_row].pid

            table.clear()

            for proc in display_procs:
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

            # restore cursor to the same PID if it still exists in the list
            if len(display_procs) > 0:
                new_cursor_row = 0

                # try to find the previously selected PID in the new list
                if selected_pid is not None:
                    for i, proc in enumerate(display_procs):
                        if proc.pid == selected_pid:
                            new_cursor_row = i
                            break
                    else:
                        # PID not found, keep cursor at same row or clamp to valid range
                        new_cursor_row = min(cursor_row, len(display_procs) - 1)
                        new_cursor_row = max(0, new_cursor_row)

                table.move_cursor(row=new_cursor_row)
                # only focus table if search input doesn't have focus
                if not search_input.has_focus:
                    table.focus()

        except Exception:
            pass

    def action_sort_cpu(self):
        self.sort_by = "cpu"
        self.current_page = 0  # reset to first page when sort changes
        self.run_worker(self.update_processes())

    def action_sort_mem(self):
        self.sort_by = "mem"
        self.current_page = 0  # reset to first page when sort changes
        self.run_worker(self.update_processes())

    def action_sort_pid(self):
        self.sort_by = "pid"
        self.current_page = 0  # reset to first page when sort changes
        self.run_worker(self.update_processes())

    def action_search(self):
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self):
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.search_query = ""
        self.query_one(DataTable).focus()

    def action_toggle_show_all(self):
        self.show_all = not self.show_all
        self.current_page = 0  # reset to first page when toggling
        mode_name = "ALL" if self.show_all else "FAST"
        self.notify(f"[#82cfff]Mode:[/] [#ffffff]{mode_name}[/]", timeout=2)
        self.run_worker(self.update_processes())

    def action_next_page(self):
        if not self.show_all or len(self.processes) <= self.processes_per_page:
            return
        total_pages = (len(self.processes) + self.processes_per_page - 1) // self.processes_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_table()
            # move cursor to top of new page
            table = self.query_one(DataTable)
            table.move_cursor(row=0)
            self.update_info_text()

    def action_prev_page(self):
        if not self.show_all or len(self.processes) <= self.processes_per_page:
            return
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()
            # move cursor to top of new page
            table = self.query_one(DataTable)
            table.move_cursor(row=0)
            self.update_info_text()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "search-input":
            self.search_query = event.value
            self.current_page = 0  # reset to first page when search changes
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

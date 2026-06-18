import psutil
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


class MemoryPanel(Static):

    CSS = """
    MemoryPanel {
        border: heavy #82cfff;
        border-title-color: #82cfff;
        border-title-style: bold;
        height: 100%;
        width: 100%;
        padding: 1 2;
        background: #262626;
    }

    MemoryPanel > Vertical {
        width: 100%;
        height: 100%;
    }

    #ram-stats {
        margin-bottom: 2;
    }

    #swap-stats {
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        self.border_title = "  MEMORY  "
        with Vertical():
            yield Static("", id="ram-stats")
            yield Static("", id="swap-stats")

    def on_mount(self):
        self.set_interval(1.0, self.update_memory_stats)
        self.call_after_refresh(self.update_memory_stats)

    async def update_memory_stats(self):
        try:
            ram = psutil.virtual_memory()
            ram_pct = ram.percent
            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)
            ram_available_gb = ram.available / (1024 ** 3)

            swap = psutil.swap_memory()
            swap_pct = swap.percent
            swap_used_gb = swap.used / (1024 ** 3)
            swap_total_gb = swap.total / (1024 ** 3)

            ram_bar = self._generate_bar(ram_pct, 50)
            ram_text = f"[bold #42be65]RAM[/]\n"
            ram_text += f"{ram_bar} [#f2f4f8]{ram_pct:5.1f}%[/]\n"
            ram_text += f"[#82cfff]Used:[/] [#f2f4f8]{ram_used_gb:6.2f}[/] [#525252]/[/] [#dde1e6]{ram_total_gb:6.2f} GB[/]\n"
            ram_text += f"[#82cfff]Free:[/] [#42be65]{ram_available_gb:6.2f} GB[/]"

            self.query_one("#ram-stats", Static).update(ram_text)

            if swap_total_gb > 0:
                swap_bar = self._generate_bar(swap_pct, 50)
                swap_text = f"[bold #be95ff]SWAP[/]\n"
                swap_text += f"{swap_bar} [#f2f4f8]{swap_pct:5.1f}%[/]\n"
                swap_text += f"[#82cfff]Used:[/] [#f2f4f8]{swap_used_gb:6.2f}[/] [#525252]/[/] [#dde1e6]{swap_total_gb:6.2f} GB[/]"
            else:
                swap_text = f"[bold #be95ff]SWAP[/]\n[#525252]not configured[/]"

            self.query_one("#swap-stats", Static).update(swap_text)

        except Exception as e:
            self.query_one("#ram-stats", Static).update(f"[#ee5396]Error: {e}[/]")

    def _generate_bar(self, percent: float, width: int = 20) -> str:
        filled = int((percent / 100) * width)
        empty = width - filled

        if percent >= 90:
            color = "#ee5396"
        elif percent >= 75:
            color = "#ff7eb6"
        elif percent >= 50:
            color = "#82cfff"
        else:
            color = "#42be65"

        bar = f"[{color}]{'▬' * filled}[/][#393939]{'▬' * empty}[/]"
        return bar

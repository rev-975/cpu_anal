import psutil
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive


class CPUPanel(Static):

    CSS = """
    CPUPanel {
        border: heavy #42be65;
        border-title-color: #42be65;
        border-title-style: bold;
        height: 100%;
        padding: 1 2;
        background: #262626;
    }

    #cpu-overall {
        color: #f2f4f8;
        margin-bottom: 1;
    }

    #cpu-frequency {
        color: #82cfff;
        margin-bottom: 1;
    }

    #cpu-sparkline {
        color: #42be65;
        margin-bottom: 2;
    }

    #cpu-cores {
        margin-top: 0;
    }
    """

    cpu_percent = reactive(0.0)
    cpu_freq = reactive(0.0)
    cpu_history = reactive([])

    def compose(self) -> ComposeResult:
        self.border_title = "  CPU  "
        with Vertical():
            yield Static("", id="cpu-overall")
            yield Static("", id="cpu-frequency")
            yield Static("", id="cpu-sparkline")
            yield Static("", id="cpu-cores")

    def on_mount(self):
        self.update_interval = self.set_interval(1.0, self.update_cpu_stats)
        self.cpu_history = [0.0] * 60

    async def update_cpu_stats(self):
        cpu_pct = psutil.cpu_percent(interval=0.1)
        self.cpu_percent = cpu_pct

        freq = psutil.cpu_freq()
        if freq:
            self.cpu_freq = freq.current

        self.cpu_history = self.cpu_history[1:] + [cpu_pct]
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)

        self.query_one("#cpu-overall", Static).update(
            f"[bold #42be65]Total:[/] [#f2f4f8]{cpu_pct:6.2f}%[/]"
        )

        if freq:
            self.query_one("#cpu-frequency", Static).update(
                f"[bold #82cfff]Freq:[/]  [#f2f4f8]{freq.current:7.0f} MHz[/]"
            )

        sparkline = self._generate_sparkline(self.cpu_history)
        self.query_one("#cpu-sparkline", Static).update(sparkline)

        cores_text = ""
        cols = 2 if len(per_cpu) > 8 else 1

        if cols == 2:
            mid = (len(per_cpu) + 1) // 2
            for i in range(mid):
                left_idx = i
                right_idx = i + mid

                left_bar = self._generate_bar(per_cpu[left_idx], 20)
                left_line = f"[#82cfff]{left_idx:2d}[/] {left_bar} [#f2f4f8]{per_cpu[left_idx]:5.1f}%[/]"

                if right_idx < len(per_cpu):
                    right_bar = self._generate_bar(per_cpu[right_idx], 20)
                    right_line = f"[#82cfff]{right_idx:2d}[/] {right_bar} [#f2f4f8]{per_cpu[right_idx]:5.1f}%[/]"
                    cores_text += f"{left_line}    {right_line}\n"
                else:
                    cores_text += f"{left_line}\n"
        else:
            for i, core_pct in enumerate(per_cpu):
                bar = self._generate_bar(core_pct, 40)
                cores_text += f"[#82cfff]{i:2d}[/] {bar} [#f2f4f8]{core_pct:5.1f}%[/]\n"

        self.query_one("#cpu-cores", Static).update(cores_text.rstrip())

    def _generate_sparkline(self, data: list[float]) -> str:
        if not data:
            return ""

        chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        max_val = max(data) if max(data) > 0 else 1
        normalized = [int((val / max_val) * 7) for val in data]

        result = ""
        for val in normalized:
            idx = min(val, 7)
            if idx >= 6:
                color = "#ee5396"
            elif idx >= 4:
                color = "#ff7eb6"
            elif idx >= 2:
                color = "#82cfff"
            else:
                color = "#42be65"
            result += f"[{color}]{chars[idx]}[/]"

        return result

    def _generate_bar(self, percent: float, width: int = 20) -> str:
        filled = int((percent / 100) * width)
        empty = width - filled

        if percent >= 90:
            color = "#ee5396"
        elif percent >= 70:
            color = "#ff7eb6"
        elif percent >= 50:
            color = "#82cfff"
        else:
            color = "#42be65"

        bar = f"[{color}]{'▬' * filled}[/][#393939]{'▬' * empty}[/]"
        return bar

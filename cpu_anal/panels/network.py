import psutil
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.reactive import reactive


class NetworkPanel(Static):

    CSS = """
    NetworkPanel {
        border: heavy #3ddbd9;
        border-title-color: #3ddbd9;
        border-title-style: bold;
        height: 100%;
        width: 100%;
        padding: 1 2;
        background: #262626;
    }

    NetworkPanel > Vertical {
        width: 100%;
        height: 100%;
    }

    #network-stats {
        margin-bottom: 1;
        color: #ffffff;
    }

    #network-interfaces {
        color: #ffffff;
    }
    """

    bytes_sent_last = reactive(0)
    bytes_recv_last = reactive(0)

    def compose(self) -> ComposeResult:
        self.border_title = "  NETWORK  "
        with Vertical():
            yield Static("", id="network-stats")
            yield Static("", id="network-interfaces")

    def on_mount(self):
        net_io = psutil.net_io_counters()
        self.bytes_sent_last = net_io.bytes_sent
        self.bytes_recv_last = net_io.bytes_recv

        self.set_interval(1.0, self.update_network_stats)
        self.call_after_refresh(self.update_network_stats)

    async def update_network_stats(self):
        try:
            net_io = psutil.net_io_counters()

            bytes_sent_rate = (net_io.bytes_sent - self.bytes_sent_last) / 1.0
            bytes_recv_rate = (net_io.bytes_recv - self.bytes_recv_last) / 1.0

            self.bytes_sent_last = net_io.bytes_sent
            self.bytes_recv_last = net_io.bytes_recv

            sent_rate_str = self._format_bytes(bytes_sent_rate)
            recv_rate_str = self._format_bytes(bytes_recv_rate)

            total_sent_str = self._format_bytes(net_io.bytes_sent)
            total_recv_str = self._format_bytes(net_io.bytes_recv)

            net_text = f"[bold #42be65]Traffic[/]\n"
            net_text += f"[#3ddbd9]▼[/] [#ffffff]{recv_rate_str:>12}/s[/]  [#6272a4]total:[/] [#ffffff]{total_recv_str:>12}[/]\n"
            net_text += f"[#82cfff]▲[/] [#ffffff]{sent_rate_str:>12}/s[/]  [#6272a4]total:[/] [#ffffff]{total_sent_str:>12}[/]\n"
            net_text += f"[#6272a4]packets:[/] [#82cfff]↓[/][#ffffff]{net_io.packets_recv:,}[/] [#82cfff]↑[/][#ffffff]{net_io.packets_sent:,}[/]"

            self.query_one("#network-stats", Static).update(net_text)

            net_if_stats = psutil.net_if_stats()
            net_if_addrs = psutil.net_if_addrs()
            net_if_io = psutil.net_io_counters(pernic=True)

            interfaces_text = "\n[bold #be95ff]Interfaces[/]\n"
            for iface, stats in net_if_stats.items():
                if iface == "lo":
                    continue

                status = "[#42be65]●[/]" if stats.isup else "[#ee5396]●[/]"
                speed = f"{stats.speed} Mbps" if stats.speed > 0 else "N/A"

                ip_addr = "no address"
                if iface in net_if_addrs:
                    for addr in net_if_addrs[iface]:
                        if addr.family == 2:
                            ip_addr = addr.address
                            break

                io_info = ""
                if iface in net_if_io:
                    io = net_if_io[iface]
                    sent = self._format_bytes(io.bytes_sent)
                    recv = self._format_bytes(io.bytes_recv)
                    io_info = f"[#6272a4]tx:[/][#ffffff]{sent:>10}[/] [#6272a4]rx:[/][#ffffff]{recv:>10}[/]"

                interfaces_text += f"{status} [#82cfff]{iface:12}[/] [#ffffff]{ip_addr:15}[/] [#6272a4]{speed:12}[/] {io_info}\n"

            self.query_one("#network-interfaces", Static).update(interfaces_text.rstrip())

        except Exception as e:
            self.query_one("#network-stats", Static).update(f"[#ee5396]Error: {e}[/]")

    def _format_bytes(self, bytes_val: float) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:6.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:6.2f} PB"

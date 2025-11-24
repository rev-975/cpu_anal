# data models for the application

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    # represents a user in the system
    user: str
    pass_hash: str
    is_admin: bool
    id: Optional[int] = None
    # granular permissions
    can_view_cpu: bool = True
    can_view_memory: bool = False
    can_view_processes: bool = True
    can_view_network: bool = True
    can_kill_processes: bool = False
    can_manage_users: bool = False


@dataclass
class ProcInfo:
    # represents a system process
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    user: str


@dataclass
class SystemStats:
    # sys stats``
    cpu_percent: float
    cpu_per_core: list[float]
    cpu_freq_current: float
    cpu_freq_min: float
    cpu_freq_max: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    swap_percent: float
    swap_used_gb: float
    swap_total_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int

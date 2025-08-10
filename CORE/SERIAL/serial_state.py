from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional, Union


class SerialState:
    """
    用于记录串口设备的最近一次状态
    """

    _values: Dict[str, Any] = {}

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls._values[key] = value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._values.get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        return dict(cls._values)

    @classmethod
    def clear(cls) -> None:
        cls._values.clear()


class SerialHistory:
    """
    用于记录每个信号的历史变化，如电压、电流、功率等。
    """

    _history: Dict[str, deque] = {}
    _maxlen: int = 200
    _recent_log: deque = deque(maxlen=_maxlen)
    
    @classmethod
    def append_log(cls, log_content: str) -> None:
        cls._recent_log.append(log_content)

    @classmethod
    def append_data(cls, name: str, value: float, ts: Optional[datetime] = None) -> None:
        if ts is None:
            ts = datetime.now()
        if name not in cls._history:
            cls._history[name] = deque(maxlen=cls._maxlen)
        cls._history[name].append((ts, value))

    @classmethod
    def get(cls, name: str) -> List[Tuple[datetime, float]]:
        return list(cls._history.get(name, []))

    @classmethod
    def get_latest(cls, name: str) -> Optional[float]:
        if name in cls._history and cls._history[name]:
            return cls._history[name][-1][1]
        return None

    @classmethod
    def get_all(cls) -> Dict[str, List[Tuple[datetime, float]]]:
        return {k: list(v) for k, v in cls._history.items()}

    @classmethod
    def clear(cls) -> None:
        cls._history.clear()


class SerialLogs:
    """
    用于记录串口接收到的日志。每条记录包括时间戳、原始内容、解析内容。
    """

    _logs: deque = deque(maxlen=50)

    @classmethod
    def log_line(cls, origin: Union[str, bytes], parsed: Union[str, Dict, None]) -> None:
        cls._logs.append({
            "timestamp": datetime.now(),
            "origin_content": origin.decode(errors="ignore") if isinstance(origin, bytes) else origin,
            "parsed_content": parsed,
        })

    @classmethod
    def get_recent(cls, n: int = 3) -> List[Dict[str, Any]]:
        return list(cls._logs)[-n:]

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        return list(cls._logs)

    @classmethod
    def clear(cls) -> None:
        cls._logs.clear()


# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================数据类==============================================================================    
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  





# ===============================================================================================================================================================
# ===============================================================================================================================================================
# ===========================================================================数据类==============================================================================    
# ===============================================================================================================================================================     
# ===============================================================================================================================================================  


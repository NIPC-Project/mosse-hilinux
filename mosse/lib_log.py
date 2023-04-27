import inspect
import time
import pathlib


class PythonLogger:
    def _GetFileInfo(self) -> str:
        callerframerecord = inspect.stack()[2]  # 1 represents line at caller
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        return (
            f"{pathlib.PurePath(info.filename).name}({info.lineno}).{info.function}()"
        )

    def __init__(self, title: str = "log", label: str = ""):
        print(f"[{title}]\t{self._GetFileInfo()}\n\t{label}")


# NOTE: Time measured is not accurate... It seems that `_GetFileInfo` waste lots of time...
# If you want to measure time in a more accurate way or you want to optimize the program somewhere, use C instead.
class PythonTimer:
    def __init__(self, label: str = "") -> None:
        self.start_time = time.time()
        self.label = label

    def _GetFileInfo(self) -> str:
        callerframerecord = inspect.stack()[2]  # 1 represents line at caller
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        return (
            f"{pathlib.PurePath(info.filename).name}({info.lineno}).{info.function}()"
        )

    def Start(self, label: str = ""):
        self.start_time = time.time()
        self.label = label

    def Display(self, label: str = ""):
        if self.label == "" and label == "":
            info = ""
        elif self.label != "" and label != "":
            info = f" {self.label} - {label}"
        elif self.label != "":
            info = f" {self.label}"
        elif label != "":
            info = f" {label}"

        print(
            f"[time]\t{self._GetFileInfo()}\n\t{info} {(time.time() - self.start_time) * 1000 :.2f} ms"
        )

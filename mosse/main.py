import lib_nipc_fpga
from lib_log import PythonLogger


def float2bytes(value: float, fixed_num: int, int_num: int = 32) -> bytes:
    return int(value * (2**fixed_num)).to_bytes(
        int_num // 8, byteorder="little", signed=True
    )


def bytes2float(value: bytes, fixed_num: int) -> float:
    return int.from_bytes(bytes=value, byteorder="little", signed=True) / (
        2**fixed_num
    )


x, y, w, h = [257, 163, 57, 36]
xc = int(x + w / 2)
yc = int(y + h / 2)

nipc_fpga = lib_nipc_fpga.NipcFpga()

if __name__ == "__main__":
    # [init]

    nipc_fpga.Reset()
    nipc_fpga.WriteRegisterRW(index=1, value=0)
    nipc_fpga.WriteRegisterRW(index=2, value=xc + yc * 2**16)
    with open("frames/1.bin", "rb") as f:
        frame_init = f.read()
        PythonLogger("debug", f"{len(frame_init)=}")
    nipc_fpga.WriteMemory(data=bytes(frame_init))
    nipc_fpga.WaitProcessDone()

    # [update]

    # TODO 目前只使用前 16 张图片
    # frame_count = 374
    frame_count = 16
    for i in range(2, frame_count + 1):
        nipc_fpga.Reset()
        nipc_fpga.WriteRegisterRW(index=1, value=1)
        with open("frames/1.bin", "rb") as f:
            frame = f.read()
            PythonLogger("debug", f"{len(frame)=}")
        nipc_fpga.WriteMemory(data=bytes(frame))
        nipc_fpga.WaitProcessDone()
        result = nipc_fpga.ReadRegisterR(index=1)
        xc = result % 2**16
        yc = result // 2**16
        PythonLogger("result", f"({xc=}, {yc=})")

    # [quit]

    nipc_fpga.Quit()

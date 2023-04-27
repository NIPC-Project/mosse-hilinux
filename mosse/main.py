import lib_nipc_fpga
from lib_log import PythonLogger

frame_count = 374

x, y, w, h = [257, 163, 57, 36]
xc: float = x + w / 2  # 285.5
yc: float = y + h / 2  # 181

if __name__ == "__main__":
    nipc_fpga = lib_nipc_fpga.NipcFpga()

    result: list[list[int]] = [[int(xc), int(yc)]]

    # [init]

    nipc_fpga.Reset()
    nipc_fpga.WriteRegisterRW(index=1, value=0)
    nipc_fpga.WriteRegisterRW(index=2, value=int(xc * 2 + yc * 2 * 2**16))
    with open("frames/1.bin", "rb") as f:
        frame_init = f.read()
    nipc_fpga.WriteMemory(data=bytes(frame_init))
    nipc_fpga.WaitProcessDone()

    # [update]

    for i in range(2, frame_count + 1):
        # input("to continue, press enter:\n")
        nipc_fpga.Reset()
        nipc_fpga.WriteRegisterRW(index=1, value=1)
        nipc_fpga.WriteRegisterRW(index=2, value=int(xc * 2 + yc * 2 * 2**16))
        with open(f"frames/{i}.bin", "rb") as f:
            # with open(f"frames/1.bin", "rb") as f:
            frame = f.read()
        nipc_fpga.WriteMemory(data=bytes(frame))
        nipc_fpga.WaitProcessDone()
        ycxc = nipc_fpga.ReadRegisterR(index=1)
        xc = (ycxc % 2**16) / 2
        yc = (ycxc // 2**16) / 2
        PythonLogger("result", f"({xc=}, {yc=})")
        result.append([int(xc), int(yc)])

    # [quit]

    with open("result.py", "w") as f:
        f.write(f"result = {result}\n")

    nipc_fpga.Quit()

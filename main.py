import lib_nipc_fpga
from lib_log import PythonLogger


series_name = "car"  # car, cup

if series_name == "car":
    frame_count = 374
    frame_size = [320, 240]
    frame_rate = 30
    x, y, w, h = [257.0, 163.0, 57.0, 36.0]
elif series_name == "cup":
    frame_count = 303
    frame_size = [320, 240]
    frame_rate = 30
    x, y, w, h = [124.67, 92.308, 46.73, 58.572]

xc2 = int((x + w / 2) * 2)
yc2 = int((y + h / 2) * 2)
result: list[list[int]] = [[xc2, yc2]]

nipc_fpga = lib_nipc_fpga.NipcFpga()

# [init]

nipc_fpga.Reset()
nipc_fpga.WriteRegisterRW(index=1, value=0)
nipc_fpga.WriteRegisterRW(index=2, value=xc2 + yc2 * 2**16)
with open(f"frames-graybin/{series_name}/1.bin", "rb") as f:
    frame_init = f.read()
nipc_fpga.WriteMemory(data=bytes(frame_init))
nipc_fpga.WaitProcessDone()

# [update]

for i in range(2, frame_count + 1):
    # input("to continue, press enter:\n")
    nipc_fpga.Reset()
    nipc_fpga.WriteRegisterRW(index=1, value=1)
    nipc_fpga.WriteRegisterRW(index=2, value=xc2 + yc2 * 2**16)
    with open(f"frames-graybin/{series_name}/{i}.bin", "rb") as f:
        frame = f.read()
    nipc_fpga.WriteMemory(data=bytes(frame))
    nipc_fpga.WaitProcessDone()
    yc2xc2 = nipc_fpga.ReadRegisterR(index=1)
    xc2 = yc2xc2 % 2**16
    yc2 = yc2xc2 // 2**16
    print(f"{i}\t({xc2/2=}, {yc2/2=})")
    result.append([xc2, yc2])

# [quit]

print(f"{result=}")

nipc_fpga.Quit()

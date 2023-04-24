import lib_nipc_fpga
import lib_parameters
from lib_log import PythonLogger


def float2bytes(value: float, fixed_num: int, int_num: int = 32) -> bytes:
    return int(value * (2**fixed_num)).to_bytes(
        int_num // 8, byteorder="little", signed=True
    )


def bytes2float(value: bytes, fixed_num: int) -> float:
    return int.from_bytes(bytes=value, byteorder="little", signed=True) / (
        2**fixed_num
    )


if __name__ == "__main__":
    x, y, w, h = [257, 163, 57, 36]
    xc = int(x + w / 2)
    yc = int(y + h / 2)

    with open("1.bin", "rb") as f:
        test_data = f.read()
        PythonLogger("debug", f"{len(test_data)=}")

    nipc_fpga = lib_nipc_fpga.NipcFpga()
    nipc_fpga.Reset()

    nipc_fpga.WriteRegisterDin(index=0, value=xc)
    nipc_fpga.WriteRegisterDin(index=1, value=yc)
    nipc_fpga.WriteMemory(data=bytes(test_data))

    nipc_fpga.WaitProcessDone()
    return_data = nipc_fpga.ReadMemory(size=lib_parameters.FPGA_TRANSMIT_BUFFER_SIZE)
    PythonLogger("debug", f"{len(return_data)=}")

    start = 0
    end = 32
    for i in range(start, end):
        re = bytes2float(value=return_data[i * 8 + 0 : i * 8 + 4], fixed_num=16)
        im = bytes2float(value=return_data[i * 8 + 4 : i * 8 + 8], fixed_num=16)
        print(f"{re + im * 1j:.3f}")

    nipc_fpga.Quit()

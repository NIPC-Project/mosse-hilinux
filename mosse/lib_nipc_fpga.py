import ctypes
import time
import sys

import lib_parameters
from lib_log import PythonLogger, PythonTimer


class NipcFpga:
    class FpgaInfo(ctypes.Structure):
        class Fpga(ctypes.Structure):
            _fields_ = [
                ("vendor", ctypes.c_uint16),
                ("device", ctypes.c_uint16),
                ("boardId", ctypes.c_int32),
            ]

        _fields_ = [("boardNum", ctypes.c_int32), ("boards", Fpga * 8)]

    # [Initialization]

    def __init__(self):
        self.pcieFd: int = -1
        self.pcieSharedMemoryPointer = ctypes.c_void_p(0)
        self.clib = ctypes.cdll.LoadLibrary("./xdma.so")

        self._OpenFpga()
        self._AllocSharedMemory()

    def _OpenFpga(self):
        # [获取板卡信息]
        pcieBoardsInfo = NipcFpga.FpgaInfo()
        self.clib.XPcie_GetBoardListInfo(ctypes.byref(pcieBoardsInfo))
        if pcieBoardsInfo.boardNum == 0:
            PythonLogger("error", "没有发现板卡")
            exit(-1)
        PythonLogger(
            "log",
            f"连接到板卡 boardId={pcieBoardsInfo.boards[0].boardId} vendor={pcieBoardsInfo.boards[0].vendor} device={pcieBoardsInfo.boards[0].device}",
        )
        # [打开板卡]
        # 0 在这里应该是没有意义的
        self.pcieFd = self.clib.XPcie_Device_Open(ctypes.c_int32(0))
        if self.pcieFd < 0:
            PythonLogger("error", "打开板卡失败")
            self.Quit()
        PythonLogger("log", "打开板卡成功")

    def _AllocSharedMemory(self):
        # [申请共享内存]
        PythonLogger("log", "开始申请共享内存")
        _return_value = self.clib._aligned_malloc(
            ctypes.byref(self.pcieSharedMemoryPointer),
            ctypes.c_uint32(lib_parameters.SHARED_MEMORY_SIZE),
        )
        if _return_value < 0:
            PythonLogger("error", "申请共享内存失败")
            exit(-1)
        memory_default_value = 0x55
        ctypes.memset(
            self.pcieSharedMemoryPointer,
            memory_default_value,
            lib_parameters.SHARED_MEMORY_SIZE,
        )
        PythonLogger("log", f"成功申请 {lib_parameters.SHARED_MEMORY_SIZE}B 共享内存且全部置零")

    # [AxiLite]

    def _WriteRegister(self, address: int, value: int):
        _return_value = self.clib.XPcie_Write_Reg(
            ctypes.c_int32(self.pcieFd),
            ctypes.c_long(address),
            ctypes.c_uint32(value),
        )
        if _return_value == -1:
            PythonLogger("error", "写寄存器失败")
            self.Quit()
        else:
            # PythonLogger("debug", "写寄存器成功")
            return

    def _ReadRegister(self, address: int) -> int:
        value = self.clib.XPcie_Read_Reg(
            ctypes.c_int32(self.pcieFd), ctypes.c_long(address)
        )
        if value == -1:
            PythonLogger("error", "读寄存器失败（也可能没失败因为确实运算之后是-1）")
            self.Quit()
        else:
            # PythonLogger("debug", "读寄存器成功")
            return value

    def _WriteRegisterRW(self, index: int, value: int):
        address = index * 0x04
        self._WriteRegister(address=address, value=value)

    def _ReadRegisterRW(self, index: int) -> int:
        address = index * 0x04
        return self._ReadRegister(address=address)

    def _ReadRegisterR(self, index: int) -> int:
        address = (lib_parameters.AXI_REG_RW_NUM + index) * 0x04
        return self._ReadRegister(address=address)

    # [AxiLite API]

    def Reset(self):
        # [初始化板卡]
        self.clib.XPcie_Reset_Device(self.pcieFd)
        PythonLogger("log", "板卡初始化成功")
        self._WriteRegisterRW(index=0, value=1)  # `usr_rst` postedge
        time.sleep(0.001)
        self._WriteRegisterRW(index=0, value=0)  # reset `usr_rst` to 0

    def StartProcess(self):
        self._WriteRegisterRW(index=1, value=1)

    def WaitProcessDone(self):
        PythonLogger("log", "开始轮询 FPGA 寄存器等待算法结束")
        while True:
            # [检查FPGA算法处理是否结束]
            _return_value = self._ReadRegisterR(index=0)
            if _return_value == 0x1:
                PythonLogger("log", "FPGA 算法结束")
                break
            else:
                PythonLogger("log", "FPGA 算法未结束  继续等待")
                time.sleep(0.1)  # TODO 轮询时间 可以调整得更小

    def WriteRegisterDin(self, index: int, value: int):
        address = (index + lib_parameters.AXI_REG_RW_SIGNAL_NUM) * 0x04
        self._WriteRegister(address=address, value=value)

    def ReadRegisterDin(self, index: int) -> int:
        address = (index + lib_parameters.AXI_REG_RW_SIGNAL_NUM) * 0x04
        return self._ReadRegister(address=address)

    def ReadRegisterDout(self, index: int) -> int:
        address = (
            lib_parameters.AXI_REG_RW_NUM + lib_parameters.AXI_REG_R_SIGNAL_NUM + index
        ) * 0x04
        return self._ReadRegister(address=address)

    # [AxiMM]

    def WriteMemory(self, data: bytes, address: int = 0x00):
        # bytes object will be converted to a pointer automatically
        ctypes.memmove(self.pcieSharedMemoryPointer, data, len(data))
        PythonLogger(
            "debug",
            f"向 FPGA 发送 {len(data)}B 的数据 ({list(data[:8])} ... {list(data[-8:])})",
        )

        # int XPcie_DMA_Write(int fd, uint32_t addr, char *buffer, size_t size);
        _return_value = self.clib.XPcie_DMA_Write(
            ctypes.c_int32(self.pcieFd),
            ctypes.c_uint32(address),
            self.pcieSharedMemoryPointer,
            ctypes.c_uint32(len(data)),
        )
        if _return_value < 0:
            PythonLogger("error", "写 FPGA 内存失败")
            self.Quit()
        PythonLogger("log", "写 FPGA 内存成功")

    def ReadMemory(self, size: int, address: int = 0x00) -> bytes:
        # int XPcie_DMA_Read(int fd, uint32_t addr, char *buffer, size_t size);
        self.clib.XPcie_DMA_Read(
            ctypes.c_int32(self.pcieFd),
            ctypes.c_int32(address),
            self.pcieSharedMemoryPointer,
            ctypes.c_uint32(size),
        )

        # 这里 `ctypes.c_char` 后面的 `*` 后面的长度必须要加括号  否则长度为最后一个乘数
        dataFromFpga = (ctypes.c_char * size).from_address(
            self.pcieSharedMemoryPointer.value
        )
        PythonLogger(
            "debug",
            f"从 FPGA 接收到 {len(dataFromFpga)}B 的数据 ({list(dataFromFpga[:8])} ... {list(dataFromFpga[-8:])})",
        )
        return bytes(dataFromFpga)

    # [Quit]

    def Quit(self):
        PythonLogger("log", "开始退出")
        if self.pcieSharedMemoryPointer != None:
            self.clib._aligned_free(self.pcieSharedMemoryPointer)
        self.clib.XPcie_Device_Close(self.pcieFd)
        PythonLogger("log", "板卡已关闭  程序退出")
        sys.exit(0)

    # [Debug]

    def PrintRegisters(self):
        regs_rw: list[int] = []
        regs_r: list[int] = []
        for i in range(lib_parameters.AXI_REG_RW_NUM):
            regs_rw.append(self._ReadRegisterRW(i))
        for i in range(lib_parameters.AXI_REG_R_NUM):
            regs_r.append(self._ReadRegisterR(i))
        PythonLogger("debug", f"registers {regs_rw=} {regs_r=}")

    def PrintRegistersData(self):
        regs_din: list[int] = []
        regs_dout: list[int] = []
        for i in range(lib_parameters.AXI_REG_RW_DIN_NUM):
            regs_din.append(self.ReadRegisterDin(i))
        for i in range(lib_parameters.AXI_REG_R_DOUT_NUM):
            regs_dout.append(self.ReadRegisterDout(i))
        PythonLogger("debug", f"registers {regs_din=} {regs_dout=}")

# [Debug]

RANDOM_DATA = True

# [AxiLite]

AXI_REG_RW_NUM = 3
AXI_REG_R_NUM = 2

# [AxiMM]

# 数据缓冲区大小  需要是 8 B 的整数倍  因为 axi 传输一次是 64 bit
FPGA_RECEIVE_BUFFER_SIZE = 320 * 240 * 32 // 8  # 单位 Byte
# TODO 接受 buffer 后续可以改为 0
FPGA_TRANSMIT_BUFFER_SIZE = 32 * 32 * 64 // 8  # 单位 Byte
# 共享内存取发送和接收的最大值
SHARED_MEMORY_SIZE = max(FPGA_RECEIVE_BUFFER_SIZE, FPGA_TRANSMIT_BUFFER_SIZE)  # 单位 Byte

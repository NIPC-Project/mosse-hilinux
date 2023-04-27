# [Debug]

RANDOM_DATA = True

# [AxiLite]

AXI_REG_RW_NUM = 3
AXI_REG_R_NUM = 2

# [AxiMM]

# 发送一个 frame 320x240x8bit
FPGA_RECEIVE_BUFFER_SIZE = 320 * 240 * 8 // 8  # 单位 Byte
# 不需要接收数据
FPGA_TRANSMIT_BUFFER_SIZE = 0 // 8  # 单位 Byte
# 共享内存取发送和接收的最大值
SHARED_MEMORY_SIZE = max(FPGA_RECEIVE_BUFFER_SIZE, FPGA_TRANSMIT_BUFFER_SIZE)  # 单位 Byte

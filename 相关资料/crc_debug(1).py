import argparse
import enum
import struct
import os
import numpy as np

class ConfigurationPacket:
    @enum.unique
    class Address(enum.Enum):
        CRC = 0
        FAR = 1
        FDRI = 2
        FDRO = 3
        CMD = 4
        CTL0 = 5
        MASK = 6
        STAT = 7
        LOUT = 8
        COR0 = 9
        MFWR = 10
        CBC = 11
        IDCODE = 12 
        AXSS = 13
        COR1 = 14
        UNKNOWN_15 = 15 #if write, csob_reg(ib) <= packet, csbo_cnt(ib) <= word count, csbo_flag(ib) < '1'
        WBSTAR = 16
        TIMER = 17
        UNKNOWN_18 = 18
        POST_CRC = 19 #Undocumented in UG470
        UNKNOWN_20 = 20
        UNKNOWN_21 = 21
        BOOTSTS = 22
        CTL1 = 24
        UNKNOWN_30 = 30 #if next packet is Type2 and bcout_cnt(ib) = 0, set bocut_flag(ib) <= '1' and bout_cnt(ib) <= word count
        BSPI = 31
        
    @enum.unique
    class OpCode(enum.Enum):
        NOOP = 0
        READ = 1
        WRITE = 2
    
    def __init__(self,b,packet=None):
        word = struct.unpack('>I',b[0:4])[0]
        self.type = word >> 29 
        self.opcode = self.OpCode((word >> 27) & 0x3)
        if self.type == 1:
            # address拿到的参与crc的内容
            self.address = self.Address((word >> 13) & 0x1F)
            word_count = word & 0x7FF
        elif self.type == 2:
            if packet is None:
                raise Exception(f'Type 2 packet require previous packet')
            if packet.type != 1:
                raise Exception(f'Type 2 packet require previous Type 1 packet')
            self.address = packet.address
            word_count = word & 0x07FFFFFF
        else:
            raise Exception(f'Unsupported Packet Type {self.type}')
        self.data = []
        b = b[4:]
        for p in [b[i:i+4] for i in range(0,word_count*4,4)]:
            #print(p)
            self.data.append(struct.unpack('>I',p)[0])
    
    def crc(self,crc):
        if self.opcode != self.OpCode.WRITE:
            return crc
        if self.address == self.Address.CMD and self.data[0] & 0x1F == 7: #RCRC
            return 0
        if self.address in [self.Address.UNKNOWN_15,self.Address.UNKNOWN_18,self.Address.UNKNOWN_20,self.Address.UNKNOWN_21,self.Address.BOOTSTS,self.Address.CRC]:
            if self.address == self.Address.CRC: #Cleared when checked
                return 0
            return crc
        for data in self.data:
            crc = icap_crc(self.address.value,data,crc)
            # print('------------------0x%08d,0x%s,crc = 0x%s' % (self.address.value, hex(data)[2:], hex(int(crc, 2))[2:]))
        else :
            return crc
        
    @property
    def header(self):
        return '<0x{:08X}>:Type{},OpCode:{}{},Word Count:{}'.format(
            (self.type << 29) | (self.opcode.value << 27) | ((self.Address.value << 13) if self.type == 1 else 0) | len(self.data),
            self.type,
            self.opcode.name,
            ', address:{}'.format(self.Address.name) if self.type == 1 else '',
            len(self.data)
    )
        
def reflect_bits(data, num_bits):
    reflected = 0
    for i in range(num_bits):
        if data & (1 << i):
            reflected |= 1 << (num_bits - 1 - i)
    reflected = bin(reflected)[2:]
    while len(reflected) != num_bits:
        reflected = '0' + reflected	
    return reflected

    
def icap_crc(addr,data,crc):
    crc_data_new = [0] * 32  # 初始化长度为 32 的列表
    crc_data_in = (addr << 32) | data
    # 将传入的数据完全反转，并转成整形列表
    crc_data_in = reflect_bits(crc_data_in,37)
    crc_data_in = [int(bit) for bit in crc_data_in]
    # 初始化长度为 32 的列表，用来存储crc的当前值
    # 将整数 crc 转换为 32 位的二进制字符串
    crc_int = int(crc, 2)  # 将二进制字符串转换为整数
    crc_bin_string = f'{crc_int:032b}'  # 将整数转换为 32 位二进制字符串
    crc_data_now = [int(bit) for bit in crc_bin_string]  
    crc_data_new[0] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[13]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[24]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[36]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[11]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[7]);
    crc_data_new[1] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[12]^crc_data_in[14]^crc_data_in[17]^crc_data_in[18]^crc_data_in[19]^crc_data_in[23]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[31]^crc_data_in[35]^crc_data_in[4]^crc_data_in[5]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[12]^crc_data_now[13]^crc_data_now[14]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[21]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[26]^crc_data_now[27]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[8]);
    crc_data_new[2] =   (crc_data_in[11]^crc_data_in[13]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[22]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[34]^crc_data_in[3]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[28]^crc_data_now[2]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[9]);
    crc_data_new[3] =   (crc_data_in[10]^crc_data_in[12]^crc_data_in[15]^crc_data_in[16]^crc_data_in[17]^crc_data_in[21]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[33]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_now[10]^crc_data_now[14]^crc_data_now[15]^crc_data_now[16]^crc_data_now[19]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[29]^crc_data_now[2]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]);
    crc_data_new[4] =   (crc_data_in[11]^crc_data_in[14]^crc_data_in[15]^crc_data_in[16]^crc_data_in[1]^crc_data_in[20]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[2]^crc_data_in[32]^crc_data_in[4]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[11]^crc_data_now[15]^crc_data_now[16]^crc_data_now[17]^crc_data_now[20]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[27]^crc_data_now[29]^crc_data_now[30]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]);
    crc_data_new[5] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[13]^crc_data_in[14]^crc_data_in[15]^crc_data_in[19]^crc_data_in[1]^crc_data_in[22]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[31]^crc_data_in[3]^crc_data_in[4]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_now[0]^crc_data_now[12]^crc_data_now[16]^crc_data_now[17]^crc_data_now[18]^crc_data_now[21]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[27]^crc_data_now[28]^crc_data_now[30]^crc_data_now[31]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]^crc_data_now[9]);
    crc_data_new[6] =   (crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[15]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[23]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[31]^crc_data_in[32]^crc_data_in[36]^crc_data_in[3]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[16]^crc_data_now[17]^crc_data_now[19]^crc_data_now[20]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[28]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[8]^crc_data_now[9]);
    crc_data_new[7] =   (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[13]^crc_data_in[14]^crc_data_in[18]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[35]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[13]^crc_data_now[17]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[29]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[9]);
    crc_data_new[8] =   (crc_data_in[11]^crc_data_in[12]^crc_data_in[15]^crc_data_in[17]^crc_data_in[21]^crc_data_in[23]^crc_data_in[25]^crc_data_in[26]^crc_data_in[28]^crc_data_in[2]^crc_data_in[31]^crc_data_in[32]^crc_data_in[34]^crc_data_in[36]^crc_data_in[4]^crc_data_now[0]^crc_data_now[10]^crc_data_now[14]^crc_data_now[16]^crc_data_now[19]^crc_data_now[20]^crc_data_now[27]^crc_data_now[29]^crc_data_now[3]^crc_data_now[5]^crc_data_now[6]^crc_data_now[8]);
    crc_data_new[9] =   (crc_data_in[0]^crc_data_in[13]^crc_data_in[14]^crc_data_in[15]^crc_data_in[16]^crc_data_in[18]^crc_data_in[19]^crc_data_in[22]^crc_data_in[25]^crc_data_in[28]^crc_data_in[29]^crc_data_in[32]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_in[9]^crc_data_now[12]^crc_data_now[13]^crc_data_now[15]^crc_data_now[16]^crc_data_now[17]^crc_data_now[18]^crc_data_now[22]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[6]^crc_data_now[9]);
    crc_data_new[10] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[17]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[14]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]);
    crc_data_new[11] =  (crc_data_in[15]^crc_data_in[16]^crc_data_in[24]^crc_data_in[27]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_now[0]^crc_data_now[15]^crc_data_now[16]^crc_data_now[1]^crc_data_now[28]^crc_data_now[4]^crc_data_now[7]);
    crc_data_new[12] =  (crc_data_in[14]^crc_data_in[15]^crc_data_in[23]^crc_data_in[26]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_now[0]^crc_data_now[16]^crc_data_now[17]^crc_data_now[1]^crc_data_now[29]^crc_data_now[2]^crc_data_now[5]^crc_data_now[8]);
    crc_data_new[13] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[14]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[20]^crc_data_in[22]^crc_data_in[24]^crc_data_in[25]^crc_data_in[27]^crc_data_in[33]^crc_data_in[34]^crc_data_in[36]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_in[9]^crc_data_now[11]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[17]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[31]^crc_data_now[4]^crc_data_now[6]^crc_data_now[7]^crc_data_now[9]);
    crc_data_new[14] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[14]^crc_data_in[15]^crc_data_in[17]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[23]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[31]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[14]^crc_data_now[16]^crc_data_now[17]^crc_data_now[1]^crc_data_now[20]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[8]);
    crc_data_new[15] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[19]^crc_data_in[20]^crc_data_in[22]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[30]^crc_data_in[32]^crc_data_in[34]^crc_data_in[35]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_now[11]^crc_data_now[12]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[1]^crc_data_now[21]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[9]);
    crc_data_new[16] =  (crc_data_in[12]^crc_data_in[13]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[21]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[31]^crc_data_in[33]^crc_data_in[34]^crc_data_in[4]^crc_data_in[5]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[18]^crc_data_now[19]^crc_data_now[22]^crc_data_now[26]^crc_data_now[27]^crc_data_now[29]^crc_data_now[2]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]);
    crc_data_new[17] =  (crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[17]^crc_data_in[18]^crc_data_in[1]^crc_data_in[20]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[30]^crc_data_in[32]^crc_data_in[33]^crc_data_in[3]^crc_data_in[4]^crc_data_in[8]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[23]^crc_data_now[27]^crc_data_now[28]^crc_data_now[30]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]);
    crc_data_new[18] =  (crc_data_in[15]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[1]^crc_data_in[20]^crc_data_in[22]^crc_data_in[23]^crc_data_in[25]^crc_data_in[26]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[16]^crc_data_now[1]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[29]^crc_data_now[30]^crc_data_now[3]^crc_data_now[5]^crc_data_now[6]^crc_data_now[8]^crc_data_now[9]);
    crc_data_new[19] =  (crc_data_in[10]^crc_data_in[11]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[25]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[27]^crc_data_now[29]^crc_data_now[3]^crc_data_now[6]^crc_data_now[9]);
    crc_data_new[20] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[12]^crc_data_in[16]^crc_data_in[17]^crc_data_in[18]^crc_data_in[21]^crc_data_in[28]^crc_data_in[32]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_now[10]^crc_data_now[13]^crc_data_now[14]^crc_data_now[15]^crc_data_now[19]^crc_data_now[20]^crc_data_now[26]^crc_data_now[28]^crc_data_now[31]^crc_data_now[3]);
    crc_data_new[21] =  (crc_data_in[10]^crc_data_in[11]^crc_data_in[15]^crc_data_in[16]^crc_data_in[17]^crc_data_in[20]^crc_data_in[27]^crc_data_in[2]^crc_data_in[31]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[4]^crc_data_now[0]^crc_data_now[11]^crc_data_now[14]^crc_data_now[15]^crc_data_now[16]^crc_data_now[20]^crc_data_now[21]^crc_data_now[27]^crc_data_now[29]^crc_data_now[4]);
    crc_data_new[22] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[18]^crc_data_in[20]^crc_data_in[24]^crc_data_in[26]^crc_data_in[27]^crc_data_in[28]^crc_data_in[29]^crc_data_in[31]^crc_data_in[33]^crc_data_in[34]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[8]^crc_data_now[0]^crc_data_now[11]^crc_data_now[13]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[20]^crc_data_now[23]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[2]^crc_data_now[31]^crc_data_now[3]^crc_data_now[4]^crc_data_now[5]^crc_data_now[7]);
    crc_data_new[23] =  (crc_data_in[0]^crc_data_in[11]^crc_data_in[12]^crc_data_in[17]^crc_data_in[18]^crc_data_in[1]^crc_data_in[20]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[26]^crc_data_in[29]^crc_data_in[2]^crc_data_in[31]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[11]^crc_data_now[13]^crc_data_now[14]^crc_data_now[19]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[27]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[5]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]);
    crc_data_new[24] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[16]^crc_data_in[17]^crc_data_in[19]^crc_data_in[1]^crc_data_in[22]^crc_data_in[23]^crc_data_in[24]^crc_data_in[25]^crc_data_in[28]^crc_data_in[30]^crc_data_in[32]^crc_data_in[34]^crc_data_in[35]^crc_data_in[3]^crc_data_in[5]^crc_data_in[6]^crc_data_in[7]^crc_data_in[8]^crc_data_now[12]^crc_data_now[14]^crc_data_now[15]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[25]^crc_data_now[26]^crc_data_now[28]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[6]^crc_data_now[7]^crc_data_now[8]^crc_data_now[9]);
    crc_data_new[25] =  (crc_data_in[11]^crc_data_in[13]^crc_data_in[16]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[23]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[36]^crc_data_in[4]^crc_data_in[7]^crc_data_in[8]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[15]^crc_data_now[18]^crc_data_now[1]^crc_data_now[20]^crc_data_now[23]^crc_data_now[24]^crc_data_now[27]^crc_data_now[29]^crc_data_now[30]^crc_data_now[3]^crc_data_now[8]^crc_data_now[9]);
    crc_data_new[26] =  (crc_data_in[11]^crc_data_in[12]^crc_data_in[13]^crc_data_in[21]^crc_data_in[22]^crc_data_in[24]^crc_data_in[28]^crc_data_in[30]^crc_data_in[33]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[5]^crc_data_in[7]^crc_data_in[8]^crc_data_in[9]^crc_data_now[10]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[24]^crc_data_now[26]^crc_data_now[28]^crc_data_now[3]^crc_data_now[7]^crc_data_now[9]);
    crc_data_new[27] =  (crc_data_in[0]^crc_data_in[12]^crc_data_in[13]^crc_data_in[15]^crc_data_in[18]^crc_data_in[19]^crc_data_in[1]^crc_data_in[21]^crc_data_in[23]^crc_data_in[24]^crc_data_in[28]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[4]^crc_data_in[5]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[12]^crc_data_now[13]^crc_data_now[16]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[22]^crc_data_now[24]^crc_data_now[26]^crc_data_now[27]^crc_data_now[29]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[7]^crc_data_now[8]);
    crc_data_new[28] =  (crc_data_in[10]^crc_data_in[12]^crc_data_in[13]^crc_data_in[14]^crc_data_in[15]^crc_data_in[17]^crc_data_in[19]^crc_data_in[22]^crc_data_in[23]^crc_data_in[24]^crc_data_in[28]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[36]^crc_data_in[3]^crc_data_in[4]^crc_data_in[5]^crc_data_in[9]^crc_data_now[0]^crc_data_now[12]^crc_data_now[14]^crc_data_now[16]^crc_data_now[17]^crc_data_now[18]^crc_data_now[19]^crc_data_now[21]^crc_data_now[22]^crc_data_now[26]^crc_data_now[27]^crc_data_now[28]^crc_data_now[3]^crc_data_now[7]^crc_data_now[8]^crc_data_now[9]);
    crc_data_new[29] =  (crc_data_in[11]^crc_data_in[12]^crc_data_in[13]^crc_data_in[14]^crc_data_in[16]^crc_data_in[18]^crc_data_in[21]^crc_data_in[22]^crc_data_in[23]^crc_data_in[27]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[35]^crc_data_in[3]^crc_data_in[4]^crc_data_in[8]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[13]^crc_data_now[15]^crc_data_now[17]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[22]^crc_data_now[23]^crc_data_now[27]^crc_data_now[28]^crc_data_now[29]^crc_data_now[4]^crc_data_now[8]^crc_data_now[9]);
    crc_data_new[30] =  (crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[13]^crc_data_in[15]^crc_data_in[17]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[22]^crc_data_in[26]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[34]^crc_data_in[3]^crc_data_in[7]^crc_data_in[8]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[14]^crc_data_now[16]^crc_data_now[18]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[23]^crc_data_now[24]^crc_data_now[28]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[5]^crc_data_now[9]);
    crc_data_new[31] =  (crc_data_in[0]^crc_data_in[10]^crc_data_in[11]^crc_data_in[12]^crc_data_in[14]^crc_data_in[16]^crc_data_in[19]^crc_data_in[1]^crc_data_in[20]^crc_data_in[21]^crc_data_in[25]^crc_data_in[28]^crc_data_in[29]^crc_data_in[2]^crc_data_in[30]^crc_data_in[31]^crc_data_in[32]^crc_data_in[33]^crc_data_in[6]^crc_data_in[7]^crc_data_in[9]^crc_data_now[0]^crc_data_now[10]^crc_data_now[11]^crc_data_now[12]^crc_data_now[15]^crc_data_now[17]^crc_data_now[19]^crc_data_now[1]^crc_data_now[20]^crc_data_now[21]^crc_data_now[22]^crc_data_now[24]^crc_data_now[25]^crc_data_now[29]^crc_data_now[2]^crc_data_now[30]^crc_data_now[31]^crc_data_now[3]^crc_data_now[6]);
    crc = ''.join(str(num) for num in crc_data_new)
    return crc
# 3823600
def crc7series(buffer):
    crc = '00000000000000000000000000000000'
    packet = None
    i = 0
    while(i+4) <= len(buffer):
        # print('i = %4X, CMD = 0X%08X' % (i, struct.unpack('>I', buffer[i:i+4])[0]))
        # if struct.unpack('>I', buffer[i:i+4])[0] == 0x30004000:
        #     print("=================================================")
        packet =  ConfigurationPacket(buffer[i:],packet)
        i += 4*(len(packet.data)+1)
        crc = packet.crc(crc)
    return crc    

file_path = "E:/top1.bit"
os.chmod(file_path, 0o755)  # 设置执行权限
f = open(file_path,'rb+')

# inputfile =  "top_platform_7014_original.bin"
# f = open(inputfile,'rb+')  

buffer = bytearray() #Buffer for storing CRC'd packets
count =0 #Byte-to-word counter
step = 0 #State machine state
b1 = 0
b2 = 0
b3 = 0
b4 = 0

while True:
    # 在码流文件中读取一个字节
    b = f.read(1)
    if(len(b) == 0):
        break
    b4 = b3
    b3 = b2
    b2 = b1
    # 将字节数据 b 解包为一个无符号的 8 位整数
    b1 = struct.unpack('<B',b)[0]
    # 移位拼接操作，让b1时钟保持在低位，b1 2 3 4 拼成一个完成的32位
    w = (b4 << 24) | (b3 << 16) | (b2 << 8) | b1 
    if step == 0: #Scanning for SYNC word
        if w == 0xAA995566:
            step += 1
            print("Step " +str(step)+"Scanning for SYN word")
        continue
    # 以4个字节顺序读取
    else:
        count += 1
        if count < 4:
            continue
        count=0
    if step == 1:  #Scanning for CMD word
        if w == 0x30008001:
            step += 1
        continue
    if step == 2:  #Scanning for CMD word
        if w == 0x00000007:
            step += 1
        else:
            step -= 1
        continue
    
    # 将 w 以大端格式打包成 4 字节并追加到 buffer,>I 无符号整形8位
    buffer += struct.pack('>I',w) #After RCRC,save buffer for CRC generation
    if step == 3 and w >> 29 == 0x2: #Scan for Packet Type2 
        step += 1
        # 0x500e95d8 & 0x07FFFFFF  
        bitsream_len = w & 0x07FFFFFF
        continue
    if step == 4 and w == 0x30000001 and len(buffer) > bitsream_len*4: #Scan for CRC
        step += 1
        # print(len(buffer))
        # print(hex(struct.unpack('>I',buffer[:4])[0])) 
        # print(hex(struct.unpack('>I',buffer[-4:])[0]))
        ccrc = crc7series(buffer[:-4]) #Calculated(should equal expected if CRC ALGORITHM is correct)
        continue
    if step == 5: #Word is checksum
        ecrc = struct.unpack('>I',buffer[-4:])[0] #Expected(from bitstream)
        ccrc = int(ccrc, 2)  # 将二进制字符串转换为整数
        # print('{:08X}:Excepted 0x{:08X},Calculated 0x{:08X}'.format(f.tell()-4,ecrc,ccrc))
        # print('{:08X}；EOF'.format(f.tell()))
        if ccrc == ecrc:
            print("计算成功，输出符合期望！")
            step += 1
            buffer.clear()
        else:
            print("计算失败，输出不符合期望。")
            break
    # 计算下一段的crc校验值
    if step == 6:
        if w == 0x30000001:
            step += 1
            # print(len(buffer))
            # print(hex(struct.unpack('>I',buffer[:4])[0])) 
            # print(hex(struct.unpack('>I',buffer[-4:])[0]))
            ccrc = crc7series(buffer[:-4]) #Calculated(should equal expected if CRC ALGORITHM is correct)
        continue
    if step == 7: #第二段CRC值的计算和校验
        ecrc = struct.unpack('>I',buffer[-4:])[0] #Expected(from bitstream)
        ccrc = int(ccrc, 2)  # 将二进制字符串转换为整数
        # print('{:08X}:Excepted 0x{:08X},Calculated 0x{:08X}'.format(f.tell()-4,ecrc,ccrc))
        # print('{:08X}；EOF'.format(f.tell()))
        f.close() 
        if ccrc == ecrc:
            print("计算成功，输出符合期望！")
            break
        else:
            print("计算失败，输出不符合期望。")
            break
        


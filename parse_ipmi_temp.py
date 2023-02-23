import sys
import datetime
import collections

t1 = datetime.datetime.now()
print(sys.argv[1])

fin = open(sys.argv[1])
fout = open(sys.argv[1] + "_filtered", "w")
line = True
lines = 0
sps = 0
cheats = 0
corrupted_transactions = 0
VRS = [0x60, 0x61, 0x62, 0x63, 0x70, 0x72, 0x74, 0x76, 0x78, 0x7a] # VRs addresses
temp_read_marker = 0
temperature_warnings = 0
warning_temperature = 45
temperature_errors = 0
error_temperature = 60

'''
Generic Completion Codes 00h, C0h-FFh
00h Command Completed Normally
C0h Node Busy. Command could not be processed because command processing resources are temporarily
unavailable.
This Completion Code is returned when Intel® ME is erasing Flash and cannot handle IPMI requests – for
example during firmware update procedure or when processing an Intel® NM configuration update request.
C1h Invalid Command. Used to indicate an unrecognized or unsupported command.
Note: For Net Function = 2Eh – 2Fh for all unrecognized Internet Assigned Numbers Authority* (IANA*)
Enterprise Numbers C1h is returned in response followed by up to 3 bytes containing unrecognized IANA*
Enterprise Number are copied from the original request.
C2h Command invalid for given LUN
C3h Timeout while processing command. Response unavailable.
C4h Out of space. Command could not be completed because of a lack of storage space required to execute the
given command operation.
C5h Reservation Canceled or Invalid Reservation ID
C6h Request data truncated
C7h Request data length invalid
'''
node_busy_code = 0xC0
node_busy_count = 0
invalid_command_code = 0xC1
invalid_command_count = 0
command_invalid_for_given_LUN_code = 0xC2
command_invalid_for_given_LUN_count = 0
timeout_code = 0xC3
timeout_count = 0
out_of_space_code = 0xC4
out_of_space_count = 0
reservation_cancelled_code = 0xC5
reservation_cancelled_count = 0
request_data_truncated_code = 0xC6
request_data_truncated_count = 0
request_data_length_invalid_code = 0xC7
request_data_length_invalid_count = 0
temperature_stats = {}

'''
Byte 1 – Completion code of Get PMBus Readings (0xF5)
=00h – Success (remaining standard completion codes are shown in
Section 2.14.)
=A1h – Illegal Device Index
=A3h – Illegal First Register Offset
=A4h – History snapshot not available
=A5h – Page number not supported
=A6h – Reading not available
'''
illegal_device_index_code = 0xA1
illegal_first_register_offset_code = 0xA3
history_snapshot_not_available_code = 0xA4
page_number_not_supported_code = 0xA5
reading_not_available_code = 0xA6

cc_zero = 0
cc_nonzero = 0
cc_unrecognized = 0
cc_unrecognized_list = []
illegal_device_index_count = 0
illegal_first_register_offset_count = 0
history_snapshot_not_available_count = 0
page_number_not_supported_count = 0
reading_not_available_count = 0

non_int = 0
f_failed = open("failed.txt", "w")  # for failing lines storage
temp_zero = 0
status_zero = 0


while line:
    lines += 1
    line = fin.readline()
    #print(line)
    #fout.write(line)
    
    line_split = line.split(",")
    if len(line_split) >= 9:
        data = line_split[9]
        data_split = data.split(" ")
        #print(data + " | " + str(len(data_split)))
        try:
            fun_lun = int(data_split[0], 16)
            command = int(data_split[4], 16)
            cc = int(data_split[5], 16)
            if 0xBC == fun_lun and 0xF5 == command:
                if 00 == cc:
                    cc_zero += 1
                    status = int(data_split[13], 16) + int(data_split[14], 16) * 256
                    t = int(data_split[15], 16) + int(data_split[16], 16) * 256
                    '''
                    The READ_TEMPERATURE_1 command returns the temperature in °C (Literal Format) of the external sense element. The external temperature, in °C, is calculated from the equation:
                    Temperature1 = TEMP1 * 2^N
                    where:
                        TEMP1 is a 11-bit signed binary integer (read_temperature1[10:0])
                        N is a 5-bit signed binary integer (read_temperature1[15:11])
                    '''
                    TEMP1 = t & 0x7FF
                    N = t >> 11
                    if N != 0:
                        print(line)
                        print("data_split[13]= " + data_split[13] + ", data_split[14]= " + data_split[14] + ", data_split[15]= " + data_split[15] + ", data_split[16]= " + data_split[16])
                    if N >= 16:
                        N = N - 31
                    if N != 0:
                        print("N= " + str(N))
                        t = TEMP1 * 2**N
                        print("temperature= " + str(t) + " (" + str(TEMP1) + ")")
                    if t > 60:
                        print(line)
                        
                    if t < 10:
                        #print(line)
                        print("Temperature= " + str(t) + " (" + str(TEMP1) + ")" + ", status= " + hex(status))
                    if t == 0:
                        temp_zero = temp_zero + 1
                        if status == 0:
                            status_zero = status_zero + 1

                    #print("status= " + hex(status) + ", temperature= " + str(TEMP1))
                    #print("data_split[13]= " + data_split[13] + ", data_split[14]= " + data_split[14] + ", data_split[15]= " + data_split[15] + ", data_split[16]= " + data_split[16])
                    temperature_stats[t] = temperature_stats.get(t, 0) + 1
                else:
                    cc_nonzero += 1
                    if illegal_device_index_code == cc:
                        illegal_device_index_count += 1
                    elif illegal_first_register_offset_code == cc:
                        illegal_first_register_offset_count += 1
                    elif history_snapshot_not_available_code == cc:
                        history_snapshot_not_available_count += 1
                    elif page_number_not_supported_code == cc:
                        page_number_not_supported_count += 1
                    elif reading_not_available_code == cc:
                        reading_not_available_count += 1
                    elif node_busy_code == cc:
                        node_busy_count += 1
                    else:
                        cc_unrecognized += 1
                        cc_unrecognized_list.append(cc)
                #print("[" + line + "], cc= ", str(cc))
        except:
            #print("<" + line + ">")
            non_int += 1
            f_failed.write(line)
            
print("lines= " + str(lines))
print("cc_zero= " + str(cc_zero))
print("cc_nonzero= " + str(cc_nonzero))
print("illegal_device_index_count= " + str(illegal_device_index_count))
print("illegal_first_register_offset_count= " + str(illegal_first_register_offset_count))
print("history_snapshot_not_available_count= " + str(history_snapshot_not_available_count))
print("page_number_not_supported_count= " + str(page_number_not_supported_count))
print("reading_not_available_count= " + str(reading_not_available_count))
print("node_busy_code= " + str(node_busy_code))
print("cc_unrecognized= " + str(cc_unrecognized))
print("cc_unrecognized_list= " + str(cc_unrecognized_list))

print("non_int= " + str(non_int))
print("temp_zero= " + str(temp_zero))
print("status_zero= " + str(status_zero))

print("temperature_stats= " + str(temperature_stats))
# collections.OrderedDict(sorted(d.items()))
print()
print(collections.OrderedDict(sorted(temperature_stats.items())))
f_failed.close()
t2 = datetime.datetime.now()
print(t2-t1)

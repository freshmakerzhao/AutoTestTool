# program.tcl - 二个参数，码流文件路径，flash型号，烧写码流到flash

# Argument check
if {$argc != 2} {
    puts "Usage error: Please provide the path to a .bit or .rbt file"
    exit 1
}

set bitstream_file [lindex $argv 0]
set flash_part [lindex $argv 1]

if {![file exists $bitstream_file]} {
    puts "The specified file does not exist: $bitstream_file"
    exit 1
}

puts "Loading file: $bitstream_file"

# Open hardware manager and connect
open_hw_manager
connect_hw_server
open_hw_target

# Check available devices
set devices [get_hw_devices]
if {[llength $devices] == 0} {
    puts "No hardware devices found. Please check the JTAG connection."
    exit 1
}


create_hw_cfgmem -hw_device $devices [lindex [get_cfgmem_parts $flash_part] 0]
set property [ get_property PROGRAM.HW_CFGMEM $devices]

set_property PROGRAM.ADDRESS_RANGE {use_file} $property

set_property PROGRAM.FILES [list $bitstream_file] $property
set_property PROGRAM.PRM_FILE {} $property
set_property PROGRAM.BPI_RS_PINS {none} $property
set_property PROGRAM.UNUSED_PIN_TERMINATION {pull-none} $property
set_property PROGRAM.EMMC_CLOCK_FREQUENCY  10Mhz $property
set_property PROGRAM.BLANK_CHECK  0 $property

set_property PROGRAM.ERASE  1 $property
set_property PROGRAM.CFG_PROGRAM  1 $property
set_property PROGRAM.VERIFY  0 $property

set_property PROGRAM.CHECKSUM  0 $property
set_property PROGRAM.UNUSED_PIN_TERMINATION  pull-down $property

create_hw_bitstream -hw_device $devices [get_property PROGRAM.HW_CFGMEM_BITFILE $devices] 
program_hw_devices $devices
refresh_hw_device $devices

set re [catch {program_hw_cfgmem -hw_cfgmem [ get_property PROGRAM.HW_CFGMEM $devices]}]
if {$re == 1} {
    exit 1
} else {
    puts "Operation Successful!"
    exit 0
}
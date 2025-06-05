# program.tcl - 一个参数，码流文件路径，烧写码流

# Argument check
if {$argc != 1} {
    puts "Usage error: Please provide the path to a .bit or .rbt file"
    puts "Example: vivado -mode batch -source program_fpga.tcl -tclargs D:/zs_prj/top.bit"
    exit 1
}

set bitstream_file [lindex $argv 0]

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

# Set programming file
set_property PROGRAM.FILE $bitstream_file $devices
set_property PROBES.FILE {} $devices
set_property FULL_PROBES.FILE {} $devices

# Start programming
puts "Programming bitstream to FPGA..."
# ug835 page1208
program_hw_devices $devices -disable_eos_check
refresh_hw_device [lindex $devices 0]

puts "Programming completed!"
exit 0

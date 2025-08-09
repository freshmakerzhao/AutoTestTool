# readback.tcl - Readback bitstream from FPGA via JTAG and save to .rbd

# Argument check
if {$argc != 1} {
    puts "Usage: vivado -mode batch -source readback.tcl -tclargs <output_rbd_file>"
    exit 1
}

set outfile [lindex $argv 0]

puts "Readback output will be saved to: $outfile"

# Open hardware manager and connect
open_hw_manager
connect_hw_server
open_hw_target

set devices [get_hw_devices]

if {[llength $devices] == 0} {
    puts "No hardware device found. Check JTAG connection."
    exit 1
}

set device [lindex $devices 0]
puts "Using device: $device"

puts "Starting readback..."
readback_hw_device $device -readback_file $outfile
puts "Readback completed."

# refresh_hw_device
refresh_hw_device $device
exit 0

# ERROR states
# mask used to communicate errors which occured on device
DEVICE_ERROR_MASK = 0x00FF0000

DEVICE_NO_ERROR = 0x00000000
# this status is result of kill command, which occured
DEVICE_ERROR_KILL = 0x00010000
# unspecified HW error occured
DEVICE_ERROR_HW = 0x00020000
# device not ready..
DEVICE_NOT_READY = 0x00040000

# State change was caused by command being run on current connection.
# Currently only used to signal that the exposure was caused
# by the connection.
#
DEVICE_SC_CURR = 0x00001000

# device need reload when it enter idle state - what should be reload is device specific
DEVICE_NEED_RELOAD = 0x00002000

# device is starting up
DEVICE_STARTUP = 0x00004000

# device is in shutdown
DEVICE_SHUTDOWN = 0x00008000

DEVICE_IDLE = 0x00000000

# Used to deal blocking functions.
# BOP is for Block OPeration. BOP is used mainly in Rts2Command and
# Rts2Value.
BOP_MASK = 0x3F000000

# Block exposures.
BOP_EXPOSURE = 0x01000000

# Block readout of CCD.
BOP_READOUT = 0x02000000

#
# Block telescope movement.
BOP_TEL_MOVE = 0x04000000

# Detector status issued before the detector takes an exposure.
BOP_WILL_EXPOSE = 0x08000000

# Waiting for exposure trigger.
BOP_TRIG_EXPOSE = 0x10000000

# Stop any move - emergency state.
STOP_MASK = 0x40000000

# System can physicaly move devices.
CAN_MOVE = 0x00000000

# Stop any move.
STOP_EVERYTHING = 0x40000000

#
# Mask for device weather voting.
WEATHER_MASK = 0x80000000

# Allow operations as weather is acceptable,
GOOD_WEATHER = 0x00000000

# Block observations because there is bad weather.
BAD_WEATHER = 0x80000000

DEVICE_STATUS_MASK = 0x00000FFF

# Miscelaneous mask.
DEVICE_MISC_MASK = 0x0000F000

#
# State change was caused by command being run on current connection.
# Currently only used to signal that the exposure was caused
# by the connection.
#
DEVICE_SC_CURR = 0x00001000

# device need reload when it enter idle state - what should be reload is device specific
DEVICE_NEED_RELOAD = 0x00002000

# device is starting up
DEVICE_STARTUP = 0x00004000

# device is in shutdown
DEVICE_SHUTDOWN = 0x00008000

DEVICE_IDLE = 0x00000000

# Focuser status
FOC_MASK_FOCUSING = 0x01
FOC_SLEEPING = 0x00
FOC_FOCUSING = 0x01

# Filter status
FILTERD_MASK = 0x02
FILTERD_IDLE = 0x00
FILTERD_MOVE = 0x02

# Camera status
CAM_MASK_CHIP = 0x000F
CAM_MASK_EXPOSE = 0x0001

CAM_NOEXPOSURE = 0x0000
CAM_EXPOSING = 0x0001
CAM_EXPOSING_NOIM = 0x0010

CAM_MASK_READING = 0x0002

CAM_NOTREADING = 0x0000
CAM_READING = 0x0002

CAM_MASK_FT = 0x0004
CAM_FT = 0x0004
CAM_NOFT = 0x0000

CAM_MASK_HAS_IMAGE = 0x0008
CAM_HAS_IMAGE = 0x0008
CAM_HASNOT_IMAGE = 0x0000

CAM_WORKING = CAM_EXPOSING | CAM_READING

CAM_MASK_FOCUSING = 0x0800

CAM_NOFOCUSING = 0x0000
CAM_FOCUSING = 0x0800

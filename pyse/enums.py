from enum import IntEnum


class InverterDeviceType(IntEnum):
    SinglePhase = 101
    SplitPhase = 102
    ThreePhase = 103


class InverterDeviceStatus(IntEnum):
    Unknown = 0
    Off = 1
    Sleeping = 2
    Staring = 3
    MPPT = 4
    Throttled = 5
    ShuttingDown = 6
    Fault = 7
    Standby = 8

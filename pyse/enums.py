from enum import IntEnum, IntFlag


class InverterDeviceType(IntEnum):
    SinglePhase = 101
    SplitPhase = 102
    ThreePhase = 103


class MeterDeviceType(IntEnum):
    SinglePhase = 201
    SplitPhase = 202
    WyeThreePhase = 203
    DeltaThreePhase = 204


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


class MeterEventFlags(IntFlag):
    Power_Failure = 0x00000004
    Under_Voltage = 0x00000008
    Low_PF = 0x00000010
    Over_Current = 0x00000020
    Over_Voltage = 0x00000040
    Missing_Sensor = 0x00000080
    Reserved1 = 0x00000100
    Reserved2 = 0x00000200
    Reserved3 = 0x00000400
    Reserved4 = 0x00000800
    Reserved5 = 0x00001000
    Reserved6 = 0x00002000
    Reserved7 = 0x00004000
    Reserved8 = 0x00008000

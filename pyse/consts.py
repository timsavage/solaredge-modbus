from enum import IntEnum


class CommonAddress(IntEnum):
    SunSpecID = 40_000
    SunSpecDID = 40_002
    SunSpecLength = 40_003
    Manufacturer = 40_004
    Model = 40_020
    Version = 40_044
    SerialNumber = 40_053
    DeviceAddress = 40_068


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


class InverterModelAddress(IntEnum):
    SunSpecDID = 40_069
    SunSpecLength = 40_070
    ACCurrent = 40_071
    ACCurrentA = 40_072
    ACCurrentB = 40_073
    ACCurrentC = 40_074
    ACCurrentScaleFactor = 40_075
    ACVoltageAB = 40_076
    ACVoltageBC = 40_077
    ACVoltageCA = 40_078
    ACVoltageAN = 40_079
    ACVoltageBN = 40_080
    ACVoltageCN = 40_081
    ACVoltageScaleFactor = 40_082
    ACPower = 40_083
    ACPowerSF = 40_084
    ACFrequency = 40_085
    ACFrequencyScaleFactor = 40_086
    ACPowerApparent = 40_087
    ACPowerApparentScaleFactor = 40_088
    ACPowerReactive = 40_089
    ACPowerReactiveScaleFactor = 40_090
    ACPowerFactor = 40_091
    ACPowerFactorScaleFactor = 40_092
    ACEnergyLifetime = 40_093
    ACEnergyLifetimeScaleFactor = 40_095
    DCCurrent = 40_096
    DCCurrentScaleFactor = 40_097
    DCVoltage = 40_098
    DCVoltageScaleFactor = 40_099
    DCPower = 40_100
    DCPowerScaleFactor = 40_101
    HeatSinkTemp = 40_103
    HeatSinkTempScaleFactor = 40_106
    Status = 40_107
    StatusVendor = 40_108

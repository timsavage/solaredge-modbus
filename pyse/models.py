"""Models that"""

import abc
from typing import NamedTuple

from pymodbus.client.base import ModbusBaseSyncClient
from pymodbus.exceptions import ModbusIOException, ModbusException

from pyse.enums import MeterDeviceType, InverterDeviceType, InverterDeviceStatus
from pyse.errors import UnknownDevice


class Phases(NamedTuple):
    a: float
    b: float
    c: float

    @classmethod
    def scaled(cls, a: float | None, b: float | None, c: float | None, scalar: float):
        return cls(
            None if a is None else a * scalar,
            None if b is None else b * scalar,
            None if c is None else c * scalar,
        )


type int16 = int
type uint16 = int
type int32 = int
type uint32 = int
convert = ModbusBaseSyncClient.convert_from_registers
DATATYPE = ModbusBaseSyncClient.DATATYPE

NULL_16 = (65535,)
NULL_32 = (65535, 65535)


class Buffer(list[int]):
    def __init__(self, items):
        super().__init__(items)
        self._idx = 0

    def jump(self, idx: int = 0):
        self._idx = idx

    def _slice(self, length: int) -> list[int]:
        start = self._idx
        self._idx += length
        return self[start : self._idx]

    def undefined(self, size: int):
        self._idx += size

    def int16(self, nullable: bool = False) -> int16:
        if nullable:
            value = self._slice(1)
            return None if value == NULL_16 else convert(value, DATATYPE.INT16)
        else:
            return convert(self._slice(1), DATATYPE.INT16)

    def uint16(self, nullable: bool = False) -> uint16:
        if nullable:
            value = self._slice(1)
            return None if value == NULL_16 else convert(value, DATATYPE.UINT16)
        else:
            return convert(self._slice(1), DATATYPE.UINT16)

    def int16_scalar(self) -> float:
        return pow(10, self.int16())

    def uint16_scalar(self) -> float:
        return pow(10, self.uint16())

    def int32(self) -> int32:
        return convert(self._slice(2), DATATYPE.INT32)

    def uint32(self, nullable: bool = False) -> uint32:
        if nullable:
            value = self._slice(2)
            return None if value == NULL_32 else convert(value, DATATYPE.UINT32)
        else:
            return convert(self._slice(2), DATATYPE.UINT32)

    def string(self, size: int):
        value = convert(self._slice(size), DATATYPE.STRING)
        return value.strip("\x00")

    def int16_sum_and_phases(self) -> tuple[float, Phases]:
        sum_value = self.int16()
        phase_a = self.int16()
        phase_b = self.int16(nullable=True)
        phase_c = self.int16(nullable=True)
        scalar = self.int16_scalar()
        return (
            sum_value * scalar,
            Phases.scaled(phase_a, phase_b, phase_c, scalar),
        )

    def uint16_sum_and_phases(self) -> tuple[float, Phases]:
        sum_value = self.uint16()
        phase_a = self.uint16()
        phase_b = self.uint16(nullable=True)
        phase_c = self.uint16(nullable=True)
        scalar = self.int16_scalar()
        return (
            sum_value * scalar,
            Phases.scaled(phase_a, phase_b, phase_c, scalar),
        )

    def voltage_phases(self) -> tuple[Phases, Phases]:
        phase_ab = self.int16()
        phase_bc = self.int16()
        phase_ca = self.int16()
        phase_an = self.uint16()
        phase_bn = self.uint16(nullable=True)
        phase_cn = self.uint16(nullable=True)
        scalar = self.int16_scalar()
        return (
            Phases(phase_ab * scalar, phase_bc * scalar, phase_ca * scalar),
            Phases.scaled(phase_an, phase_bn, phase_cn, scalar),
        )

    def acc32_import_export(self) -> tuple[float, Phases, float, Phases]:
        import_sum = self.uint32()
        import_phase_a = self.uint32()
        import_phase_b = self.uint32(nullable=True)
        import_phase_c = self.uint32(nullable=True)
        export_sum = self.uint32()
        export_phase_a = self.uint32()
        export_phase_b = self.uint32(nullable=True)
        export_phase_c = self.uint32(nullable=True)
        scalar = self.int16_scalar()
        return (
            import_sum * scalar,
            Phases.scaled(import_phase_a, import_phase_b, import_phase_c, scalar),
            export_sum * scalar,
            Phases.scaled(export_phase_a, export_phase_b, export_phase_c, scalar),
        )


class BaseModel(abc.ABC):
    BASE_ADDRESS: int = 40_000
    HEADER_SIZE: int = 2

    def __init__(
        self, client: ModbusBaseSyncClient, base_address: int = None, unit: int = 1
    ):
        self.client = client
        self._base = base_address or self.BASE_ADDRESS
        self._unit = unit

    @abc.abstractmethod
    def _parse_header(self, buffer: Buffer) -> int:
        """Read header and return length of body."""

    @abc.abstractmethod
    def _parse_body(self, buffer: Buffer):
        """Read body and populate model."""

    def refresh(self):
        """Refresh model."""
        read = self.client.read_holding_registers

        result = read(self._base, self.HEADER_SIZE, self._unit)
        if isinstance(result, ModbusException):
            raise result
        buffer = Buffer(result.registers)
        body_length = self._parse_header(buffer)

        buffer = Buffer(
            read(self._base + self.HEADER_SIZE, body_length, self._unit).registers
        )
        self._parse_body(buffer)


class CommonModel(BaseModel):
    HEADER_SIZE: int = 4

    manufacturer: str
    model: str
    version: str
    serial_number: str
    device_address: uint16

    def __str__(self):
        return f"{self.manufacturer} {self.model} {self.version} - {self.serial_number}"

    def _parse_header(self, buffer: Buffer) -> int:
        if buffer.uint32() != 0x53756E53:
            raise UnknownDevice("Not a valid SunSpec Register Map")
        if buffer.uint16() != 1:
            raise UnknownDevice("Not a Common Model block")
        return buffer.uint16()

    def _parse_body(self, buffer: Buffer):
        self.manufacturer = buffer.string(16)
        self.model = buffer.string(16)
        buffer.undefined(8)
        self.version = buffer.string(8)
        self.serial_number = buffer.string(16)
        self.device_address = buffer.uint16()


class InverterModel(BaseModel):
    BASE_ADDRESS = 40_069
    HEADER_SIZE: int = 2

    did: InverterDeviceType

    ac_current: float
    ac_current_phases: Phases
    ac_voltage_between_phases: Phases
    ac_voltage_phases_to_neutral: Phases
    ac_real_power: float
    ac_frequency: float
    ac_apparent_power: float
    ac_reactive_power: float
    ac_power_factor: float
    ac_energy_lifetime: float

    dc_current: float
    dc_voltage: float
    dc_power: float

    heat_sink_temp: float
    status: InverterDeviceStatus
    status_vendor: uint16

    def __str__(self):
        return "\n".join(
            [
                f"Type:             {self.did.name}",
                f"Status:           {self.status.name}",
                f"Temp:             {self.heat_sink_temp:.2f} °C",
                f"-----------------------------",
                f"AC Current:       {self.ac_current:.2f} A",
                f"AC Voltage:       {self.ac_voltage_phases_to_neutral[0]:.2f} V",
                f"AC Power:         {self.ac_real_power:.2f} W",
                f"AC Freq:          {self.ac_frequency:.2f} Hz",
                f"AC Power Factor:  {self.ac_power_factor:.2f} %",
                f"AC Total:         {self.ac_energy_lifetime/1_000_000:.2f} MWh",
                f"-----------------------------",
                f"DC Current:       {self.dc_current:.2f} A",
                f"DC Voltage:       {self.dc_voltage:.2f} V",
                f"DC Power:         {self.dc_power:.2f} W",
            ]
        )

    def _parse_header(self, buffer: Buffer) -> int:
        self.did = InverterDeviceType(buffer.uint16())
        return buffer.uint16()

    def _parse_body(self, buffer: Buffer):
        self.ac_current, self.ac_current_phases = buffer.uint16_sum_and_phases()
        self.ac_voltage_between_phases, self.ac_voltage_phases_to_neutral = (
            buffer.voltage_phases()
        )
        self.ac_real_power = buffer.int16() * buffer.int16_scalar()
        self.ac_frequency = buffer.uint16() * buffer.int16_scalar()
        self.ac_apparent_power = buffer.int16() * buffer.int16_scalar()
        self.ac_reactive_power = buffer.int16() * buffer.int16_scalar()
        self.ac_power_factor = buffer.int16() * buffer.int16_scalar()
        self.ac_energy_lifetime = buffer.uint32() * buffer.uint16_scalar()

        self.dc_current = buffer.uint16() * buffer.int16_scalar()
        self.dc_voltage = buffer.uint16() * buffer.int16_scalar()
        self.dc_power = buffer.int16() * buffer.int16_scalar()

        buffer.undefined(1)
        temp = buffer.int16()
        buffer.undefined(2)
        self.heat_sink_temp = temp * buffer.int16_scalar()

        self.status = InverterDeviceStatus(buffer.uint16())
        self.status_vendor = buffer.uint16()


class MeterCommonModel(BaseModel):
    HEADER_SIZE: int = 2

    manufacturer: str
    model: str
    option: str
    version: str
    serial_number: str
    device_address: uint16

    @classmethod
    def meter_1(cls, client: ModbusBaseSyncClient):
        return cls(client, 40_121)

    @classmethod
    def meter_2(cls, client: ModbusBaseSyncClient):
        return cls(client, 40_295)

    @classmethod
    def meter_3(cls, client: ModbusBaseSyncClient):
        return cls(client, 40_469)

    def __str__(self):
        return f"{self.manufacturer} {self.model} {self.option} {self.version} - {self.serial_number}"

    def _parse_header(self, buffer: Buffer) -> int:
        if buffer.uint16() != 1:
            raise RuntimeError("Not a meter.")
        return buffer.uint16()

    def _parse_body(self, buffer: Buffer):
        self.manufacturer = buffer.string(16)
        self.model = buffer.string(16)
        self.option = buffer.string(8)
        self.version = buffer.string(8)
        self.serial_number = buffer.string(16)
        self.device_address = buffer.uint16()


class MeterDataModel(BaseModel):
    HEADER_SIZE: int = 2

    type: MeterDeviceType

    ac_current: float
    ac_current_phases: Phases
    # Line to Neutral voltage
    ac_voltage: float
    ac_voltage_phases: Phases
    # Line To Line voltage not supported
    ac_frequency: float
    real_power: float
    real_power_phases: Phases
    apparent_power: float
    apparent_power_phases: Phases
    reactive_power: float
    reactive_power_phases: Phases
    power_factor: float
    power_factor_phases: Phases

    real_exported: float
    real_exported_phases: Phases
    real_imported: float
    real_imported_phases: Phases

    @classmethod
    def meter_1(cls, client: ModbusBaseSyncClient):
        return cls(client, 40_188)

    @classmethod
    def meter_2(cls, client: ModbusBaseSyncClient):
        return cls(client, 40_362)

    @classmethod
    def meter_3(cls, client: ModbusBaseSyncClient):
        return cls(client, 40_537)

    def __init__(self, client: ModbusBaseSyncClient, base_address: int = 40_188):
        super().__init__(client, base_address)

    def __str__(self):
        return "\n".join(
            [
                f"AC Current:         {self.ac_current:.2f} A",
                f"AC Voltage:         {self.ac_voltage:.2f} V",
                f"AC Frequency:       {self.ac_frequency:.2f} Hz",
                f"AC Real Power:      {self.real_power/1000:.2f} kW",
                f"AC Apparent Power:  {self.apparent_power:.2f} VA",
                f"AC Reactive Power:  {self.reactive_power:.2f} VAR",
                f"AC Power Factor:    {self.power_factor:.1f} %",
                "--------------------------------",
                f"Real Exported:      {self.real_exported/1_000_000:.2f} MWh",
                f"Real Imported:      {self.real_imported/1_000_000:.2f} MWh",
            ]
        )

    def _parse_header(self, buffer: Buffer) -> int:
        self.type = MeterDeviceType(buffer.uint16())
        return buffer.uint16()

    def _parse_voltages(self, buffer: Buffer):
        value = buffer.int16()
        phase_a = buffer.int16()
        phase_b = buffer.int16(nullable=True)
        phase_c = buffer.int16(nullable=True)
        buffer.undefined(4)  # Not supported by Solar Edge inverters
        scalar = buffer.int16_scalar()
        self.ac_voltage = value * scalar
        self.ac_voltage_to_neutral = Phases.scaled(phase_a, phase_b, phase_c, scalar)

    def _parse_body(self, buffer: Buffer):
        self.ac_current, self.ac_current_phases = buffer.int16_sum_and_phases()
        self._parse_voltages(buffer)

        self.ac_frequency = buffer.int16() * buffer.int16_scalar()

        self.real_power, self.real_power_phases = buffer.int16_sum_and_phases()
        self.apparent_power, self.apparent_power_phases = buffer.int16_sum_and_phases()
        self.reactive_power, self.reactive_power_phases = buffer.int16_sum_and_phases()
        self.power_factor, self.power_factor_phases = buffer.int16_sum_and_phases()

        (
            self.real_exported,
            self.real_exported_phases,
            self.real_imported,
            self.real_imported_phases,
        ) = buffer.acc32_import_export()

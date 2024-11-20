from pymodbus.client.base import ModbusBaseSyncClient

from pyse.enums import MeterDeviceType

Phases = tuple[float, float, float]

type int16 = int
type uint16 = int
convert = ModbusBaseSyncClient.convert_from_registers
DATATYPE = ModbusBaseSyncClient.DATATYPE


def read_int16(buffer: list[int], offset: int) -> int16:
    return convert(buffer[offset : offset + 1], DATATYPE.INT16)


def read_uint16(buffer: list[int], offset: int) -> uint16:
    return convert(buffer[offset : offset + 1], DATATYPE.UINT16)


def read_uint32(buffer: list[int], offset: int) -> uint16:
    return convert(buffer[offset : offset + 2], DATATYPE.UINT32)


def read_string(buffer: list[int], offset: int, size: int) -> str:
    value = convert(buffer[offset : offset + size], DATATYPE.STRING)
    return value.strip("\x00")


def read_int16_scalar(buffer: list[int], offset: int) -> float:
    return pow(10, read_int16(buffer, offset))


def read_int16_sum_and_phases(buffer: list[int], offset: int) -> tuple[float, Phases]:
    scalar = read_int16_scalar(buffer, offset + 4)
    return (
        read_int16(buffer, offset) * scalar,
        (
            read_int16(buffer, offset + 1) * scalar,
            read_int16(buffer, offset + 2) * scalar,
            read_int16(buffer, offset + 3) * scalar,
        ),
    )


def read_acc32_import_export(
    buffer: list[int], offset: int
) -> tuple[float, Phases, float, Phases]:
    scalar = read_int16_scalar(buffer, offset + 16)
    return (
        read_uint32(buffer, offset) * scalar,
        (
            read_uint32(buffer, offset + 2) * scalar,
            read_uint32(buffer, offset + 4) * scalar,
            read_uint32(buffer, offset + 6) * scalar,
        ),
        read_uint32(buffer, offset + 8) * scalar,
        (
            read_uint32(buffer, offset + 10) * scalar,
            read_uint32(buffer, offset + 12) * scalar,
            read_uint32(buffer, offset + 14) * scalar,
        ),
    )


class BaseModel:
    def __init__(self, client: ModbusBaseSyncClient, base_address: int = 40_000):
        self.client = client
        self._base = base_address
        self.refresh()

    def _read(self, address: int, count: int) -> list[int]:
        return self.client.read_holding_registers(self._base + address, count).registers

    def refresh(self) -> bool:
        raise NotImplementedError()


class MeterCommonModel(BaseModel):
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

    def __init__(self, client: ModbusBaseSyncClient, base_address: int = 40_121):
        super().__init__(client, base_address)

    def __str__(self):
        return f"{self.manufacturer} {self.model} {self.option} {self.version} - {self.serial_number}"

    def refresh(self) -> bool:
        if buffer := self._read_header():
            self.manufacturer = read_string(buffer, 0, 16)
            self.model = read_string(buffer, 16, 16)
            self.option = read_string(buffer, 32, 8)
            self.version = read_string(buffer, 40, 8)
            self.serial_number = read_string(buffer, 48, 16)
            self.device_address = read_uint16(buffer, 64)
            return True
        return False

    def _read_header(self):
        buffer = self._read(0, 2)
        if read_uint16(buffer, 0) != 1:
            raise RuntimeError("Not a meter.")
        if (length := read_uint16(buffer, 1)) != 65:
            return
        return self._read(2, length)


class MeterDataModel(BaseModel):
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
                f"AC Current:         {self.ac_current:.2f}A",
                f"AC Voltage:         {self.ac_voltage:.2f}V",
                f"AC Frequency:       {self.ac_frequency:.2f}Hz",
                f"AC Real Power:      {self.real_power:.2f}W",
                f"AC Apparent Power:  {self.apparent_power:.2f}VA",
                f"AC Reactive Power:  {self.reactive_power:.2f}VAR",
                f"AC Power Factor:    {self.power_factor:.1f}%",
                "--------------------------------",
                f"Real Exported:      {self.real_exported/1_000_000:.2f}MWh",
                f"Real Imported:      {self.real_imported/1_000_000:.2f}MWh",
            ]
        )

    def refresh(self) -> bool:
        if buffer := self._read_header():
            self.ac_current, self.ac_current_phases = read_int16_sum_and_phases(
                buffer, 0
            )

            scalar = read_int16_scalar(buffer, 13)
            self.ac_voltage = read_int16(buffer, 5) * scalar
            self.ac_voltage_phases = (
                read_int16(buffer, 6) * scalar,
                read_int16(buffer, 7) * scalar,
                read_int16(buffer, 8) * scalar,
            )

            self.ac_frequency = read_int16(buffer, 14) * read_int16_scalar(buffer, 15)

            self.real_power, self.real_power_phases = read_int16_sum_and_phases(
                buffer, 16
            )
            self.apparent_power, self.apparent_power_phases = read_int16_sum_and_phases(
                buffer, 21
            )
            self.reactive_power, self.reactive_power_phases = read_int16_sum_and_phases(
                buffer, 26
            )
            self.power_factor, self.power_factor_phases = read_int16_sum_and_phases(
                buffer, 31
            )

            (
                self.real_exported,
                self.real_exported_phases,
                self.real_imported,
                self.real_imported_phases,
            ) = read_acc32_import_export(buffer, 36)

            return True
        return False

    def _read_header(self):
        buffer = self._read(0, 2)
        self.type = MeterDeviceType(read_uint16(buffer, 0))
        length = read_uint16(buffer, 1)
        return self._read(2, length)

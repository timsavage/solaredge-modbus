from pymodbus.client.base import ModbusBaseSyncClient

from .enums import InverterDeviceStatus, InverterDeviceType


DATATYPE = ModbusBaseSyncClient.DATATYPE
type int16 = int
type uint16 = int
type int32 = int
type uint32 = int

MAX_UINT16 = 65535
MAX_INT16 = -0x7FFF


class BaseModel:
    """Common base model."""

    def __init__(self, client: ModbusBaseSyncClient):
        self._client = client
        self.refresh()

    def _read_str(self, address: int, length: int) -> str:
        """Read a string from an address."""
        result = self._client.read_holding_registers(address, length // 2)
        value = self._client.convert_from_registers(result.registers, DATATYPE.STRING)
        return value.strip("\x00")

    def _read_int(
        self, address: int, datatype: DATATYPE, null_value: int | None = None
    ) -> int | None:
        """Read an integer from an address."""
        _, count = datatype.value
        result = self._client.read_holding_registers(address, count)
        value = self._client.convert_from_registers(result.registers, datatype)
        return None if value == null_value else value

    def _read_int16(self, address: int, nullable: bool = False) -> int | None:
        """Read an int16 from an address."""
        return self._read_int(
            address,
            DATATYPE.INT16,
            MAX_INT16 if nullable else None,
        )

    def _read_uint16(self, address: int, nullable: bool = False) -> int | None:
        """Read an uint16 from an address."""
        return self._read_int(
            address,
            DATATYPE.UINT16,
            MAX_INT16 if nullable else None,
        )

    def _read_scaled_int16(
        self, address: int, sf_address: int, nullable: bool = False
    ) -> float | None:
        """Read an uint16 and apply scaling factor."""
        value = self._read_int(
            address,
            DATATYPE.INT16,
            MAX_INT16 if nullable else None,
        )
        if value is None:
            return value
        scale = self._read_int(sf_address, DATATYPE.INT16)
        return value * pow(10, scale)

    def _read_scaled_uint16(
        self, address: int, sf_address: int, nullable: bool = False
    ) -> float | None:
        """Read an uint16 and apply scaling factor."""
        value = self._read_int(
            address,
            DATATYPE.UINT16,
            MAX_UINT16 if nullable else None,
        )
        if value is None:
            return value
        scale = pow(10, self._read_int(sf_address, DATATYPE.INT16))
        return value * scale

    def _read_scaled_acc32(
        self, address: int, sf_address: int, nullable: bool = False
    ) -> float | None:
        """Read an acc32 and apply scaling factor."""
        value = self._read_int(address, DATATYPE.UINT32)
        if value is None:
            return value
        scale = pow(10, self._read_int(sf_address, DATATYPE.UINT16))
        return value * scale

    def _read_multi_scaled_uint16(
        self, addresses: list[int], sf_address: int, nullable: bool = True
    ) -> tuple[float, ...]:
        """Read multiple uint16 and apply scaling factor."""
        null_value = MAX_UINT16 if nullable else None
        scale = pow(10, self._read_int(sf_address, DATATYPE.INT16))
        return tuple(
            None
            if (value := self._read_int(address, DATATYPE.UINT16, null_value)) is None
            else value * scale
            for address in addresses
        )

    def refresh(self):
        pass


class CommonModel(BaseModel):
    sun_spec_id: uint32
    sun_spec_did: uint16
    sun_spec_len: uint16
    manufacturer: str
    model: str
    version: str
    serial_number: str
    device_address: uint16

    def __str__(self):
        return f"{self.manufacturer} {self.model} {self.version} - {self.serial_number}"

    def refresh(self):
        self.sun_spec_id = self._read_int(40_000, DATATYPE.UINT32)
        self.sun_spec_did = self._read_uint16(40_002)
        self.sun_spec_len = self._read_uint16(40_003)
        self.manufacturer = self._read_str(40_004, 32)
        self.model = self._read_str(40_020, 32)
        self.version = self._read_str(40_044, 16)
        self.serial_number = self._read_str(40_052, 32)
        self.device_address = self._read_uint16(40_068)


class InverterModel(BaseModel):
    sun_spec_did: InverterDeviceType
    sun_spec_length: uint16

    ac_current: float
    ac_current_a: float
    ac_current_b: float
    ac_current_c: float

    ac_voltage_ab: float
    ac_voltage_bc: float
    ac_voltage_ca: float
    ac_voltage_an: float
    ac_voltage_bn: float
    ac_voltage_cn: float

    ac_power: float
    ac_frequency: float
    ac_power_apparent: float
    ac_power_reactive: float
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
                f"Type:             {self.sun_spec_did.name}",
                f"Status:           {self.status.name}",
                f"Temp:             {self.heat_sink_temp:.2f}W",
                f"-----------------------------",
                f"AC Current:       {self.ac_current:.2f}A",
                f"AC Voltage:       {self.ac_voltage_an:.2f}V",
                f"AC Power:         {self.ac_power:.2f}W",
                f"AC Freq:          {self.ac_frequency:.2f}Hz",
                f"AC Power Factor:  {self.ac_power_factor:.2f}%",
                f"AC Total:         {self.ac_energy_lifetime}Wh",
                f"-----------------------------",
                f"DC Current:       {self.dc_current:.2f}A",
                f"DC Voltage:       {self.dc_voltage:.2f}V",
                f"DC Power:         {self.dc_power:.2f}W",
            ]
        )

    def refresh(self):
        self.sun_spec_did = InverterDeviceType(self._read_uint16(40_069))
        self.sun_spec_length = self._read_uint16(40_070)

        self.ac_current, self.ac_current_a, self.ac_current_b, self.ac_current_c = (
            self._read_multi_scaled_uint16([40_071, 40_072, 40_073, 40_074], 40_075)
        )
        (
            self.ac_voltage_ab,
            self.ac_voltage_bc,
            self.ac_voltage_ca,
            self.ac_voltage_an,
            self.ac_voltage_bn,
            self.ac_voltage_cn,
        ) = self._read_multi_scaled_uint16(
            [40_076, 40_077, 40_078, 40_079, 40_080, 40_081],
            40_082,
        )
        self.ac_power = self._read_scaled_int16(40_083, 40_084)
        self.ac_frequency = self._read_scaled_uint16(40_085, 40_086)
        self.ac_power_apparent = self._read_scaled_int16(40_087, 40_088)
        self.ac_power_reactive = self._read_scaled_int16(40_089, 40_090)
        self.ac_power_factor = self._read_scaled_int16(40_091, 40_092)
        self.ac_energy_lifetime = self._read_scaled_acc32(40_093, 40_095)

        self.dc_current = self._read_scaled_uint16(40_096, 40_097)
        self.dc_voltage = self._read_scaled_uint16(40_098, 40_099)
        self.dc_power = self._read_scaled_int16(40_100, 40_101)

        self.heat_sink_temp = self._read_scaled_int16(40_103, 40_106)
        self.status = InverterDeviceStatus(self._read_uint16(40_107))
        self.status_vendor = self._read_uint16(40_108)

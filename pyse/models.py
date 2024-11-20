from pymodbus.client.base import ModbusBaseSyncClient

from .consts import InverterDeviceStatus


DATATYPE = ModbusBaseSyncClient.DATATYPE
type int16 = int
type uint16 = int
type int32 = int
type uint32 = int


class BaseModel:
    """Common base model."""

    def __init__(self, client: ModbusBaseSyncClient):
        self._client = client
        self.refresh()

    def _read(
        self,
        address: int,
        data_type: DATATYPE,
        count: int = 0,
    ):
        if not count:
            _, count = data_type.value

        result = self._client.read_holding_registers(address, count)
        value = self._client.convert_from_registers(result.registers, data_type)

        if data_type is DATATYPE.STRING:
            value = value.strip("\x00")
        return value

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
        self.sun_spec_id = self._read(40_000, DATATYPE.UINT32)
        self.sun_spec_did = self._read(40_002, DATATYPE.UINT16)
        self.sun_spec_len = self._read(40_003, DATATYPE.UINT16)
        self.manufacturer = self._read(40_004, DATATYPE.STRING, 16)
        self.model = self._read(40_020, DATATYPE.STRING, 16)
        self.version = self._read(40_044, DATATYPE.STRING, 8)
        self.serial_number = self._read(40_052, DATATYPE.STRING, 16)
        self.device_address = self._read(40_068, DATATYPE.UINT16)


class InverterModel(BaseModel):
    sun_spec_did: uint16
    status: InverterDeviceStatus

    def __str__(self):
        return f"{self.status.name} - {self.sun_spec_did}"

    def refresh(self):
        self.sun_spec_did = self._read(40_069, DATATYPE.UINT16)

        self.status = InverterDeviceStatus(
            self._read(40_107, DATATYPE.UINT16),
        )

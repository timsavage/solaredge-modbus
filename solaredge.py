from pymodbus.client import ModbusTcpClient
from pyse.models import CommonModel, InverterModel

client = ModbusTcpClient("192.168.1.140", port=1502)
with client:
    common = CommonModel(client)
    inverter = InverterModel(client)

    print(common)
    print(inverter)

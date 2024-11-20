from pymodbus.client import ModbusTcpClient

from pyse.meter import MeterCommonModel, MeterDataModel
from pyse.models import CommonModel, InverterModel

client = ModbusTcpClient("192.168.1.140", port=1502)
with client:
    common = CommonModel(client)
    print(common)
    inverter = InverterModel(client)
    print(inverter)
    print("")
    meter = MeterCommonModel.meter_1(client)
    print(meter)
    data = MeterDataModel.meter_1(client)
    print(data)

from pymodbus.client import ModbusTcpClient

from pyse import MeterCommonModel, InverterModel, MeterDataModel, CommonModel

client = ModbusTcpClient(
    "192.168.1.140",
    port=1502,
)
with client:
    common = CommonModel(client)
    common.refresh()
    print(common)

    inverter = InverterModel(client)
    inverter.refresh()
    print(inverter)

    print("")

    meter = MeterCommonModel.meter_1(client)
    meter.refresh()
    print(meter)

    data = MeterDataModel.meter_1(client)
    data.refresh()
    print(data)

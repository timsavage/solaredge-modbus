# Solar Edge Modbus

A simple implementation of the SunSpec Modbus logging interface for Solar Edge Inverters.

## Usage

Requires Python 3.12+

This requires that your inverter has Modbus enabled, typically this works over Ethernet (not WiFi).

## Quick Example

Install pymodbus from pip (or use included poetry config).

This script is included in the repository as `solaredge.py`. Replace `INVERTER_HOST` with the IP address of your 
inverter. 

```python
from pymodbus.client import ModbusTcpClient
from pyse.models import CommonModel, InverterModel

client = ModbusTcpClient("INVERTER_HOST", port=1502)
with client:
    common = CommonModel(client)
    print(common)

    inverter = InverterModel(client)
    print(inverter)
```

This will print out the model number, version and serial number as well as the status of the inverter.

## References

- [Implementation Notes](https://knowledge-center.solaredge.com/sites/kc/files/sunspec-implementation-technical-note.pdf)
s
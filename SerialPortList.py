import serial.tools.list_ports


class SerialPortList:
    def __init__(self):
        self.ports = []

    def refresh_ports(self):
        # Get a list of all available serial ports (name and address)
        self.ports = [
            (port.device, port.description) for port in serial.tools.list_ports.comports()
        ]

    def get_ports(self):
        # Export a json string with the list of available ports
        try:
            self.refresh_ports()
            ports_array = [{"name": name if name != "n/a" else address, "address": address} for address, name in self.ports]
            return {
                "ports": ports_array,
                "error": "None"
            }
        except Exception as e:
            return {
                "ports": [],
                "error": str(e)
            }
import serial.tools.list_ports


class SerialPortList:
    def __init__(self):
        self.ports = []

    def refresh_ports(self):
        # Get a list of all available serial ports (name and address)
        all_ports = serial.tools.list_ports.comports()
        
        # Filter out unwanted ports on Linux (ttyS ports that aren't actually connected)
        filtered_ports = []
        for port in all_ports:
            # Skip ttyS ports on Linux unless they have a meaningful description
            if port.device.startswith('/dev/ttyS') and (
                port.description == 'ttyS' + port.device.split('ttyS')[1] or 
                port.description == 'n/a' or
                'ttyS' in port.description and len(port.description) < 10
            ):
                continue
            
            # Skip ports with no hardware info (likely virtual/built-in ports)
            if not port.hwid or port.hwid == 'n/a':
                # But keep USB ports even without hwid
                if not any(usb_indicator in port.device.lower() for usb_indicator in ['usb', 'acm', 'ttyACM', 'ttyUSB']):
                    continue
            
            filtered_ports.append(port)
        
        self.ports = [
            (port.device, port.description) for port in filtered_ports
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
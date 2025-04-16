# defines.py
# Definitions used by NDI Combined API
# Combined API definitions are documented in
# - Polaris Vega Application Program Interface Guide

# import standard libraries
from enum import Enum, IntEnum

# import NDI libraries
from ndtrack.ndtypes.NDLog import *


class FrameType(Enum):
    """ enumerator of Frame Types
    """
    Dummy = 0
    ActiveWireless = 1
    Passive = 2
    Active = 3
    Laser = 4
    Illuminated = 5
    Background = 6
    Magnetic = 7

    def __str__(self):
        self._translation = {
            self.Dummy.value: "Dummy",
            self.ActiveWireless.value: "Active Wireless",
            self.Passive.value: "Passive",
            self.Active.value: "Active",
            self.Laser.value: "Laser",
            self.Illuminated.value: "Illuminated",
            self.Background.value: "Background",
            self.Magnetic.value: "Magnetic"
        }
        return self._translation[self.value]


class ComponentType(Enum):
    """ enumerator of Component Types """
    NONE = 0x0000
    Frame = 0x0001
    comp6D = 0x0002
    comp3D = 0x0003
    comp1D = 0x0004
    comp3DError = 0x0009
    Image = 0x000A
    Alert = 0x0012

    def __str__(self):
        self._translation = {
            self.NONE.value: "--none--",
            self.Frame.value: "Frame Component",
            self.comp6D.value: "6D Component",
            self.comp3D.value: "3D Component",
            self.comp1D.value: "1D Component",
            self.comp3DError.value: "3D Error Component",
            self.Image.value: "Image Component",
            self.Alert.value: "Alert Component"
        }
        return self._translation[self.value]


class SystemAlertType(Enum):
    """ enumerator of System Alert Component Type """
    Fault = 0
    Alert = 1
    Event = 2

    def __str__(self):
        self._translation = {
            self.Fault.value: "Fault",
            self.Alert.value: "Alert",
            self.Event.value: "Event"
        }
        return self._translation[self.value]


class FaultCode(Enum):
    """ enumerator of System Alert of type Fault """
    FatalParameter = 1
    SensorParameter = 2
    MainVoltage = 3
    SensorVoltage = 4
    IlluminatorVoltage = 5
    IlluminatorCurrent = 6
    Sensor0Temperature = 7
    Sensor1Temperature = 8
    MainTemperature = 9
    Sensor = 10

    def __str__(self):
        self._translation = {
            self.FatalParameter.value: "SYSTEM_FAULT_FATAL_PARAMETER_FAULT",
            self.SensorParameter.value: "SYSTEM_FAULT_SENSOR_PARAMETERS",
            self.MainVoltage.value: "SYSTEM_FAULT_MAIN_VOLTAGE_FAULT",
            self.SensorVoltage.value: "SYSTEM_FAULT_SENSOR_VOLTAGE_FAULT",
            self.IlluminatorVoltage.value: "SYSTEM_FAULT_ILLUMINATOR_VOLTAGE_FAULT",
            self.IlluminatorCurrent.value: "SYSTEM_FAULT_ILLUMINATOR_CURRENT_FAULT",
            self.Sensor0Temperature.value: "SYSTEM_FAULT_SENSOR_0_TEMPERATURE_FAULT",
            self.Sensor1Temperature.value: "SYSTEM_FAULT_SENSOR_1_TEMPERATURE_FAULT",
            self.MainTemperature.value: "SYSTEM_FAULT_MAIN_TEMPERATURE_FAULT",
            self.Sensor.value: "SYSTEM_FAULT_SENSOR_FAULT"
        }
        return self._translation[self.value]


class AlertCode(Enum):
    """ enumerator of System Alert of type Alert """
    BatteryFault = 1
    BumpDetected = 2
    FirmwareIncompatible = 3
    NonFatalParameterFault = 4
    FlashFull = 5
    LaserBatteryFault = 6
    StorageTemperature = 7
    TemperatureHigh = 8
    TemperatureLow = 9
    SCUDisconnected = 10
    PSUDisconnected = 11
    FGDisconnected = 12
    HardwareChanged = 13
    PTPSyncFault = 14
    VideoCameraFault = 15
    FirmwareInSafeMode = 17

    def __str__(self):
        self._translation = {
            self.BatteryFault.value: "SYSTEM_ALERT_BATTERY_FAULT",
            self.BumpDetected.value: "SYSTEM_ALERT_BUMP_DETECTED",
            self.FirmwareIncompatible.value: "SYSTEM_ALERT_FIRMWARE_INCOMPATIBLE",
            self.NonFatalParameterFault.value: "SYSTEM_ALERT_NON-FATAL_PARAMETER_FAULT",
            self.FlashFull.value: "SYSTEM_ALERT_FLASH_FULL",
            self.LaserBatteryFault.value: "SYSTEM_ALERT_LASER_BATTERY_FAULT",
            self.StorageTemperature.value: "SYSTEM_ALERT_STORAGE_TEMP_EXCEEDED",
            self.TemperatureHigh.value: "SYSTEM_ALERT_TEMPERATURE_HIGH",
            self.TemperatureLow.value: "SYSTEM_ALERT_TEMPERATURE_LOW",
            self.SCUDisconnected.value: "SYSTEM_ALERT_SCU_DISCONNECTED",
            self.PSUDisconnected.value: "SYSTEM_ALERT_PSU_DISCONNECTED",
            self.FGDisconnected.value: "SYSTEM_ALERT_FG_DISCONNECTED",
            self.HardwareChanged.value: "SYSTEM_ALERT_HW_CHANGED",
            self.PTPSyncFault.value: "SYSTEM_ALERT_PTP_SYNCHRONIZATION_FAULT",
            self.VideoCameraFault.value: "SYSTEM_ALERT_VIDEO_CAMERA_NOT_FUNCTIONING",
            self.FirmwareInSafeMode.value: "SYSTEM_ALERT_FIRMWARE_RUNNING_IN_SAFE_MODE"
        }
        return self._translation[self.value]


class EventCode(Enum):
    ActiveToolConnected = 1
    ActiveToolDisconnected = 2
    SIUConnected = 3
    SIUDisconnected = 4
    HardwareChanged = 5
    PTPMasterChanged = 6

    def __str__(self):
        self._translation = {
            self.ActiveToolConnected.value: "SYSTEM_EVENT_TOOL_CONNECTED",
            self.ActiveToolDisconnected.value: "SYSTEM_EVENT_TOOL_DISCONNECTED",
            self.SIUConnected.value: "SYSTEM_EVENT_SIU_CONNECTED",
            self.SIUDisconnected.value: "SYSTEM_EVENT_SIU_DISCONNECTED",
            self.HardwareChanged.value: "SYSTEM_EVENT_HARDWARE_CONFIGURATION_CHANGED",
            self.PTPMasterChanged.value: "SYSTEM_EVENT_PTP_MASTER_CHANGED"
        }
        return self._translation[self.value]


class Status3D(Enum):
    """ enumerator of 3D status """
    OKAY = 0x00
    Missing = 0x01
    OffAngle = 0x02
    BadFit = 0x03
    OOV = 0x04
    OOV_UsedIn6D = 0x05
    PossiblePhantom = 0x06
    Saturated = 0x07
    Saturated_OOV = 0x08
    Stray = 0xFF

    def __str__(self):
        self._translation = {
            self.OKAY.value: "OKAY",
            self.Missing.value: "MISSING",
            self.OffAngle.value: "OFF ANGLE",
            self.BadFit.value: "BAD FIT",
            self.OOV.value: "OUT OF VOLUME",
            self.OOV_UsedIn6D.value: "OOV. Used.",
            self.PossiblePhantom.value: "PHANTOM",
            self.Saturated.value: "SATURATED",
            self.Saturated_OOV.value: "SATURATED OOV",
            self.Stray.value: "STRAY"
        }
        return self._translation[self.value]


def main():
    # set up to log everything
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(levelname)s : %(message)s')

    # check each of the FrameType definitions
    for f in FrameType:
        print(f)
        frame_type = FrameType(f.value)
        print(frame_type)

    for c in ComponentType:
        print(c)
        component_type = ComponentType(c.value)
        print(component_type)

    for a in SystemAlertType:
        print(a)
        alert_type = SystemAlertType(a.value)
        print(alert_type)

    for f in FaultCode:
        print(f)
        fault = FaultCode(f.value)
        print(fault)

    for a in AlertCode:
        print(a)
        alert = AlertCode(a.value)
        print(alert)

    for e in EventCode:
        print(e)
        ev = EventCode(e.value)
        print(ev)


if __name__ == "__main__":
    main()

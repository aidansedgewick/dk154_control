from logging import getLogger
#from pysnmp.hlapi.asyncio.cmdgen import *
from pysnmp.hlapi import (
    getCmd,
    setCmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    Integer32,
)

OUTLET_STATES = {
    "immediateOn": 1,
    "immediateOff": 2,
    "immediateReboot": 3,
    "delayedOn": 4,
    "delayedOff": 5,
    "delayedReboot": 6,
    "cancelPendingCommand": 7,
    "outletIdentify": 8,
}

OUTLET_STATES_INV = {v: k for k, v in OUTLET_STATES.items()}


class CyberPowerPduException(Exception):
    pass


logger = getLogger(__name__.split(".")[-1])


class WaveLamps:

    INTERNAL_HOST = "192.168.132.59"
    PDU_PORT = 161
    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 8884
    DEFAULT_OUTLETS = (5, 6)
    AVAILABLE_OUTLETS = (1, 2, 3, 4, 5, 6, 7, 8)

    ePDUOutletControlOutletCommand = "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4"

    def __init__(self, test_mode=False, outlets=DEFAULT_OUTLETS):

        logger.info("init wavelamp controller")

        self.HOST = self.INTERNAL_HOST
        self.PORT = self.PDU_PORT
        if test_mode:
            logger.info("starting in TEST MODE")
            self.HOST = self.LOCAL_HOST
            self.PORT = self.LOCAL_PORT

        if isinstance(outlets, int):
            outlets = tuple(outlets)  # So can loop through them later...
        self.outlets = outlets

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def set_outlet(self, outlet: int, state: int):

        if state not in OUTLET_STATES.values():
            msg = f"unknown state {state}. Choose from:\n" + "\n    ".join(
                f"{k}={v}" for k, v in OUTLET_STATES_INV
            )
            raise CyberPowerPduException(msg)

        if outlet not in self.AVAILABLE_OUTLETS:
            msg = f"outlet not in available_outlets: {self.AVAILABLE_OUTLETS}"
            raise CyberPowerPduException()

        state_str = OUTLET_STATES_INV[state]
        logger.info(f"switching outlet {outlet} to state {state} ({state_str})")

        oid = ObjectIdentity(f"{self.ePDUOutletControlOutletCommand}.{outlet}")

        errorIndication, errorStatus, errorIndex, varBinds = next(
            setCmd(
                SnmpEngine(),
                CommunityData("private"),
                UdpTransportTarget((self.HOST, self.PORT)),
                ContextData(),
                ObjectType(oid, Integer32(state)),
            )
        )
        print(errorIndication, errorStatus, errorIndex, varBinds)

    def get_outlet_state(self, outlet):

        if outlet not in self.AVAILABLE_OUTLETS:
            msg = f"outlet not in available_outlets: {self.AVAILABLE_OUTLETS}"
            raise CyberPowerPduException(msg)

        oid = ObjectIdentity(f"{self.ePDUOutletControlOutletCommand}.{outlet}")

        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(
                SnmpEngine(),
                CommunityData("private"),
                UdpTransportTarget((self.HOST, self.PORT)),
                ContextData(),
                ObjectType(oid),
            )
        )

    def all_lamps_on(self):
        for outlet in self.outlets:
            self.set_outlet(outlet, 1)  # immediateOn

    def all_lamps_off(self):
        for outlet in self.outlets:
            self.set_outlet(outlet, 2)  # immediateOff

    def all_outlets_off(self):
        for outlet in self.AVAILABLE_OUTLETS:
            self.set_outlet(outlet, 2)  # immediateOff


if __name__ == "__main__":

    import dk154_control  # For logger

    print("testmode wavelamps")

    wvlamps = WaveLamps(test_mode=True)
    wvlamps.all_lamps_off()

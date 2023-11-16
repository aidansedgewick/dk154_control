"""
Python lookup for TCS TCP-IP command constants

ASCOL protocol

16-11-23
"""

#GLOBAL COMMAND CODES

#Global LoGin
GLLG_CODES = {
    "0": "wrong password",
    "1": "correct password",
}

#GLobal DePartment
GLDP_CODES = {
    "00000":"---",
    "19539":"La Silla department",
    "20529":"Prague department",
    "17201":"Copenhagen department",
    "20273":"Ondrejov NEOS department",
    "20274":"Ondrejov GAIA department",
    "16945":"Brno department",
    "20563":"Projectsoft department",
}

#'GLobal read REmote state (IN: none, OUT: 0/1 - local/remote)'
#this command is not defined in the ASCOL document
GLRE_CODES = {
    "0":"<b>LOCAL</b>",
    "1":"REMOTE"
}

#'GLobal read Safety Relay state (IN: none, OUT: 0/1 - open/closed)'
#(this command is not defined in the ASCOL document)
GLSR_CODES = {
    "0":"open",
    "1":"closed",
}

#TELESCOPE COMMAND CODES

#Telescope Read Right ascension and Declination
TRRD_POSITION_CODES = {
   "0": "east",
   "1": "west",
}

#Telescope additional Tracking speeds 1 Selected
TTT1S_CODES = {
   "1": "on",
   "2": "off",
}

#Telescope additional Tracking speeds 2 Selected
TTT2S_CODES = {
   "1": "on",
   "2": "off",
}

#TElescope Read State
TERS_CODES = {
    "00": "switched off",
    "01": "switching off",
    "02": "switching on 1",
    "03": "switching on 2",
    "04": "ready",
    "05": "sky track",
    "06": "mechanical slew",
    "07": "sky slew",
    "08": "mechanical flip",
    "09": "sky flip",
    "10": "parking",
    "11": "parking",
    "12": "initializing",
}


#DOME COMMAND CODES

#DOme Read State
DORS_CODES = {
    "00":"stopped",
    "01":"slew -",
    "02":"slew +",
    "03":"auto",
    "04":"auto -",
    "05":"auto +",
    "06":"manual -",
    "07":"manual +",
    "08":"parking",
    "09":"parking -",
    "10":"parking +",
    "11":"initializing",
}

#'DOme read Slit State'
#this command is not defined in the ASCOL document
DOSS_CODES = {
    "00":"stopped",
    "01":"openning",
    "02":"closing",
    "03":"open",
    "04":"closed",
}

#'DOme read LAmp state (IN: none, OUT: 1/0 - on/off)'
#this command is not defined in the ASCOL document
DOLA_CODES = {
    "0":"off",
    "1":"on",
}

#FLAP COMMAND CODES

#Flap Cassegrain Read State
FCRS_CODES = {
    "00":"stopped",
    "01":"opening",
    "02":"closing",
    "03":"open",
    "04":"closed",
}

#Flap Mirror Read State
FMRS_CODES = {
    "00":"stopped",
    "01":"opening",
    "02":"closing",
    "03":"open",
    "04":"closed",
}

#DFOSC FILTER WHEEL A and B COMMAND CODES

#Wheel A Read Position
WARP_CODES = {
    "0":"empty",
    "1":"Stromgr u",
    "2":"Stromgr v",
    "3":"Stromgr b",
    "4":"Stromgr y",
    "5":"OII",
    "6":"g2",
    "7":"OIII",
    "8":"rotating",
}

#Wheel A Read State
WARS_CODES = {
    "00":"stopped",
    "01":"positioning +",
    "02":"positioning -",
    "03":"positioning",
    "04":"locked",
}

#Wheel B Read Position
WBRP_CODES = {
    "0":"empty",
    "1":"U",
    "2":"B",
    "3":"V",
    "4":"R",
    "5":"I",
    "6":"H-alpha rs",
    "7":"rotating",
}

#Wheel B Read State
WBRS_CODES = {
    "00":"stopped",
    "01":"positioning +",
    "02":"positioning -",
    "03":"positioning",
    "04":"locked",
}


#FOCUS COMMAND CODES

#FOcus Read State
FORS_CODES = {
    "00":"stopped",
    "01":"positioning",
    "02":"positioning",
    "03":"manual -",
    "04":"manual +",
}

#MOVABLE CARRIAGE COMMAND CODES

#Movable Carriage Read State
MCRS_CODES = {
    "00":"stopped",
    "01":"positioning",
    "02":"manual -",
    "03":"manual +",
    "04":"parking",
    "05":"initializing -",
    "06":"initializing +",
}


#AUTOGUIDING COMMAND CODES

#AutoGuider Tracking selected
AGTS_CODES = {
    "0":"on",
    "1":"off",
}

#AutoGuider out of Field of view Limits
AGFL_CODES = {
    "0":"within limits",
    "1":"out of limits",
}

#Autoguider Mirror Read Position
AMRP_CODES = {
    "1":"position 1",
    "2":"position 2",
}

#Autoguider Wheel Read Position
AWRP_CODES = {
    "0":"tbd",
    "1":"tbd",
    "2":"tbd",
    "3":"tbd",
    "4":"tbd",
    "5":"tbd",
    "6":"between positions",
}

#Autoguider Focus Read State
AFRS_CODES = {
    "00":"stopped",
    "01":"poitioning",
    "02":"manual -",
    "03":"manual +",
    "04":"parking",
    "05":"initialising -",
    "06":"initialising +",
}

#Autoguider X axis Read State
AXRS_CODES = {
    "00":"stopped",
    "01":"poitioning",
    "02":"manual -",
    "03":"manual +",
    "04":"parking",
    "05":"initialising -",
    "06":"initialising +",
}

#Autoguider Y axis Read State
AYRS_CODES = {
    "00":"stopped",
    "01":"poitioning",
    "02":"manual -",
    "03":"manual +",
    "04":"parking",
    "05":"initialising -",
    "06":"initialising +",
}

#Autoguider Mirror Read State
AMRS_CODES = {
    "00":"stopped",
    "01":"positioning 1",
    "02":"positioning 2",
    "03":"position 1",
    "04":"position 2",
}

#Autoguider Wheel Read State
AWRS_CODES = {
    "00":"stopped",
    "01":"positioning -",
    "02":"positioning +",
    "03":"positioning",
    "04":"locked",
}

#SHUTTER COMMAND CODES

#SHutter Read Position
SHRP_CODES = {
    "0":"closed",
    "1":"open",
}


#METEOR COMMAND CODES

#MEteo Brightness East
MEBE_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo Brightness North
MEBN_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo Brightness West
MEBW_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo TWilight
METW_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo HUmidity
MEHU_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo TEmperature
METE_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo Wind Speed
MEWS_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo PRecipitation
MEPR_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo Atmospheric Pressure
MEAP_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#MEteo PYrgeometer
MEPY_VALIDITY_CODES = {
    "0":"not valid",
    "1":"valid",
}

#Commands below are not defined in the ASCOL document.

#'Vent North read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VNOS_CODES = {
    "04":"open",
    "05":"closed",
}

#'Vent NorthEast read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VNES_CODES = {
    "04":"open",
    "05":"closed",
}

#'Vent EAst read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VEAS_CODES = {
    "04":"open",
    "05":"closed",
}

#'Vent SouthEast read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VSES_CODES = {
    "04":"open",
    "05":"closed",
}

#'Vent SOuth read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VSOS_CODES = {
    "04":"open",
    "05":"closed",
}

#'Vent SouthWest read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VSWS_CODES = {
    "04":"open",
    "05":"closed",
}

#'Vent WEst read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VWES_CODES = {
    "04":"open",
    "05":"closed",
}

#'Vent NorthWest read State (IN: none, OUT: 0-5 - U/S/Oing/Cing/O/C)'
VNWS_CODES = {
    "04":"open",
    "05":"closed",
}

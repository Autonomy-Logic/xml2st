#
# Generated by erpcgen 1.11.0 on Fri Jan 19 08:26:41 2024.
#
# AUTOGENERATED - DO NOT EDIT
#

# Abstract base class for BeremizPLCObjectService
class IBeremizPLCObjectService(object):
    SERVICE_ID = 1
    APPENDCHUNKTOBLOB_ID = 1
    GETLOGMESSAGE_ID = 2
    GETPLCID_ID = 3
    GETPLCSTATUS_ID = 4
    GETTRACEVARIABLES_ID = 5
    MATCHMD5_ID = 6
    NEWPLC_ID = 7
    PURGEBLOBS_ID = 8
    REPAIRPLC_ID = 9
    RESETLOGCOUNT_ID = 10
    SEEDBLOB_ID = 11
    SETTRACEVARIABLESLIST_ID = 12
    STARTPLC_ID = 13
    STOPPLC_ID = 14

    def AppendChunkToBlob(self, data, blobID, newBlobID):
        raise NotImplementedError()

    def GetLogMessage(self, level, msgID, message):
        raise NotImplementedError()

    def GetPLCID(self, plcID):
        raise NotImplementedError()

    def GetPLCstatus(self, status):
        raise NotImplementedError()

    def GetTraceVariables(self, debugToken, traces):
        raise NotImplementedError()

    def MatchMD5(self, MD5, match):
        raise NotImplementedError()

    def NewPLC(self, md5sum, plcObjectBlobID, extrafiles, success):
        raise NotImplementedError()

    def PurgeBlobs(self):
        raise NotImplementedError()

    def RepairPLC(self):
        raise NotImplementedError()

    def ResetLogCount(self):
        raise NotImplementedError()

    def SeedBlob(self, seed, blobID):
        raise NotImplementedError()

    def SetTraceVariablesList(self, orders, debugtoken):
        raise NotImplementedError()

    def StartPLC(self):
        raise NotImplementedError()

    def StopPLC(self, success):
        raise NotImplementedError()



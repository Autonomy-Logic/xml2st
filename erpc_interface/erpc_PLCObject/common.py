#
# Generated by erpcgen 1.11.0 on Wed Jan 17 21:59:20 2024.
#
# AUTOGENERATED - DO NOT EDIT
#


# Enumerators data types declarations
class PLCstatus_enum:
    Empty = 0
    Stopped = 1
    Started = 2
    Broken = 3
    Disconnected = 4


# Structures data types declarations
class log_message(object):
    def __init__(self, msg=None, tick=None, sec=None, nsec=None):
        self.msg = msg # string
        self.tick = tick # uint32
        self.sec = sec # uint32
        self.nsec = nsec # uint32

    def _read(self, codec):
        self.msg = codec.read_string()
        self.tick = codec.read_uint32()
        self.sec = codec.read_uint32()
        self.nsec = codec.read_uint32()
        return self

    def _write(self, codec):
        if self.msg is None:
            raise ValueError("msg is None")
        codec.write_string(self.msg)
        if self.tick is None:
            raise ValueError("tick is None")
        codec.write_uint32(self.tick)
        if self.sec is None:
            raise ValueError("sec is None")
        codec.write_uint32(self.sec)
        if self.nsec is None:
            raise ValueError("nsec is None")
        codec.write_uint32(self.nsec)

    def __str__(self):
        return "<%s@%x msg=%s tick=%s sec=%s nsec=%s>" % (self.__class__.__name__, id(self), self.msg, self.tick, self.sec, self.nsec)

    def __repr__(self):
        return self.__str__()

class PSKID(object):
    def __init__(self, ID=None, PSK=None):
        self.ID = ID # string
        self.PSK = PSK # string

    def _read(self, codec):
        self.ID = codec.read_string()
        self.PSK = codec.read_string()
        return self

    def _write(self, codec):
        if self.ID is None:
            raise ValueError("ID is None")
        codec.write_string(self.ID)
        if self.PSK is None:
            raise ValueError("PSK is None")
        codec.write_string(self.PSK)

    def __str__(self):
        return "<%s@%x ID=%s PSK=%s>" % (self.__class__.__name__, id(self), self.ID, self.PSK)

    def __repr__(self):
        return self.__str__()

class PLCstatus(object):
    def __init__(self, PLCstatus=None, logcounts=None):
        self.PLCstatus = PLCstatus # PLCstatus_enum
        self.logcounts = logcounts # uint32[4]


    def _read(self, codec):
        self.PLCstatus = codec.read_int32()
        self.logcounts = []
        for _i0 in range(4):
            _v0 = codec.read_uint32()
            self.logcounts.append(_v0)

        return self

    def _write(self, codec):
        if self.PLCstatus is None:
            raise ValueError("PLCstatus is None")
        codec.write_int32(self.PLCstatus)
        if self.logcounts is None:
            raise ValueError("logcounts is None")
        for _i0 in self.logcounts:
            codec.write_uint32(_i0)


    def __str__(self):
        return "<%s@%x PLCstatus=%s logcounts=%s>" % (self.__class__.__name__, id(self), self.PLCstatus, self.logcounts)

    def __repr__(self):
        return self.__str__()

class trace_sample(object):
    def __init__(self, tick=None, TraceBuffer=None):
        self.tick = tick # uint32
        self.TraceBuffer = TraceBuffer # binary

    def _read(self, codec):
        self.tick = codec.read_uint32()
        self.TraceBuffer = codec.read_binary()
        return self

    def _write(self, codec):
        if self.tick is None:
            raise ValueError("tick is None")
        codec.write_uint32(self.tick)
        if self.TraceBuffer is None:
            raise ValueError("TraceBuffer is None")
        codec.write_binary(self.TraceBuffer)

    def __str__(self):
        return "<%s@%x tick=%s TraceBuffer=%s>" % (self.__class__.__name__, id(self), self.tick, self.TraceBuffer)

    def __repr__(self):
        return self.__str__()

class TraceVariables(object):
    def __init__(self, PLCstatus=None, traces=None):
        self.PLCstatus = PLCstatus # PLCstatus_enum
        self.traces = traces # list<trace_sample>

    def _read(self, codec):
        self.PLCstatus = codec.read_int32()
        _n0 = codec.start_read_list()
        self.traces = []
        for _i0 in range(_n0):
            _v0 = trace_sample()._read(codec)
            self.traces.append(_v0)

        return self

    def _write(self, codec):
        if self.PLCstatus is None:
            raise ValueError("PLCstatus is None")
        codec.write_int32(self.PLCstatus)
        if self.traces is None:
            raise ValueError("traces is None")
        codec.start_write_list(len(self.traces))
        for _i0 in self.traces:
            _i0._write(codec)


    def __str__(self):
        return "<%s@%x PLCstatus=%s traces=%s>" % (self.__class__.__name__, id(self), self.PLCstatus, self.traces)

    def __repr__(self):
        return self.__str__()

class extra_file(object):
    def __init__(self, fname=None, blobID=None):
        self.fname = fname # string
        self.blobID = blobID # binary

    def _read(self, codec):
        self.fname = codec.read_string()
        self.blobID = codec.read_binary()
        return self

    def _write(self, codec):
        if self.fname is None:
            raise ValueError("fname is None")
        codec.write_string(self.fname)
        if self.blobID is None:
            raise ValueError("blobID is None")
        codec.write_binary(self.blobID)

    def __str__(self):
        return "<%s@%x fname=%s blobID=%s>" % (self.__class__.__name__, id(self), self.fname, self.blobID)

    def __repr__(self):
        return self.__str__()

class trace_order(object):
    def __init__(self, idx=None, iectype=None, force=None):
        self.idx = idx # uint32
        self.iectype = iectype # uint8
        self.force = force # binary

    def _read(self, codec):
        self.idx = codec.read_uint32()
        self.iectype = codec.read_uint8()
        self.force = codec.read_binary()
        return self

    def _write(self, codec):
        if self.idx is None:
            raise ValueError("idx is None")
        codec.write_uint32(self.idx)
        if self.iectype is None:
            raise ValueError("iectype is None")
        codec.write_uint8(self.iectype)
        if self.force is None:
            raise ValueError("force is None")
        codec.write_binary(self.force)

    def __str__(self):
        return "<%s@%x idx=%s iectype=%s force=%s>" % (self.__class__.__name__, id(self), self.idx, self.iectype, self.force)

    def __repr__(self):
        return self.__str__()


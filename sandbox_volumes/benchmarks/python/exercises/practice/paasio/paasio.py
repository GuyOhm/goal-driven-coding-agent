import io


class MeteredFile(io.BufferedRandom):
    """Implement using a subclassing model."""

    def __init__(self, *args, **kwargs):
        # counters
        self._read_bytes = 0
        self._read_ops = 0
        self._write_bytes = 0
        self._write_ops = 0
        # call parent init (patched in tests)
        super(MeteredFile, self).__init__(*args, **kwargs)

    def __enter__(self):
        # do not delegate to underlying object's __enter__
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # delegate to underlying object's __exit__ via super()
        return super(MeteredFile, self).__exit__(exc_type, exc_val, exc_tb)

    def __iter__(self):
        return self

    def __next__(self):
        data = super(MeteredFile, self).readline()
        # readline returns bytes; iterate until empty
        if not data:
            raise StopIteration
        # count this read
        self._read_ops += 1
        self._read_bytes += len(data)
        return data

    def read(self, size=-1):
        data = super(MeteredFile, self).read(size)
        # count op
        self._read_ops += 1
        # data may be None or bytes
        if data is None:
            return data
        self._read_bytes += len(data)
        return data

    @property
    def read_bytes(self):
        return self._read_bytes

    @property
    def read_ops(self):
        return self._read_ops

    def write(self, b):
        written = super(MeteredFile, self).write(b)
        # increment counters
        try:
            # write returns size as int
            self._write_ops += 1
            self._write_bytes += written
        except Exception:
            pass
        return written

    @property
    def write_bytes(self):
        return self._write_bytes

    @property
    def write_ops(self):
        return self._write_ops


class MeteredSocket:
    """Implement using a delegation model."""

    def __init__(self, socket):
        self._sock = socket
        self._recv_bytes = 0
        self._recv_ops = 0
        self._send_bytes = 0
        self._send_ops = 0

    def __enter__(self):
        # do not call underlying __enter__
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # delegate to underlying socket's __exit__
        return self._sock.__exit__(exc_type, exc_val, exc_tb)

    def recv(self, bufsize, flags=0):
        # call underlying recv and update counters
        data = self._sock.recv(bufsize, flags)
        # update only on success
        if data is not None:
            self._recv_ops += 1
            self._recv_bytes += len(data)
        return data

    @property
    def recv_bytes(self):
        return self._recv_bytes

    @property
    def recv_ops(self):
        return self._recv_ops

    def send(self, data, flags=0):
        sent = self._sock.send(data, flags)
        # update on success
        try:
            self._send_ops += 1
            self._send_bytes += sent
        except Exception:
            pass
        return sent

    @property
    def send_bytes(self):
        return self._send_bytes

    @property
    def send_ops(self):
        return self._send_ops

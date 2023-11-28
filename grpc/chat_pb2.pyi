from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EncryptedPayload(_message.Message):
    __slots__ = ["encryptedMsg", "sender"]
    ENCRYPTEDMSG_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    encryptedMsg: bytes
    sender: str
    def __init__(self, sender: _Optional[str] = ..., encryptedMsg: _Optional[bytes] = ...) -> None: ...

class KeepAliveRequest(_message.Message):
    __slots__ = ["backup_id"]
    BACKUP_ID_FIELD_NUMBER: _ClassVar[int]
    backup_id: int
    def __init__(self, backup_id: _Optional[int] = ...) -> None: ...

class KeepAliveResponse(_message.Message):
    __slots__ = ["backup_ids", "primary_id"]
    BACKUP_IDS_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_ID_FIELD_NUMBER: _ClassVar[int]
    backup_ids: _containers.RepeatedScalarFieldContainer[int]
    primary_id: int
    def __init__(self, primary_id: _Optional[int] = ..., backup_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class Operation(_message.Message):
    __slots__ = ["opLst"]
    OPLST_FIELD_NUMBER: _ClassVar[int]
    opLst: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, opLst: _Optional[_Iterable[str]] = ...) -> None: ...

class Payload(_message.Message):
    __slots__ = ["msg"]
    MSG_FIELD_NUMBER: _ClassVar[int]
    msg: str
    def __init__(self, msg: _Optional[str] = ...) -> None: ...

class SendRequest(_message.Message):
    __slots__ = ["recipient", "sender", "sentMsg"]
    RECIPIENT_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    SENTMSG_FIELD_NUMBER: _ClassVar[int]
    recipient: Username
    sender: Username
    sentMsg: Payload
    def __init__(self, sender: _Optional[_Union[Username, _Mapping]] = ..., recipient: _Optional[_Union[Username, _Mapping]] = ..., sentMsg: _Optional[_Union[Payload, _Mapping]] = ...) -> None: ...

class Unreads(_message.Message):
    __slots__ = ["errorFlag", "privateKey", "unreads"]
    ERRORFLAG_FIELD_NUMBER: _ClassVar[int]
    PRIVATEKEY_FIELD_NUMBER: _ClassVar[int]
    UNREADS_FIELD_NUMBER: _ClassVar[int]
    errorFlag: bool
    privateKey: _containers.RepeatedScalarFieldContainer[str]
    unreads: str
    def __init__(self, errorFlag: bool = ..., unreads: _Optional[str] = ..., privateKey: _Optional[_Iterable[str]] = ...) -> None: ...

class Username(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

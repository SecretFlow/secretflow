# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: secretflow/spec/v1/report.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from secretflow.spec.v1 import component_pb2 as secretflow_dot_spec_dot_v1_dot_component__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fsecretflow/spec/v1/report.proto\x12\x12secretflow.spec.v1\x1a\"secretflow/spec/v1/component.proto\"\xc0\x01\n\x0c\x44\x65scriptions\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12\x34\n\x05items\x18\x03 \x03(\x0b\x32%.secretflow.spec.v1.Descriptions.Item\x1a^\n\x04Item\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12\x0c\n\x04type\x18\x03 \x01(\t\x12,\n\x05value\x18\x04 \x01(\x0b\x32\x1d.secretflow.spec.v1.Attribute\"\x90\x02\n\x05Table\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12\x35\n\x07headers\x18\x03 \x03(\x0b\x32$.secretflow.spec.v1.Table.HeaderItem\x12+\n\x04rows\x18\x04 \x03(\x0b\x32\x1d.secretflow.spec.v1.Table.Row\x1a\x36\n\nHeaderItem\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12\x0c\n\x04type\x18\x03 \x01(\t\x1aO\n\x03Row\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12,\n\x05items\x18\x03 \x03(\x0b\x32\x1d.secretflow.spec.v1.Attribute\"\xf2\x01\n\x03\x44iv\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12/\n\x08\x63hildren\x18\x03 \x03(\x0b\x32\x1d.secretflow.spec.v1.Div.Child\x1a\x9d\x01\n\x05\x43hild\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\x36\n\x0c\x64\x65scriptions\x18\x02 \x01(\x0b\x32 .secretflow.spec.v1.Descriptions\x12(\n\x05table\x18\x03 \x01(\x0b\x32\x19.secretflow.spec.v1.Table\x12$\n\x03\x64iv\x18\x04 \x01(\x0b\x32\x17.secretflow.spec.v1.Div\"H\n\x03Tab\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12%\n\x04\x64ivs\x18\x03 \x03(\x0b\x32\x17.secretflow.spec.v1.Div\"q\n\x06Report\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x65sc\x18\x02 \x01(\t\x12%\n\x04tabs\x18\x03 \x03(\x0b\x32\x17.secretflow.spec.v1.Tab\x12\x10\n\x08\x65rr_code\x18\x04 \x01(\x05\x12\x12\n\nerr_detail\x18\x05 \x01(\tB\'\n\x16\x63om.secretflow.spec.v1B\x0bReportProtoP\x01\x62\x06proto3')



_DESCRIPTIONS = DESCRIPTOR.message_types_by_name['Descriptions']
_DESCRIPTIONS_ITEM = _DESCRIPTIONS.nested_types_by_name['Item']
_TABLE = DESCRIPTOR.message_types_by_name['Table']
_TABLE_HEADERITEM = _TABLE.nested_types_by_name['HeaderItem']
_TABLE_ROW = _TABLE.nested_types_by_name['Row']
_DIV = DESCRIPTOR.message_types_by_name['Div']
_DIV_CHILD = _DIV.nested_types_by_name['Child']
_TAB = DESCRIPTOR.message_types_by_name['Tab']
_REPORT = DESCRIPTOR.message_types_by_name['Report']
Descriptions = _reflection.GeneratedProtocolMessageType('Descriptions', (_message.Message,), {

  'Item' : _reflection.GeneratedProtocolMessageType('Item', (_message.Message,), {
    'DESCRIPTOR' : _DESCRIPTIONS_ITEM,
    '__module__' : 'secretflow.spec.v1.report_pb2'
    # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Descriptions.Item)
    })
  ,
  'DESCRIPTOR' : _DESCRIPTIONS,
  '__module__' : 'secretflow.spec.v1.report_pb2'
  # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Descriptions)
  })
_sym_db.RegisterMessage(Descriptions)
_sym_db.RegisterMessage(Descriptions.Item)

Table = _reflection.GeneratedProtocolMessageType('Table', (_message.Message,), {

  'HeaderItem' : _reflection.GeneratedProtocolMessageType('HeaderItem', (_message.Message,), {
    'DESCRIPTOR' : _TABLE_HEADERITEM,
    '__module__' : 'secretflow.spec.v1.report_pb2'
    # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Table.HeaderItem)
    })
  ,

  'Row' : _reflection.GeneratedProtocolMessageType('Row', (_message.Message,), {
    'DESCRIPTOR' : _TABLE_ROW,
    '__module__' : 'secretflow.spec.v1.report_pb2'
    # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Table.Row)
    })
  ,
  'DESCRIPTOR' : _TABLE,
  '__module__' : 'secretflow.spec.v1.report_pb2'
  # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Table)
  })
_sym_db.RegisterMessage(Table)
_sym_db.RegisterMessage(Table.HeaderItem)
_sym_db.RegisterMessage(Table.Row)

Div = _reflection.GeneratedProtocolMessageType('Div', (_message.Message,), {

  'Child' : _reflection.GeneratedProtocolMessageType('Child', (_message.Message,), {
    'DESCRIPTOR' : _DIV_CHILD,
    '__module__' : 'secretflow.spec.v1.report_pb2'
    # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Div.Child)
    })
  ,
  'DESCRIPTOR' : _DIV,
  '__module__' : 'secretflow.spec.v1.report_pb2'
  # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Div)
  })
_sym_db.RegisterMessage(Div)
_sym_db.RegisterMessage(Div.Child)

Tab = _reflection.GeneratedProtocolMessageType('Tab', (_message.Message,), {
  'DESCRIPTOR' : _TAB,
  '__module__' : 'secretflow.spec.v1.report_pb2'
  # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Tab)
  })
_sym_db.RegisterMessage(Tab)

Report = _reflection.GeneratedProtocolMessageType('Report', (_message.Message,), {
  'DESCRIPTOR' : _REPORT,
  '__module__' : 'secretflow.spec.v1.report_pb2'
  # @@protoc_insertion_point(class_scope:secretflow.spec.v1.Report)
  })
_sym_db.RegisterMessage(Report)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\026com.secretflow.spec.v1B\013ReportProtoP\001'
  _DESCRIPTIONS._serialized_start=92
  _DESCRIPTIONS._serialized_end=284
  _DESCRIPTIONS_ITEM._serialized_start=190
  _DESCRIPTIONS_ITEM._serialized_end=284
  _TABLE._serialized_start=287
  _TABLE._serialized_end=559
  _TABLE_HEADERITEM._serialized_start=424
  _TABLE_HEADERITEM._serialized_end=478
  _TABLE_ROW._serialized_start=480
  _TABLE_ROW._serialized_end=559
  _DIV._serialized_start=562
  _DIV._serialized_end=804
  _DIV_CHILD._serialized_start=647
  _DIV_CHILD._serialized_end=804
  _TAB._serialized_start=806
  _TAB._serialized_end=878
  _REPORT._serialized_start=880
  _REPORT._serialized_end=993
# @@protoc_insertion_point(module_scope)

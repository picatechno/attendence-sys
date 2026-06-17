"""Debug pyzk Attendance attributes"""
from zk import ZK

zk = ZK('192.168.9.201', port=4370, timeout=10)
conn = zk.connect()
conn.disable_device()
atts = conn.get_attendance()
print(f"Total records: {len(atts)}")
first = atts[0]
print(f"Type: {type(first)}")
attrs = [x for x in dir(first) if not x.startswith('_')]
print(f"Attrs: {attrs}")
print(f"user_id: {first.user_id} (type: {type(first.user_id)})")
print(f"timestamp: {first.timestamp} (type: {type(first.timestamp)})")
for attr in ['status', 'punch', 'verify', 'mode', 'state']:
    if hasattr(first, attr):
        print(f"{attr}: {getattr(first, attr)}")
conn.enable_device()
conn.disconnect()

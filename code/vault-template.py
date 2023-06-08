import hvac
import os
import sys

host = os.environ.get("INFLUX_HOST")
if not host:
    print("InfluxDB host undefined")
    sys.exit()
port = int(os.environ.get("INFLUX_PORT", 8086))
user = os.environ.get("INFLUX_USER", "")
password = os.environ.get("INFLUX_PW", "")

client = hvac.Client(
    url='http://172.16.0.2:8200',
    token='nh-vault-root',
)

create_response = client.secrets.kv.v2.create_or_update_secret(
    path='influx',
    secret=dict(host=host, port=port, user=user, passw=password),
)

read_response = client.secrets.kv.read_secret_version(path='influx')

print(read_response['data']['data']['host'])
print(read_response['data']['data']['port'])
print(read_response['data']['data']['user'])

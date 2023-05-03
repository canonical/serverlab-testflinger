import hvac

client = hvac.Client(
    url='http://10.172.10.21:8200',
    token='nh-vault-root',
)

create_response = client.secrets.kv.v2.create_or_update_secret(
    path='influx',
    secret=dict(host='10.172.10.17', port=8086, user='root', passw='root'),
)

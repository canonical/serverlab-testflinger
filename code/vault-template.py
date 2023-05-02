import hvac

client = hvac.Client(
    url='http://10.245.128.21:8200',
    token='nh-vault-root',
)

create_response = client.secrets.kv.v2.create_or_update_secret(
    path='influx',
    secret=dict(host='', port=8086, user='', passw=''),
)

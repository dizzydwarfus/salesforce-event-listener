# Commands to push to azure container registry

1. Login to azure container registry

```docker
docker login salesforcesap.azurecr.io
```

2. Build and push the image

```docker
docker buildx build --platform linux/amd64 -t salesforcesap.azurecr.io/salesforce-listener:latest --push .
```

# Commands to build image locally and run it

1. Build the image

```docker
docker build -t salesforce-listener:latest .
```

2. Run the image

```docker
docker run --name salesforce-listener -e PROD_CONSUMER_KEY=3MVG9fTLmJ60pJ5LZmhGDcWxW0idc_RUYgK9EaRfjpPyHXfGLlp8XTlpYj7ysrpvI6wgP8U4dmKk_fGgsAFft -e PROD_CONSUMER_SECRET=F1B69CC57ACE6BCC7B8500A1D4AB6095CD47AB7E5DEB0738F58A9936990BD2FF -e PROD_DOMAIN=https://basf3dps.my.salesforce.com -e PROD_USERNAME=lian.zhen-yang@basf-3dps.com -e PROD_PASSWORD=Dizzydwarfus98! -e PROD_SECURITY_TOKEN=n6KA9eRd1xXorLj7QTDNwUYkk -e  KAFKA_BOOTSTRAP_SERVER=pkc-57q33g.westeurope.azure.confluent.cloud:9092 -e SECRUITY_PROTOCOL=SASL_SSL -e SASL_MECHANISM=PLAIN -e SASL_USERNAME=HTFLXZ73ZZX7BTHL -e SASL_PASSWORD=J6rrH4436iu1jH13pAaJ+g7VBFQPtOACXS67D4qunEhIW+7FU3v83BKwrGZu3ykE -e SESSION_TIMEOUT_MS=45000 salesforce-listener:latest
```

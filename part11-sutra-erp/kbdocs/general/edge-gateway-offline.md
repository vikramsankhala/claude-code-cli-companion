# Edge gateway shows offline

## Symptoms

Telemetry stops for every machine on one line; dashboards show the gateway as offline; alerts stop.

## Causes

Most often the gateway lost its network uplink or its certificate expired. Less often the MQTT broker on the gateway ran out of disk.

## Resolution

Check the uplink, then renew the device certificate with `sutra-edge cert renew`. Clear old buffers if the disk is full. Buffered readings upload automatically once the gateway reconnects.

# Trainer companion experiment

The rider pairs a phone with their passport, connects the trainer on the phone and launches a supported app from the catalogue. The browser and phone communicate with the Open Fitness service over HTTPS. Apogee is the first participating riding app. Live device access, app sign-in and permission to save a ride are independent.

## Implement in a riding app

1. Use an HTTPS launch URL you control. Read the fragment `#of_trainer=<code>` on arrival, then remove it with `history.replaceState`. Treat the code as a secret. Keep it out of analytics, referrers and logs. A launch without a code uses your usual device setup.
2. If `of_launch=signin` accompanies the grant, keep the grant in this tab across the normal passport sign-in redirect. A sign-in-enabled launch has up to 15 minutes to claim the trainer. Other grants expire after two minutes. From the registered launch origin, POST JSON `{"code":"…"}` to `https://openfitness.apogee.training/v1/trainer/claim`. Each code can be used once. The response contains `token`, `name`, `caps`, `accessories` and `cursor`. Clear the stored grant on claim or expiry. Keep the ride token in memory. Send requests with credentials omitted.
3. POST `{"cursor":0}` (use the cursor from the claim) to `/v1/trainer/ride` on the same API host with `Authorization: Bearer <token>`. Poll about four times per second and use each response's cursor for the next poll. Events contain a `key` in service/characteristic form and `bytes`, an array of unsigned octets. Decode only channels present in `caps`. FTMS indoor bike data is `1826/2ad2`. Cycling power, cadence and trainer-provided heart rate can also be present. Readable features and ranges are in the capability values.
4. When `1826/2ad9` is present, request FTMS control by posting `{"command":[0],"cursor":…}` to the ride endpoint. Wait for the physical trainer's matching control-point indication before sending the next command. The HTTP response only confirms queueing. Continue polling with the measurement cursor. Apogee uses this for ERG watts, simulated gradient, resistance, start, pause and stop. Trainers vary in which commands they accept.
5. On exit, post `{"end":true}`. Launching another catalogue experience invalidates the old ride token. An idle browser loses the session after seven seconds. The phone stops forwarding commands on disconnect and attempts an FTMS stop on ending a controlled session. If the browser loses the connection, show a disconnected state and invite the rider to relaunch.

Once implemented, select the trainer companion checkbox when submitting your catalogue listing. Launch origins must match exactly. A rider can unlink their phone from the Trainer companion page in their passport account menu.

## Heart-rate straps and controllers

The optional `accessories` object in the claim and each ride poll describes the current devices. Missing slots mean disconnected. An older companion supplies an empty roster. A strap or controller can join or leave mid-ride. Keep the trainer connected through those changes.

| Slot | Protocol | Notification key | Payload |
|---|---|---|---|
| `hr` | `hr` | `hr/measurement` | Standard Bluetooth Heart Rate Measurement bytes, including the flags byte. |
| `controller1`, `controller2` | `obc` or `zwift` | `controller/buttons` | The original OpenBikeControl button notification or a supported Zwift plaintext input frame. |

For example, the roster may contain `{"hr":{"id":"strap-1","name":"Chest strap","protocol":"hr"}}`. An event from this strap looks like `{"key":"hr/measurement","source":"hr","id":"strap-1","bytes":[0,145]}`. Match both slot and connection ID against the latest roster before decoding. Discard stale frames and clear held buttons on disconnect. Apps choose which supported actions to map and should handle repeated button reports. A phone completes controller subscription and startup locally. Only the trainer FTMS channel accepts commands from riding apps.

## Implement in a phone companion

1. The rider requests a five-minute pairing code in their passport. POST `{"code":"ABCDE-F0123"}` to `/v1/trainer/pair`. Save the returned `phone_token` in device-private storage. The rider can unlink or replace the phone from their passport.
2. POST to `/v1/trainer/phone` with the phone bearer token. Include trainer `name`, `caps`, the current `accessories` roster, `events`, `epoch` and the last accepted command ID (`accepted`). Use a fresh opaque accessory ID per device connection. Report an empty trainer name when disconnected.
3. A reply includes `epoch`, `app` and optional `command:{id,bytes}`. On epoch change, clear buffered events, release old trainer control and reset command tracking. Forward current events only for the active epoch. Write each fresh command at most once and deliver the physical control-point indication to the ride. Never replay a stale command after a reconnect.
4. Keep the phone app open. Stop control on foreground exit, loss of the relay or trainer disconnect. End the session with `{"end":true}`. The relay expires an inactive ride after seven seconds and marks a phone offline after ten seconds.

## Testing scope

The Android APK requires Android 12 or newer. Keep the phone app and riding tab active. The relay needs internet on both devices. It persists the linked phone credential digest and holds live readings and commands in memory. Trainer control, strap readings and button support depend on the services and firmware the equipment exposes. [Companion downloads and setup](https://openfitness.apogee.training/companion).

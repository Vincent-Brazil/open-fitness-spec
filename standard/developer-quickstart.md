# Connect your app to a rider passport

Start with one thing your riders already do. A workout app can use their FTP to set a target. A cycling game can save the effort when they finish. A training journal can pick up rides from both.

The public service is https://openfitness.apogee.training. Use the [exchange specification in Markdown](https://openfitness.apogee.training/standard/contract.md) for the API contract and the [runnable Python example](../examples/passport_quickstart.py) to test one feature. A catalogue listing needs no integration. Sign-in and passport data sharing are independent.

## Continue with Open Fitness

Put **Continue with Open Fitness** on your app’s sign-in screen. A rider with a passport can use their usual sign-in method, including Apple or Google if linked. Your app gets its own stable rider ID. You can offer this even if your app never reads a training profile or saves a ride.

1. [Register your app](https://openfitness.apogee.training/studio/app/new). Expand **Add Continue with Open Fitness**, enter `http://127.0.0.1:8765/signin/callback` as the sign-in callback and save the draft. Copy the **Sign-in client ID** from My apps.
2. [Download the example](../examples/passport_quickstart.py) and run `python passport_quickstart.py YOUR_CLIENT_ID signin`. Approve the sign-in in your browser. The terminal should say **Passport identity verified for this app**.
3. In your own backend, start the browser flow at `/signin/authorize` and redeem the code at `/signin/token`. The example’s `connect` and `run` functions show state, PKCE and identity checks. Use a registered HTTPS callback for your deployed app.
4. Look up the verified `(iss, aud, sub)` in your account store. Create a session for a returning rider. For a new rider, offer to create an account or sign in to an existing app account to link it. Bind a linking attempt to that authenticated account and reject an identity already linked elsewhere.

[Read the sign-in request and response contract](training-v0.2.md#continue-with-open-fitness). To add optional ride sharing, offer **Connect passport** inside the app and follow the data example below.

## Try a connection with your own app ID

1. [Register an app](https://openfitness.apogee.training/studio/app/new) with your rider passport. Enter your launch URL and listing details. To try the API, expand **Add a passport connection**. You can test a private draft immediately and submit it for catalogue review when you’re ready for riders to find it.
2. For this example, register the exact callback `http://127.0.0.1:8765/callback`. Select **FTP (W)**, **Save completed rides** and **Ride history** if you want to try all three commands. Save the draft and copy the **Passport client ID**.
3. [Download the Python example](../examples/passport_quickstart.py). It uses the Python 3 standard library and opens the consent screen in your browser. Use a test passport for synthetic rides. Your own passport can also connect to a listing you own. In the [rider passport](https://openfitness.apogee.training/profile), open **Edit training profile** and enter a test FTP such as 240 W.
4. In the download folder, replace `YOUR_CLIENT_ID` with your draft’s ID and run whichever command you want to try.

```shell
python passport_quickstart.py YOUR_CLIENT_ID settings
python passport_quickstart.py YOUR_CLIENT_ID ride
python passport_quickstart.py YOUR_CLIENT_ID history
```

**Settings** asks for FTP and prints `Passport FTP: 240 W` for that fixture. **Ride** asks for write access and sends the same 15-minute sample twice. Both receipts should have the same `ride_id`, and the test passport should show one ride. **History** asks for read access and prints each ride’s ID, date, source label and duration. Each run asks for one permission and replaces the preceding approved grant for that client and rider.

The example connects to the public passport by default. If you run a local passport on port 5810, register the app and rider on that instance and add `--local` to the command. For your deployed app, use a separate registration with its HTTPS callback. Saving an edit to an existing registration revokes its rider grants.

## Show a passport picture

Select **Profile picture** in your registration and request `picture` when the rider connects. If they grant it, call `GET /v1/profile/picture` with the bearer token. Display the returned JPEG data URL or use initials when `picture` is null. Keep it in memory and refresh on profile open. See the [picture contract](training-v0.2.md#profile-picture).

## Offer Strava delivery

Link riders to `/profile/strava` on the passport host to connect or manage Strava. With the rider’s `write` grant, `GET /v1/sharing/strava` reports whether forwarding is available for your app and whether it is on. Use the same bearer token you use to save rides. Pass an optional `delivery_key` (normally your source ride ID) to check your own delivery. A completed receipt includes its Strava activity ID.

If your app records its own rides and has no Strava uploader, select **Offer Strava forwarding** under its passport connection. Keep sending rides with stable IDs as usual. Riders connect Strava from their passport. Open Fitness includes your app name in the title and its catalogue launch URL in the activity description. Apogee also uses the shared uploader for its own results button, so one ride shared both ways to the same Strava athlete has one receipt. A summary-only grant shares a summary. A detailed route may include a public course link. Apps that import another app’s rides or upload to Strava themselves should leave this option off.

## Pick the permissions your feature uses

| When in your app | Request | Call |
|---|---|---|
| [Before a workout](#use-settings-before-a-ride) | Any of `ftp`, `max_hr`, `hr_zones`, `weight`, `units` | `GET /v1/training` |
| [When a rider saves an activity](#send-rides-automatically) | `write`. Add `detail_write` for workout detail and `hr_write` for average heart rate | `POST /v1/activities` |
| [When opening or refreshing history](#read-shared-history) | `history`. Add `detail_read` for contributions, then `hr_read` for average HR or `ftp` for ride-time FTP | `GET /v1/history` |
| [After a rider accepts an FTP test](#offer-to-save-an-ftp-test) | `ftp_update`. Add `ftp` to show the current value | `GET /v1/training` then `POST /v1/training/ftp` |
| When displaying FTP changes over time | `ftp_log` | `GET /v1/training` |

A catalogue listing needs only a launch URL and listing details. A file-exporting app can document its FIT, timed GPX or cycling TCX export and direct riders to **Import a ride** in their passport.

## Connect from your own code

The public API origin is `https://openfitness.apogee.training`. The downloadable example’s `connect` function implements the handshake. The same requests work from other languages.

1. When the rider chooses **Connect passport**, generate a fresh random state and PKCE verifier. Keep them with the signed-in app account for this attempt. Open `GET /oauth/authorize` in the browser with `client_id`, the exact `redirect_uri`, space-separated `scope`, `state`, `code_challenge_method=S256` and `code_challenge`. The challenge is the unpadded base64url encoding of the SHA-256 digest of the verifier. [PKCE specification](https://www.rfc-editor.org/rfc/rfc7636)
2. In the callback, verify the state and the account that started the request. For `error=access_denied`, return to the app. On success, exchange the single-use code within two minutes. Send `POST /oauth/token` as form data with `grant_type=authorization_code`, `client_id`, `redirect_uri`, `code` and `code_verifier`.
3. Read `access_token` and the space-separated `scope` from the token response. Enable only the features the rider approved. API requests use `Authorization: Bearer <access_token>`. JSON writes also use `Content-Type: application/json`. This is a public-client flow.
4. For background sync, store the token securely with the rider’s app account. The token and training responses include a stable `subject` for this passport **within your client**. When the same rider reviews permissions, preserve their chosen settings source for fields still shared. Keep pending rides and cursors scoped to the connection. On a switch to another passport, start a fresh sync. Browser clients can call the API from the registered callback origin with fetch credentials set to `omit`.

## Use settings before a ride

Convert your measurements once before upload. Ride distance is metres, body weight is kilograms and height is centimetres. Read the optional `units` preference to display metric or imperial history. A rider changing display units keeps the same stored measurements. [Measurement contract](training-v0.2.md#measurements-and-display-units)

With only `ftp` approved and set, a training response can look like this.

```json
{"subject":"example-rider-in-your-app","shared":{"ftp":240,"ftp_revision":7}}
```

Show the rider how the shared settings compare with their local settings. If they choose the passport, refresh before starting the workout. A 75% interval at 240 W targets **180 W**. Keep that starting FTP with the ride. An absent field can mean unset or unshared, so keep the app’s current value. Heart-rate bands include both limits in bpm. Apply them automatically only when your app can represent the rider’s zone model.

## Record a game without distance

A balloon game can send this completed activity with `write detail_write`. The same source ride ID makes retries safe.

```json
{"source_ride_id":"balloon-round-7","started":"2026-11-17T09:00:00Z","duration":600,"power":150,
 "revision":1,"details":{"kind":"game","title":"Balloon sprint","timer_s":600,"work_kj":90,
 "achievements":[{"name":"Balloons inflated","score":12,"unit":"balloons"}]}}
```

The passport can compare time, measured watts and mechanical work across apps. A measured average of 150 W over the full 600 seconds gives 90 kJ. Use the duration covered by the power measurements and exclude pauses. Omit work when coverage is unknown. Game scores retain the source app’s meaning. Omit distance and ascent when the activity has neither. For a route, send elevation actually gained in `details.ascent_m`, including a measured zero on a flat route.

## Send rides automatically

When your app saves a completed or rider-ended effort, queue its stable recording ID and payload alongside the local save. A background worker can send the following JSON to `POST /v1/activities` and mark it delivered after receiving the receipt.

If you share detailed efforts, set `details.power_source` when you know how the watts were obtained. A crank power meter can supply `measured` watts. Power inferred from wheel speed is `estimated`. Leave older records with an undocumented method unclassified. [Power provenance](training-v0.2.md#power-provenance)

```json
{"source_ride_id":"ride-42","started":"2026-01-15T09:00:00Z","duration":900,"distance":6000,"power":180}
```

The minimum is a source ID, start time with UTC offset and duration in seconds. Distance is metres and power is average watts. Omit missing measurements. Keep the same source ID and start time across retries, restarts and backfills. A new ride returns 201. A repeat or matched ride returns 200 and its existing ID. Tell the rider if connecting also sends earlier activities.

With `detail_write`, send a positive integer `revision` and a `details` object in the same envelope. For example, a ride with 15 minutes of pedalling and a two-minute pause can carry `"duration":1020` and `"details":{"timer_s":900,"elapsed_s":1020,"ftp_w":240}`. Keep the same revision for an identical retry. To correct or enrich that recording, increment its revision and send the full contribution. Each app owns its contribution. [Training field schema](training-v0.2.json)

## Read shared history

Start with `GET /v1/history?after=0&limit=100`. Each page contains `rides`, `next_cursor` and `has_more`. Insert or update each ride by its passport `id`, preserve its `sources`, and save the returned cursor **after** saving the page. Continue while `has_more` is true. On the next refresh, resume from the saved cursor. Use the returned cursor even when rides appear in a different date order.

A corrected ride can return on a later page with the same ID. An entry can have several sources, including file imports. Display it once and keep imported history out of the app’s outgoing ride queue. If a rider authorises additional read fields, restart from zero to pick up newly visible detail on older rides.

## Offer to save an FTP test

After the rider accepts a measured result, read `shared.ftp_revision` from `GET /v1/training`. Show the proposed change and ask whether to save it to the passport. Send the revision the rider reviewed, the actual test time and its source ride ID.

```json
{"watts":255,"method":"ramp","effective_at":"2026-01-16T10:00:00Z","source_ride_id":"test-43","expected_revision":7}
```

Post that JSON to `/v1/training/ftp`. Retry an interrupted submission with the same test ID and content. A reader with `ftp_log` can now show the dated change from 240 W to 255 W, and the earlier ride still carries 240 W.

## Handle errors and check your integration

| Response | What the app should do |
|---|---|
| 400 | Correct the callback, requested scopes or invalid payload field identified by the error. |
| 401 | For a token exchange, start a fresh connection attempt. For an API call, stop using that bearer token and offer to reconnect. |
| 403 | Check the granted scopes. Leave the affected feature off and let the rider review permissions. |
| 409 | For a ride, check source ID, start and revision. For FTP, read the current revision and show the conflict before proposing a change again. |
| 429 | Pause requests for this grant. Honour `Retry-After` when available. The service allows 120 API calls per minute per grant. |
| Timeout or 5xx | Keep the pending operation and retry with backoff using the same recording or test ID. |

Before submitting the listing, try granting FTP while declining weight, replaying a saved ride after restarting your app, and revoking access from the passport. For a two-way integration, connect a second test client as a history reader. It should see one attributed ride, and its own read token should receive 403 on a write. Record which capabilities you tested in the listing so riders know what will carry across. [Full specification](open-fitness-v0.1.md) · [Apogee integration](https://openfitness.apogee.training/apps/apogee) · [Publisher studio](https://openfitness.apogee.training/studio)

## Carry rider measurements and full ride recordings

Request `height` only if your app uses it. To show current FTP W/kg, request both `ftp` and `weight` and read `shared.ftp_w_per_kg` from /v1/training. For past efforts, use the weight stored with the source ride. Offer riders a preview before filling an empty passport with confirmed app settings.

A recorder can start with a basic ride and add training-load method, power zones, ride-time weight, samples, laps or original files independently. In a test rider, send the [recording example](training-v0.2.md#recordings-laps-and-downloads) twice. Check that a second client sees one ride, can download its TCX, and receives only the channels its own rider grant allows. Update the rider's current weight and check that the old ride's W/kg stays fixed. Omit unavailable older recordings during backfill.

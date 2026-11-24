# Training exchange · draft v0.2

An app can offer passport sign-in, training data exchange or both. For training data, use the rider authorisation, bearer token and revocation rules in the cycling exchange. Ask for each field the app needs. Existing grants retain their original permissions.

### Optional live trainer connection

A web riding app can register its HTTPS launch URL for the [experimental phone companion handoff](https://openfitness.apogee.training/trainer/guide). A signed-in rider launching that listing with an online trainer receives a one-time, origin-bound grant. Claiming it gives the ride access to live equipment for that session. Persisting ride history and reading passport fields each require their own consent.

### Continue with Open Fitness

Sign-in is an optional capability available to every registered app. A developer registers an exact **sign-in callback** in My apps and uses its **sign-in client ID**. A private draft can test sign-in. Catalogue publication is a separate review. Use HTTPS for a web app. A native app can register `http://127.0.0.1/signin/callback` or `http://[::1]/signin/callback` without a port and open its own listener on a free port. Supply the runtime URL, including the assigned port, at authorization and token exchange. Only the port may vary. Callbacks with an explicitly registered port keep exact matching. Queries, fragments, wildcards and credentials are excluded.

* **Start** at `GET /signin/authorize` on the passport issuer with `client_id`, `redirect_uri`, `response_type=code`, `state`, `code_challenge_method=S256` and `code_challenge`. Generate state from 32 random bytes encoded as unpadded base64url (43 characters). Generate a fresh 43–128 character base64url verifier. The challenge is unpadded base64url of SHA-256 of the ASCII verifier. Bind the state, verifier, callback and intended action to the app browser session.
* **Return** to the exact callback from the accepted request with `state` and either `code` or `error=access_denied`. The app must verify and consume the stored state for this browser before exchanging a code or acting on a cancellation. Codes expire after 120 seconds, are single-use and bind to that client, callback and challenge.
* **Exchange** from the native app or the web app backend with `POST /signin/token` on the configured issuer using `application/x-www-form-urlencoded`. Send `grant_type=authorization_code`, `client_id`, `redirect_uri`, `code` and `code_verifier`. A successful JSON response contains only `iss` (issuer origin), `aud` (registered sign-in client ID) and `sub` (32-character opaque base64url subject). Invalid request parameters return HTTP 400. An expired, used or unproven code returns HTTP 401.
* **Identify the rider** only from the direct exchange with the trusted issuer. Require the expected issuer and audience, then look up `(iss, aud, sub)`. The subject is stable for the life of the passport and app registration and differs between apps. A returning rider may use any linked passport sign-in method. Link to an existing local account only after that rider authenticates to it and confirms linking. Never infer a link from a name or email address.
* **Data access** is a separate rider decision. Sign-in issues no access token, requests no scopes and leaves existing data grants alone. The sign-in subject and the data-grant subject have independent lifecycles. Apps offering sync use the data flow below from the rider’s authenticated app account.

### Profile picture

An app may register and request the optional `picture` permission. Riders upload or remove a picture in their passport and choose access per app. `GET /v1/profile/picture` requires the current bearer grant. The response is `{"picture":null}` when the rider has no picture, or a `picture` string with a 256 × 256 JPEG encoded as a base64 data URL. A missing permission returns 403 and an invalid or revoked token returns 401. Treat the picture as private. Refresh it when displaying the profile and discard it on removal, loss of permission or account switch. Sign-in never returns a picture.

### Strava forwarding

An original activity writer may select **Offer Strava forwarding** in its registration and request `write`. This declares that the app sends only its own recordings and leaves all Strava uploads to the passport. Apps operating an independent Strava uploader leave it off. Apogee's results button instead uses the same Open Fitness uploader as the passport. Both paths supply the same source upload reference and share a durable receipt per Strava athlete. The button works with an Apogee account alone. Riders enable the destination separately. Only new, unambiguous rides started after connection are eligible. Replays, merged contributions and file imports do not enqueue an upload. Where samples are available the service forwards a TCX with permitted cycling measurements, excluding heart rate and location. The activity title identifies the source app. Its description includes public links to the app and Open Fitness. With detailed sharing, an Apogee route can provide a public course identifier in `details.course_id`. For a ride without eligible samples the service creates a summary activity with elapsed time and optional distance. An uncertain delivery is held for inspection.

### Training data

| Operation | Permissions and behaviour |
|---|---|
| GET /v1/training | Returns a pairwise subject and a shared object. Optional fields are ftp (watts), max_hr (bpm), hr_zones, weight (kg), height (cm) and units. Each requires the matching scope. Missing values are unknown. |
| Structured heart-rate zones | Ordered labelled bands with inclusive min_bpm and max_bpm. source is entered or derived. Apps can display any model and apply a compatible model after rider approval. |
| POST /v1/activities | With write, use the v0.1 envelope. With detail_write, add a positive integer revision and details. hr_write also authorises average HR. Detail sharing includes the FTP used on the ride, if supplied. |
| GET /v1/history?after=0&limit=100 | Requires history. Returns rides, next_cursor and has_more. Save the cursor after processing the page. Upsert by passport ride id. Each contribution carries its client_id and revision. detail_read enables contributions, hr_read enables HR and ftp enables the ride's starting FTP. |
| GET /v1/training with ftp_log | Includes dated ftp_history with watts, method, client_id, source_ride_id and revision. A legacy baseline may have no date. |
| POST /v1/training/ftp | Requires ftp_update. After rider acceptance send watts, method, effective_at, source_ride_id and expected_revision from GET /v1/training. A matching retry succeeds. A conflict returns 409. Reload and show the rider the new value before trying again. |

For example, a workout that ran for 30 minutes with a five-minute pause can send this activity. A second app reading history receives the details inside the original app's contribution.

```json
{
  "source_ride_id": "morning-ride-28",
  "started": "2026-11-17T08:00:00Z",
  "duration": 2100,
  "revision": 1,
  "details": {
    "title": "Morning intervals",
    "kind": "workout",
    "completion": "completed",
    "timer_s": 1800,
    "elapsed_s": 2100,
    "ftp_w": 240,
    "power_source": "measured",
    "best_watts": {"300": 210}
  }
}
```

[Measurement and test schemas](training-v0.2.json). Time fields use seconds. timer_s excludes pauses and elapsed_s includes them. Preserve an older timer-only record as such. best_watts keys are durations in seconds and values are best average watts for a complete recorded window. power_coverage is the fraction of timer time covered by power readings. Omit unavailable measurements. Source-specific achievements have meaning under the issuing app's rules.

### Power provenance

A writer with `write detail_write` may send `details.power_source`. It describes the inputs to that recorder’s ride-average watts, normalised power and best-effort watts. Readers with `history detail_read` receive it on the individual contribution.

| Value | When to use it |
|---|---|
| `measured` | All contributing watts came from equipment known to measure rider output, such as a crank power meter. Averaging those readings still counts as measured. |
| `estimated` | Some or all contributing watts were inferred, for example from wheel speed and a resistance curve. |
| `unknown` or omitted | The recorder cannot establish the method. Use this for legacy records and imports without reliable provenance. |

A trainer connection, file format or complete sample coverage alone cannot establish the method. Target watts and simulation inputs are not rider efforts. Keep provenance local to each recorder when apps contribute to the same ride. For a measured-only personal best, filter contributions **before** choosing the highest watts for each duration. A higher estimate or an unclassified effort can still appear in an all-sources view.

To classify previously unclassified watts, send a full, higher revision of the contribution. A fill-only backfill preserves the existing classification. Adding watts of a different classification to existing watts in a fill-only backfill returns 409.

### Updating a contribution

Send the same source_ride_id when enriching an existing ride. A higher revision replaces that source's detailed contribution. Replaying an identical revision is idempotent. Older revisions leave the latest contribution intact. Reusing a revision with different data returns 409. Later FTP tests must be at least as recent as the latest effective date. Other contributors retain their data. Record the settings used during each ride independently of later profile changes. Keep imported history attributed to its original app and out of the outbound ride queue.

## Efforts without a route

Distance and elevation are optional. A cycling game can send duration, average measured power and a `kind: game` detail. Mechanical work is the sum of watts × observed seconds divided by 1000, in kJ. Keep native outcomes in `details.achievements` with the issuing app, score and unit. Do not convert scores or work into kilometres or climbing. When work is absent, the passport can calculate it from one contribution’s average power and timer if power_coverage is 1. A missing metric is unknown or inapplicable. A numeric zero is a reported measurement. In history totals, count a matched session once and report how many sessions contributed to each metric. [Balloon game payload](https://openfitness.apogee.training/standard/quickstart?feature=full#record-a-game-without-distance)

## Measurements and display units

A source app converts measurements to the field units below before sending them. A reader interprets each field in those units, even when the rider selects imperial. Apps do not need to discover the source app’s screen settings.

| Measurement | Exchange unit |
|---|---|
| Profile weight, weight history, ride-time weight | Kilograms |
| Profile height | Centimetres |
| Ride distance, recorded distance, altitude and ascent | Metres |
| Recorded speed (`speed_kph`) | Kilometres per hour |
| Duration, sample and lap offsets, time in zones | Seconds |
| Power and FTP, heart rate, cadence, work | Watts, beats/min, rev/min, kilojoules respectively |
| Power-to-weight | Watts per kilogram in both display systems |

Request the optional `units` permission to receive `shared.units` on the profile or training endpoint. Its values are `metric` and `imperial`. When reading an older provider, accept case-insensitive Metric/Imperial and the legacy kg/lb aliases. If the preference is missing, unknown or withheld, use your app’s local display preference. Treat a change as a display change. Keep the original file and canonical numbers, including past rides and dated body weights.

For example, a 10-mile ride is sent as `"distance": 16093.44`. A reader can show 10.0 mi or 16.1 km. An entered 150 lb is sent as 68.0388555 kg. Use 1 mi = 1609.344 m, 1 lb = 0.45359237 kg and 1 in = 2.54 cm. Round only the displayed result.

## Body measurements and starting settings

Weight and height are optional and separately permissioned. With both `ftp` and `weight`, the training response also returns `ftp_w_per_kg` if both measurements exist. `weight_log` returns `weight_history` entries with kg, effective_at and client_id. Null kg marks a cleared measurement. An undated baseline has null effective_at. It cannot establish the weight used on a particular ride.

When the rider explicitly confirms values in the app, POST a JSON object to `/v1/training/initial` with `profile_seed` and each included field's scope. Supported keys are ftp, weight, height, max_hr, hr_zones and units. Only empty fields are filled. An identical retry succeeds. A differing stored value returns 409 so the app can refresh the preview. A rider can edit or remove settings in the passport.

## Detailed measurements

All additions are optional. Include only values supported by the saved record.

| Detail field | Meaning |
|---|---|
| `weight_kg`, `weight_source` | A positive body mass at ride time and its source, entered, measured, passport or saved_setting. Apogee uses saved_setting for a non-default historical ride setting whose entry method is unknown. Saving uses `detail_write` and `ride_weight_write`. Reading uses `history`, `detail_read` and `ride_weight_read`. Use the same contribution's power and weight for historical W/kg. |
| `normalized_power_w` | Normalised power in watts, calculated from observed 30-second rolling means using the fourth-power method. |
| `training_load` | Object with method, nonnegative score and boolean estimated. Apogee sends power_tss, calculated as 100 × moving hours × (normalised watts / ride FTP) squared. Compare scores from compatible methods. |
| `power_zones` | Ordered bands with label, inclusive min_pct, exclusive max_pct (null for an open top), and observed seconds. Include the reference ftp_w. Unknown time stays outside the bands. |
| `ascent_m` | Elevation gained over the ridden portion, in metres. A source can add `ascent_source: "saved_route_profile"` when recovering gain from historical course elevations up to the rider’s saved distance. Omit gain when that section cannot be recovered. |

To fill absent details without reading private history, send `merge_details: true` with details and omit revision. The passport assigns a new source revision only when values are added. A previously saved value takes precedence. Use the explicit revision protocol for corrections. Each detailed contribution can include its own average power.

## Recordings, laps and downloads

A writer with `write recording_write` can include a top-level `recording` in POST /v1/activities. This is independent of detail_write. The measurement schema includes the recording object. Each sample starts with seconds since the ride start and has one number or null per named channel. Use clock timer for pause-excluded offsets or elapsed for wall time. Sample times increase strictly. Laps use non-overlapping start_s and end_s on the same clock. No interpolation is implied. The request limit is 5 MiB, including the activity envelope. A recording accepts up to 86,401 samples. Apps can add channels to an identical source recording in a later grant.

```json
{"source_ride_id":"workout-7","started":"2026-11-17T07:30:00Z","duration":60,
 "recording":{"clock":"timer","channels":["power_w","cadence_rpm"],
 "samples":[[0.5,180,84],[1.5,null,83]],"laps":[{"label":"Warm-up","start_s":0,"end_s":60}]}}
```

| Operation | Permission and response |
|---|---|
| Read samples and laps | GET /v1/history with history and recording_read includes recordings with id, app, samples and laps. GET /v1/recordings/{id} returns started, clock, channels, samples and laps. Append ?format=tcx for a cycling TCX file. |
| Sensitive channels | Sending hr_bpm requires trace_hr_write. Sending lat or lon requires location_write. The reader needs trace_hr_read or location_read respectively. Missing grants strip those columns from both JSON and TCX. Average HR permissions are independent. |
| Keep an original | After getting the ride receipt, POST multipart file and source_ride_id to /v1/activities/{ride_id}/original. Use a FIT, timed GPX or cycling TCX for the same start, within two seconds. Requires write, original_write, trace_hr_write and location_write. Original bytes can contain private extensions and cannot be redacted. A byte-identical retry returns the existing digest. |
| Read an original | GET /v1/history with history, original_read, trace_hr_read and location_read lists originals with name and digest. GET /v1/originals/{digest} with the same permissions returns the original bytes. |

A rider can delete one ride from the passport ride log. Its contributions, recordings and original files are removed together. Separate FTP and weight history entries remain. Incremental history pages include `deleted_ride_ids` for removals after the supplied cursor. Discard cached copies for those IDs and advance the cursor even on pages containing only deletions. Clients using earlier servers can treat an absent deletion list as empty.

Riders can download each ride's summary, its TCX when samples exist, and any attached originals. Their full ZIP includes the JSON recordings, the profile and weight and FTP histories. TCX exports from a timer-clock source use the ride start plus timer offsets. Use the JSON clock and nulls for analysis sensitive to pauses or missing data.

## Personal workout library

A rider adds a structured cycling workout under **Rider passport → My workouts → Add workout** by choosing a ZWO file. The passport keeps the original XML, including workout steps, power targets, cadence cues and text events. Power targets in ZWO are fractions of FTP. Reading a workout does not grant access to the rider’s FTP. A riding app can use its local FTP or request the existing `ftp` permission separately.

Register `workouts_read` as a passport data scope. Use the normal OAuth authorization-code flow with S256 PKCE, then send the granted bearer token with both requests. One grant lets that app read the rider’s whole private library, including future additions. The rider can turn off workout access for that app under **Apps with access**.

1. When the rider opens the app’s workout picker, call `GET /v1/workouts`. The server returns up to 100 workouts. For another page, send the URL-encoded opaque `next_cursor` as `?after=…`. A null cursor ends the listing. Refresh from the first page when the picker reopens.
2. Show each `name`. When the rider chooses a workout, fetch its `download_url` from the same passport issuer, with the same bearer token. The response is the original ZWO bytes as an `application/xml` attachment. Parse it with the app’s ZWO reader and run it locally. IDs are opaque and scoped to the passport server.
3. A missing workout or a workout belonging to another rider returns 404. An absent or revoked token returns 401. A valid token without the scope returns 403. Apps can continue using local workouts in each case. Older servers without this optional endpoint can return 404.

Example request and response for a synthetic rider:

```http
GET /v1/workouts HTTP/1.1
Authorization: Bearer EXAMPLE
```

```json
{"workouts":[{"id":"example-tempo","name":"Morning tempo","download_url":"/v1/workouts/example-tempo/file"}],"next_cursor":null}
```

`GET /v1/workouts/example-tempo/file` with the same bearer returns:

```xml
<workout_file>
  <name>Morning tempo</name>
  <sportType>bike</sportType>
  <workout>
    <Warmup Duration="300" PowerLow="0.45" PowerHigh="0.70"/>
    <SteadyState Duration="600" Power="0.80" Cadence="90"/>
  </workout>
</workout_file>
```

An empty library returns `{"workouts":[],"next_cursor":null}`. Re-uploading identical ZWO bytes creates one library entry. Removing a workout stops subsequent downloads. The grant offers read access only. Saving the completed ride uses the existing, separately granted `write` flow.

## Move a rider passport

The rider downloads **Export my data** on the source server and chooses **Account settings → Restore from passport ZIP** on the destination passport. The destination adds missing rides, their original source labels, contributions, recordings, attached activity files, FTP and weight history, and saved workouts. Settings and a picture supplied by the archive update those fields. Existing rides and workouts are kept. The rider signs in and consents to connections on the destination. Restore does not enqueue rides for external delivery.

Version 1 stores `format_version: 1`, the issuing server’s `origin`, `profile`, `activities`, `sources`, `source_apps`, `ftp_history`, `weight_history` and `workouts` in `profile.json`. Each activity’s `id` joins its source rows through `ride`. Its optional `primary_source` selects the primary source app. The `source_apps` map records the original issuer, client ID and display name for attribution across moves. Restore assigns destination-local IDs. Issuer and client labels in an uploaded file confer no authority to act for an app.

Optional ZIP entries include `profile-picture.jpg`, `recordings/{id}.json` (with source app, source ride ID, clock, channels, samples and laps), and `originals/{first 12 hex digits of digest}-{name}` referenced by activity metadata. Each workout manifest entry supplies `digest` (lower-case SHA-256 of the original bytes) and `filename`. Its file is `workouts/{digest}.zwo`. Verify file digests and apply a restore atomically. Replaying the same archive leaves the destination unchanged. The reference server also accepts earlier exports without a format version or workout list. Its restore limits are 64 MiB zipped, 192 MiB expanded, 32 MiB per member and 10,000 members.

# Open Fitness cycling exchange

**Draft v0.1 · 18 November 2026.** This specification lets an independent app share one rider’s completed cycling effort or read information that rider approves. A rider can try another app without abandoning their history. A writer can contribute a ride without reading any personal settings.

## What an app can claim

| Participation | What the app must do | Example |
|---|---|---|
| Continue with Open Fitness | Register an identity callback and complete the [sign-in exchange](training-v0.2.md#continue-with-open-fitness). | A rider signs in to a game with their existing passport. |
| Activity writer v0.1 | Obtain a rider grant with `write`, send the activity below and keep its source ID stable on retry. | A game records a 30-second effort with no distance. |
| Profile reader v0.1 | Request only the fields it uses, check the grant and handle an absent field or an empty history. | A training app requests FTP. A journal requests history. |
| File exchange | Name the format, direction and content. A rider explicitly imports or exports the file. | “Exports a completed cycling activity as TCX” lets a rider bring an Apogee ride back. |
| Directory listing | Describe launch, availability, equipment and evidence. Indicate unknowns. | A trainer-to-gamepad bridge may have no activity to share. |

A client can implement either API role or both. Listing an app, exchanging files and adopting a controller protocol are independent choices.

## Connect a rider

1. From **List your app** in the catalogue, register your launch URL. To use the API, add an exact callback URL and the scopes your app may request. The publisher page shows your client ID. Use HTTPS, or HTTP loopback for local development. Apogee requests `write`.
2. Navigate the rider to `GET /oauth/authorize`. Send `client_id`, `redirect_uri`, an unpredictable `state`, space-separated `scope`, `code_challenge_method=S256` and `code_challenge`. Derive the challenge from a fresh, random verifier using SHA-256 and unpadded base64url. Retain state and verifier for this attempt. [PKCE specification](https://www.rfc-editor.org/rfc/rfc7636)
3. The rider chooses individual permissions. On return, match `state` to this attempt and handle denial (`error=access_denied`). Exchange the code at `POST /oauth/token` as form data with `grant_type=authorization_code`, `client_id`, `redirect_uri`, `code` and `code_verifier`. A code is single-use and expires after two minutes in the prototype.
4. The JSON response contains `access_token`, `token_type: Bearer` and `scope` (the space-separated granted subset). Use `Authorization: Bearer <token>` with the platform API. A successful connection may have zero data permissions. A new approved grant replaces the earlier one for this app and rider. A declined request leaves any earlier grant in place.

The prototype implements delegated access. It issues no ID token. For an offline or guest ride, keep the local experience usable. Offer export or ask the rider whether to sync when connected. On a shared trainer, establish which rider owns an effort before asking them to share it.

Backend and native apps can exchange the code directly. A browser-only client can use PKCE from its registered callback origin. Send the token request as form data, then send the bearer token on API calls with browser credentials omitted. The service permits CORS for the registered origin. Keep the verifier and state specific to this sign-in attempt. Native clients may register a loopback callback.

## Write one completed effort

Use `POST /v1/activities`, content type `application/json`, with a `write` grant. The service derives the rider and source app from the grant. Body fields are defined by the [activity schema](activity-v0.1.json).

| Field | Meaning |
|---|---|
| `source_ride_id` | Required string, 1–140 characters. Persist a stable ID for this completed effort within this app and rider. |
| `started` | Required date-time including seconds and UTC offset. Use capture time even when uploading later. The prototype stores UTC at whole-second resolution. |
| `duration` | Required elapsed session seconds, integer 1–604800. Use the completed session’s duration. |
| `distance` | Optional finite nonnegative number in metres. An indoor app can report the distance its engine records. Rider histories cannot compare distances across different physics as equivalent course performances. |
| `power` | Optional finite nonnegative number in watts, average over recorded rider power. Exclude missing readings and targets. Summary-only rides have unknown power provenance. Use the [training extension](training-v0.2.md#power-provenance) to distinguish measured and estimated watts. |

For unknown optional metrics, omit the field or send null. A measured zero is a value. Keep the original or source-specific data in the originating app. Coordinates, HR traces, game scores, plan targets, race positions, equipment identifiers and rider account IDs have no place in this write. A game with only a timer can send the entire request below.

The optional `premium` flag in the schema is reserved for the legacy shared-pass demonstration. Omit it for ordinary ride sharing. Imported history uses the original start and the same stable source ID as future retries. Describe backfill at consent and queue accepted ride saves durably so a transient network failure does not lose a ride.

```json
{"source_ride_id":"round-17","started":"2026-11-18T09:00:00Z","duration":30}
```

On first creation the service returns HTTP 201, for example `{"ride_id":42,"created":true}`. Retrying returns 200 with the same ID and `created:false`. The returned ID belongs to this service. Once accepted, the source ID identifies the original ride. Replays cannot edit it. Persist the payload for retries and wait for acknowledgement before marking it synced.

The prototype also reconciles a single candidate from a different source when UTC start (to the second), duration and known distance (within two metres) match. It keeps both sources. Without enough evidence it stores the separate rides and flags same-start overlaps. This heuristic can still merge coincident rides. Cross-source matching is a service policy. Clients can rely on replay identity without reproducing the heuristic.

## Read a profile

Use `GET /v1/profile` with the bearer token. A valid grant returns an app-specific opaque `subject`, granted `scopes` and a `shared` object. The token exchange also returns this subject. It stays stable when the same passport reviews this app’s permissions. An app can use it to recognise a renewed connection. Compare subjects only within the same client and service. The service omits settings that are unset or unapproved. Readers must tolerate absent optional fields and additional response metadata. [Profile response schema](profile-v0.1.json)

| Requested scope | Data returned in `shared` |
|---|---|
| `name`, `units` | Display name and preferred display units, individually selectable. Wire measurements keep their specified units. |
| `ftp`, `weight`, `age`, `height`, `max_hr` | FTP in watts, weight in kilograms, age in years, height in centimetres and maximum HR in beats/minute, selected individually. |
| `zones`, `control` | Rider-entered HR-zone text or pause-control preference. The draft provides no machine-readable zone boundaries or device pairing. |
| `history` | Newest-first cycling summaries with ID, start, seconds, optional metrics, source label and overlap indicator. The prototype also supplies file or client provenance in `sources`. No original files or raw tracks are exposed. |
| `achievements` | Cross-app stamp name, progress and target. Apps retain their own scoring rules. |
| `write` | Permission for the activity endpoint. It adds no fields to the read response. |

### Which apps contributed rides?

A reader with `history` permission can collect the distinct `client_id` values from entries in `sources` whose `kind` is `app`. Count each ride once per contributing client when sources are matched. A file-only entry identifies a file import and may have no reliable app identity. The list describes recorded contributions. An app launch, installation, or access grant alone does not establish that the rider recorded an activity there. The draft has no separate installed-app or launch-history scope.

The rider can see past contributors after revoking a grant. Current access is managed separately in the passport. An existing write-only Apogee grant continues to share summaries. The rider can review permissions to enable the v0.2 training exchange.

```json
{"subject":"opaque-to-other-apps","scopes":["ftp"],"shared":{"ftp":220}}
```

Riders revoke grants from their passport. Future reads and writes then fail. Revocation preserves the rider’s previously saved rides. Readers should discard their token and stop requesting data after a revocation. A rider can export activity summaries and their original imported files, or delete their profile.

## Files, access and errors

The prototype accepts timed GPX tracks, FIT activity sessions, and TCX v2 files containing one cycling activity with lap summaries. A course template, an untimed route or a ZWO workout prescription is not evidence that a rider completed an effort. Imported files retain file provenance. Raw files stay accessible through the rider’s own export. The hosted sandbox accepts its supplied samples only. [Garmin FIT file types](https://developer.garmin.com/fit/file-types/)

API errors contain a JSON `error` string. Use HTTP status to decide the next action.

| HTTP | What the client should do |
|---|---|
| 400 | Correct the malformed payload or invalid registration parameters before retrying. |
| 401 | Obtain a fresh grant after a missing or revoked bearer token. Restart a failed code exchange. |
| 403 | Explain the missing permission. Let the rider decide whether to reconnect. |
| 429 | Back off. The sandbox allows 120 API calls per minute per grant. |
| Network failure or 5xx | Keep the completed record. Retry the same source ID after connectivity returns. |

## Checking an implementation

| Exercise | Expected observation |
|---|---|
| Connect a writer with only `write`. | The profile has an empty `shared` object. Submit the short effort above and receive 201. |
| Resend the same payload, including after a restart. | Receive 200 and the original ride ID. History gains one effort across the two calls. |
| Connect a different client as a history-only reader. | Its subject differs. It sees the effort and receives 403 on a write. A second rider has a separate history. |
| Omit distance, then submit a distinct effort with measured zero power. | The first record retains unknown distance. The second retains zero watts. |
| Revoke one grant and retry it. | That token receives 401. Other apps keep only their own grants. |
| Import, export and re-import the same activity file. | The original bytes round-trip. One ride remains. A separate file-based publisher need not register an OAuth client. |

## Draft decisions

The URL family is `/v1` and these schema documents identify draft 0.1. Implementers should declare the draft and roles they tested. Introduce incompatible units, required fields or permission meanings in a separately versioned contract. New health fields need a separate explicit permission. Workout exchange, raw-stream access, live riders, multisport metrics and paid settlement need their own evidence before extension.

Apogee implements the writer in its own codebase. When a rider approves the connection, Apogee queues eligible trainer history and future finished rides. Retries keep the same source ride ID. Independent developers can propose changes with an example from their app. The public specification, schemas and example client use the MIT licence. [Contribute to the specification](https://github.com/Vincent-Brazil/open-fitness-spec/blob/main/CONTRIBUTING.md)

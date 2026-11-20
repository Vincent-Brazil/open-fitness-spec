# Open Fitness starter kit

Download or clone this repository and run the commands below from its root with Python 3. The examples use the standard library.

## Preview a ride on your computer

```sh
python examples/sample_ride.py game
```

This prints the JSON your app would send to `POST /v1/activities`. Preview mode runs offline and needs no account. Pick the example closest to your app:

| Example | What it carries |
| --- | --- |
| [Route](rides/route.json) | 12 km ridden and 186 metres climbed |
| [Workout](rides/workout.json) | 15 minutes of pedalling, one minute paused, and best power over two durations |
| [Game](rides/game.json) | 10 minutes, 90 kJ of work and 12 balloons inflated, with distance omitted |

## Test a real save and retry

1. Use a test rider passport to [register a private draft app](https://openfitness.apogee.training/studio/app/new). Add a passport connection with the exact callback `http://127.0.0.1:8765/callback`. Enable **Save completed rides** and **Save detailed rides and past efforts**. Save the draft and copy the **Passport client ID**.
2. Run the command below. In the browser, sign in with the test passport and approve both permissions. This writes the sample to that passport’s history.

```sh
python examples/sample_ride.py game --client-id YOUR_CLIENT_ID
```

The example sends the same activity twice. Both receipts should show the same `ride_id`, and the retry should return `created: false`. Open the passport’s ride log to see the recording under your app’s name. The supplied IDs and dates stay fixed for repeat runs. A fresh workout or route uses its own ID.

## Try another integration

The [reference client](passport_quickstart.py) also supports passport sign-in, reading an approved training setting, saving a summary ride, and reading shared history. Each feature has its own registration steps, command and expected result in the [developer quickstart](https://openfitness.apogee.training/standard/quickstart).

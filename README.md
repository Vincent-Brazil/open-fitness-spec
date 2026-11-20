# Open Fitness rider passport

A rider can share their training settings with a cycling app and bring their completed rides back to one history. A workout app might read FTP, while a cycling game might save a timed effort with power and no distance. Each app asks the rider for the permissions its feature needs.

## Start with one feature

| If your app needs to… | Start here |
| --- | --- |
| Sign a rider in | [Continue with Open Fitness](standard/training-v0.2.md#continue-with-open-fitness) |
| Use a rider’s training settings | [Read a profile](standard/open-fitness-v0.1.md#read-a-profile) |
| Save a completed ride | [Write one completed effort](standard/open-fitness-v0.1.md#write-one-completed-effort) |
| Read rides from other apps | [Read shared history](standard/developer-quickstart.md#read-shared-history) |

The [quickstart](standard/developer-quickstart.md) explains how to register a test app and run the [Python example](examples/passport_quickstart.py). The [example rider passport](https://openfitness.apogee.training/passport/example) shows how a workout, a route and a game look together.

## Specification

- [Cycling exchange v0.1](standard/open-fitness-v0.1.md) defines permissions, rider profile reads, ride writes and replay behaviour. [Ride schema](standard/activity-v0.1.json) · [Profile schema](standard/profile-v0.1.json)
- [Training exchange v0.2](standard/training-v0.2.md) adds optional capabilities including sign-in, detailed measurements, power provenance, recordings and history sync. [Training schemas](standard/training-v0.2.json)

These are drafts. Developers can propose changes or report differences between the text and a working integration. [Contribution guide](CONTRIBUTING.md)

The public specification, schemas and example code are available under the [MIT licence](LICENSE).

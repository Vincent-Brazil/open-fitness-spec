# Contribute to the Open Fitness specification

If your app records something the passport cannot express, open an issue and describe what the rider does, the value the app has, and what another app should receive. A small example with invented data is enough. For a documentation fix, open a pull request directly.

For a change to the exchange, include:

1. A sample request and the expected response, including the permission needed to share the field.
2. The unit and how to represent a missing value. Explain what happens when an older app omits the field or a writer retries the same ride.
3. The matching changes to the specification, JSON schema and quickstart where relevant. For a breaking change, propose a new version and describe how an existing app can migrate.

The maintainer reviews pull requests. A merged proposal changes the public draft. Apps can check the hosted implementation and declare the capabilities they have tested. Use synthetic riders in examples and reports.

Contributions to this repository use its [MIT licence](LICENSE).

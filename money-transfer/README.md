# Money transfer examples

Within this directory, there are two subdirectories that contain
example code that simulates moving money between accounts at two
different banks, plus another subdirectory that contains code for
a service upon which both depend.

The first, in the `normal-execution` subdirectory, is the one
included in the article. It demonstrates the inherent volatility
of normal execution, the problems that arise when the application
crashes, and how restarting the application does not solve them.

The second, in the `durable-execution` subdirectory, demonstrates
how Durable Execution enables the application to survive a crash.
Unlike the other example, it does not lose state, repeat work that
was already completed, or cause money to be lost. This example
also demonstrates the use of idempotency keys in a Temporal
application.

The `banking-service` subdirectory contains a service that simulates
API gateways at different banks. It provides APIs for withdrawing,
depositing, and viewing the current balance of bank accounts. Both
examples depend on this service to be running. The instructions for
both examples mention this and provide the command used to start it.

The recommended path is to start with the `normal-execution` example
and then run the `durable-execution` example after that. This will
enable you to observe the differences in how they react to a crash.

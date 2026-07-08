# Resilience of Durable Execution

This example illustrates how Durable Execution, provided here by Temporal,
protects application state against the same kind of crash that loses money
in the `normal-execution` example. It performs the same task: transferring \$100
from one bank account to another. The transfer runs as a Temporal workflow
that calls two activities: `withdraw` and `deposit`. Each call includes an
idempotency key so the bank can recognize and ignore a repeated request.

### Prerequisites
* These instructions use the `uv` package manager. Ensure that this is
  [installed](https://docs.astral.sh/uv/getting-started/installation/)
  and that the `uv` command is in your executable path.
  * Run `uv sync` in this directory to install any necessary Python packages.
* [Python 3.10](https://www.python.org/downloads/) or higher
* The [Temporal CLI](https://docs.temporal.io/cli#install), which provides the
  local development server used below (for example, `brew install temporal`
  on macOS).

This code has been tested on macOS (Tahoe on an Apple Silicon M2). It is
expected to work on any system with a similar configuration, as well as
slight variations (for example, macOS Sonoma, Windows 10, or Fedora Linux).

## Running the example

### Initial setup
This example relies on three long-running processes, each of which should be
started in its own terminal and left running.

First, start the banking service, just as in the `normal-execution` example:

```command
cd ..
cd banking-service
uv run python app.py
```

Second, start a local Temporal service, if it's not already running. 

```command
temporal server start-dev
```
This also makes the Web UI available at <http://localhost:8233>. You
can use this to follow the progress of the workflow execution and
see its event history.

Third, in the directory containing this `README.md`, start a *worker*. This is
the process that runs your workflow and activity code:

```command
uv run python worker.py
```

### Happy path
Open another terminal to the directory containing this `README.md` and then
run the following command, which starts a workflow that transfers \$100
between two accounts:

```command
uv run python starter.py
```

This is expected to complete successfully, so it represents the so-called
happy path. The command prints a line beginning with `SUCCESS:`. Upon
completion the source account balance has decreased by \$100 and the
destination account balance has increased by \$100.

### Premature termination
Now induce the same kind of crash that lost money in the `normal-execution`
example, this time between the `withdraw` and `deposit` steps. 

Stop the worker (press `Ctrl-C` in its terminal), then start it again with the
`CRASH_AFTER_WITHDRAW` environment variable set to `1`. This causes the 
`withdraw` activity to crash the worker *after* the bank has debited the
account but *before* Temporal records the result (on non-UNIX systems, 
you may need to adjust the command syntax to reflect your operating system's
syntax for setting environment variables):

```command
CRASH_AFTER_WITHDRAW=1 uv run python worker.py
```

Initiate another transfer:

```command
uv run python starter.py
```

The worker process will terminate immediately after the withdrawal. At this
point the source account has been debited by \$100, but the destination
account has not yet been credited — the money is in flight. The `starter.py`
command does not fail; it simply waits, because the workflow is durably
suspended on the Temporal service.

Now restart the worker, this time normally:

```command
uv run python worker.py
```

After a brief pause, Temporal retries the withdrawal. Because the retried call
carries the same idempotency key, the bank recognizes it as a duplicate and
does *not* debit the account a second time. The deposit then proceeds,
`starter.py` prints its `SUCCESS:` line, and the transfer finishes with the
source account \$100 lower and the destination account \$100 higher than when
this transfer began.

No money was lost, and none was withdrawn twice. Contrast this with the
`normal-execution` example, where the same crash left the source account \$100
short — and re-running the transfer did not fix the problem.

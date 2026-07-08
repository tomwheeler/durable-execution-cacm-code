# Resilience of Durable Execution

This example illustrates how Durable Execution, provided here by Temporal,
protects application state against the same kind of crash that loses money
in the `normal-execution` example. It performs the same task: transferring \$100
from one bank account to another. The transfer runs as a Temporal workflow
that calls two activities: `withdraw` and `deposit`. Each call includes an
idempotency key so the bank can recognize and ignore a repeated request.

### Prerequisites
* The [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package
  manager, with the `uv` command in your executable path.
* [Python 3.10](https://www.python.org/downloads/) or higher.
* The [Temporal CLI](https://docs.temporal.io/cli#install), with the
  `temporal` command in your executable path.

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

After this, open your browser to <http://127.0.0.1:9109>. You will see
a web page showing the current balances of two accounts used in this
example. As you progress through the instructions that follow, those 
balances will change in reaction to `withdraw` and `deposit` calls 
invoked by the code. You can click the **Reset All** button in the 
upper-right corner of the page to restore the original balances of
both accounts.

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
example, this time during the `deposit` step. 

Stop the worker (press `Ctrl-C` in its terminal), then start it again 
with the `CRASH_DURING_DEPOSIT` environment variable set to `1`. This
causes the `deposit` activity to crash the worker *after* the bank has
debited the account but *before* Temporal records the result.

On non-UNIX systems, you may need to adjust the command syntax to reflect
your operating system's syntax for setting environment variables):

```command
CRASH_DURING_DEPOSIT=1 uv run python worker.py
```

Initiate another transfer:

```command
uv run python starter.py
```

The worker process will terminate. At this point, the source account
has been debited \$100, which was recorded into history before the
crash, so it won't be repeated. The target account has been credited
\$100, but since the Worker crashed before it was recorded into history,
this will be repeated when the worker is restarted.

Now restart the worker, this time without the environment variable
that induces the crash:

```command
uv run python worker.py
```

After a brief pause, Temporal retries the deposit. Because the retried
call uses the same idempotency key as before, the bank recognizes it as
a duplicate and does *not* debit the account a second time. The deposit
activity succeeds, and the `starter.py` script that started the workflow
execution now reports the successful result. Despite the crash, the 
source account has a balance \$100 lower and the target account has
a balance \$100 higher than before the crash.

No money was lost, and none was withdrawn twice. Contrast this with the
`normal-execution` example, where the same crash left the source account
\$100 short — and re-running the transfer did not fix the problem.

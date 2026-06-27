# e-Book Order Example

This project is a Temporal application that processes orders for
electronic books.

## Prerequisites

* You will need the `uv` package manager. Ensure that this is
  [installed](https://docs.astral.sh/uv/getting-started/installation/)
  and that the `uv` command is in your executable path. 
* You will need Python 3.10 or higher.

* These instructions use the `uv` package manager. Ensure that this is
  [installed](https://docs.astral.sh/uv/getting-started/installation/)
  and that the `uv` command is in your executable path.
  * Run `uv sync` in this directory to install any necessary Python packages.
* [Python 3.10](https://www.python.org/downloads/) or higher
* You will also need the [Temporal CLI](https://docs.temporal.io/cli#install)

This code has been tested on macOS (Tahoe on an Apple Silicon M2),
Linux (Debian 13.4 on x86\_64), and Windows 11 (x86\_64). It is
expected to work on any system with a similar configuration, as
well as slight variations (for example, macOS Sonoma, Windows 10,
or Fedora Linux).

## Running the example

### Set up project dependencies
Open a terminal and run the following command to set up the
project dependencies:

```command
uv sync
```

### Start the Temporal service

Open a terminal and start a local Temporal service if it is not
already running:

```command
temporal server start-dev
```

### Start the worker
Next, run the following command to start the worker:

```command
uv run python worker.py
```

### Submit an order

#### Happy path
You will now place an order. The code that creates the required
input data and submits the workflow execution request to the Temporal
Service, which results in the worker processing the order, is in the
`submit_order.py` file.

Review the code if you like. Afterward, open a second terminal window 
(or tab), and then run the following command to submit the order:


```command
uv run python submit_order.py
```

The log messages that are written as the workflow and activities run
are displayed in the terminal window used to start the worker. 

#### Payment failure
The `charge_customer` activity is written to make it easy to induce
a failure on demand. Do this by creating a file named `charge.fail`
in your home directory.

After you have done so, run the following to submit a new order:


```command
uv run python submit_order.py
```

If you open your browser to <http://localhost:8233/>, you should see
that this execution is still running. If you click it in the table, 
the Temporal Web UI will display its detail page. This shows that the
activity has failed and is being retried. 

If you want to see how the application is able to survive a crash, 
press Ctrl+C in the terminal window where you started the worker.
You can then subsequently repeat the above command to start a new
worker. You should observe in the Web UI that the `validate_coupon`
activity was not duplicated upon restart and that the retry attempts
for the `charge_customer` activity have resumed. If you want to see
an automatic recovery, start another worker in a separate terminal
just before you kill the first one. Within a few seconds, you should
observe that the remaining worker took over for the one that crashed.
In a production system, it is typically to run dozens or hundreds of
workers across multiple machines. This improves both the throughput
and availability of the application.

Once you remove the `charge.fail` file, the next retry attempt will
succeed, and the execution will proceed with the `send_email` activity. 
The `send_email` activity is coded to fail in roughly half of all 
attempts. Unlike the `charge_customer` failure above, this one is 
non-retryable, so the failure propagates back to the workflow instead
of being retried as it otherwise would. The workflow responds by
running the `refund_customer` activity, an example of a compensating
action that undoes an earlier step when a later one fails. When this
happens, the order confirmation reports an amount charged of zero, and
the Web UI will show `refund_customer` in the timeline and event
history. If you submit a few orders, you should see both outcomes.

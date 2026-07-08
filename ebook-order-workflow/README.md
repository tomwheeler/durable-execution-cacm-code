# e-Book Order Example

This project is a Temporal application that processes orders for
electronic books.

## Prerequisites

* The [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package
  manager, with the `uv` command in your executable path.
* [Python 3.10](https://www.python.org/downloads/) or higher.
* The [Temporal CLI](https://docs.temporal.io/cli#install), with the
  `temporal` command in your executable path.

This code has been tested on macOS (Tahoe on an Apple Silicon M2),
Linux (Debian 13.4 on x86\_64), and Windows 11 (x86\_64). It is
expected to work on any system with a similar configuration, as
well as slight variations of it (for example, macOS Sonoma, Windows
10, or Fedora Linux).

## Running the example

### Set up project dependencies
Open a terminal and run the following command to set up the
project dependencies, which includes the Temporal Python SDK:

```command
uv sync
```

### Start the Temporal service

If the Temporal service is not already running locally, open a terminal and start it now:

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

Most of the time, the order completes successfully and the receipt
shows the full amount charged. However, the `send_email` activity is
written to fail occasionally, so about one in five orders will instead
be refunded and report an amount charged of zero. The "Email failure
and compensation" section below explains why.

#### Payment failure
The `charge_customer` activity is written to make it easy to induce
a failure on demand. Do this by creating an empty file named `charge.fail`
in your home directory. On a UNIX system, you can do this by running this command:

```command
touch ~/charge.fail
```

After you have created that file, run the following to submit a new order:


```command
uv run python submit_order.py
```

If you open your browser to <http://localhost:8233/>, you should see
that this execution is still running. If you click it in the table, 
the Temporal Web UI will display its detail page. This shows that the
activity has failed and is being retried. 

If you want to see how the application is able to survive a crash,
press Ctrl+C in the terminal window where you started the worker.
You can then repeat the above command to start a new worker. You
should observe in the Web UI that the `validate_coupon` activity was
not duplicated upon restart and that the retry attempts for the
`charge_customer` activity have resumed.

If you want to see an automatic recovery instead, start a second
worker in a separate terminal just before you kill the first one.
Within a few seconds, you should observe that the remaining worker
took over for the one that crashed. In a production system, it is
typical to run dozens or hundreds of workers across multiple machines,
which improves both application availability and throughput.

If you remove the `charge.fail` file, the next retry attempt will
succeed, and the execution will proceed with the `send_email` activity.

#### Email failure and compensation
The `send_email` activity is coded to randomly fail in roughly one out of 
five attempts. Unlike the `charge_customer` failure above, this one is
non-retryable, so the failure propagates back to the workflow instead
of being retried as it otherwise would. The workflow responds by
running the `refund_customer` activity, an example of a compensating
action that undoes an earlier step when a later one fails. When this
happens, the order confirmation reports an amount charged of zero, and
the Web UI will show `refund_customer` in the timeline and event
history. If you submit a few orders, you should see both outcomes represented.

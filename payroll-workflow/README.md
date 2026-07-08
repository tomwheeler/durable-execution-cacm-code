# Payroll Example

This is an example Temporal application that runs payroll for an employee.
When an employee is hired, the workflow deposits their pay every 14 days
for as long as they remain employed. For demo purposes, the pay period
is 14 seconds instead of 14 days, but you can change `workflow.py` to
use any duration you wish (just remember to restart the worker afterwards
so your change will take effect).

It demonstrates two ways to interact with a running workflow:

* A **signal** changes the state of the workflow. This example has one signal
  to change the employee's pay rate (`set_pay_rate`) and another to end their
  employment (`end_employment`).
* A **query** reads a value from the workflow without changing it. This
  example has one query that returns the current pay rate (`get_pay_rate`)
  and another that returns the total amount paid so far (`get_cumulative_amount`).

## Project files

| File | Purpose |
| --- | --- |
| `workflow.py` | The `PayrollWorkflow` definition, including its signals and queries. |
| `activities.py` | The `deposit` activity, which records a single payment. |
| `worker.py` | Runs the worker that executes the workflow and activities. |
| `start_payroll.py` | Starts payroll for a new employee. |
| `set_pay_rate.py` | Sends a signal to change the pay rate. |
| `query_pay_rate.py` | Queries the current pay rate. |
| `query_cumulative_amount.py` | Queries the total amount paid so far. |
| `end_employment.py` | Sends a signal to end employment and stop payroll. |
| `shared.py` | Settings shared across the scripts, such as the task queue name and workflow ID. |

## Prerequisites

* The [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package
  manager, with the `uv` command in your executable path.
* [Python 3.10](https://www.python.org/downloads/) or higher.
* The [Temporal CLI](https://docs.temporal.io/cli#install), with the
  `temporal` command in your executable path.

## Running the example

### Start the Temporal development server

Open a terminal and start a local Temporal Service if it is not already
running:

```command
temporal server start-dev
```

Leave this running. You can follow the payroll workflow's progress in the
Web UI at <http://localhost:8233/> as you complete the steps that follow.

### Set up project dependencies

In a second terminal, run the following command to install the project
dependencies:

```command
uv sync
```

### Start the worker

In that same terminal, start the worker:

```command
uv run python worker.py
```

The worker processes the workflow and activities. Log messages from each
deposit will appear in the worker's terminal window.

### Hire the employee

In a third terminal, run the following command to start payroll for a new
employee:

```command
uv run python start_payroll.py
```

Since this is a long-running workflow, the command is designed to submit
the request and then exit. If you open the Temporal Web UI in your browser
(<http://localhost:8233/>), you should see a new payroll workflow listed
there. Click it to view the details.

The workflow deposits the first payment right away, so you will see a deposit
in the worker's terminal output immediately. It then waits until the next
pay period before making another deposit. The starting pay rate is $2,000
per period, set in `start_payroll.py`.

The workflow spends almost all of its time waiting. That wait is done with
a durable timer, so the workflow consumes no resources between deposits
and would resume on schedule even if every worker is restarted in the
meantime. The commands below let you interact with it during that wait,
without needing to wait two weeks to see anything happen.

### Query the current pay rate

Run the following to ask the workflow what the employee is currently paid
per pay period:

```command
uv run python query_pay_rate.py
```

This issues a query to the workflow, retrieving the current value of the
variable that holds the pay rate.

### Change the pay rate

Run the following to give the employee a raise:

```command
uv run python set_pay_rate.py
```

This sends a signal that sets the pay rate to $2,750 (you can change this
by modifying the `new_pay_rate` variable in that file). You can confirm the
change by running `query_pay_rate.py` again. The new amount applies to all
future deposits.

### Query the total amount paid

Run the following to ask the workflow how much it has paid the employee so
far, across all pay periods:

```command
uv run python query_cumulative_amount.py
```

This issues a query to the workflow, retrieving the running total that the
workflow updates after each deposit. 

If you'd like to see Durable Execution in action, press Ctrl-C in the
worker's terminal to kill it, then run the command from the **Start the
worker** section to start a new worker. Afterwards, run the previous
command to retrieve the total amount paid to the worker. You should find
that, while the value may now be higher if one or more pay periods has
since elapsed, the previous amount paid remains accounted for. No data
was lost and no extra payments were made. This is the power of Durable
Execution.


### End employment

Run the following to end the employment:

```command
uv run python end_employment.py
```

This sends a signal that stops the payroll. The workflow finishes the next
time it wakes at the start of the next pay period, at which point it sees that
employment has ended and completes instead of making another deposit. You can
watch its status change to Completed in the Web UI.

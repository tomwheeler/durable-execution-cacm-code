# Inherent volatility of normal execution

This example illustrates how a crash negatively affects application state
in an application that does not have the benefit of Durable Execution.

### Prerequisites
* These instructions use the `uv` package manager. Ensure that this is
  [installed](https://docs.astral.sh/uv/getting-started/installation/)
  and that the `uv` command is in your executable path. 
  * Run `uv sync` in this directory to install any necessary Python packages.
* [Python 3.10](https://www.python.org/downloads/) or higher

This code has been tested on macOS (Tahoe on an Apple Silicon M2),
Linux (Debian 13.4 on x86\_64), and Windows 11 (x86\_64). It is
expected to work on any system with a similar configuration, as
well as slight variations (for example, macOS Sonoma, Windows 10, 
or Fedora Linux). 

## Running the example

### Initial setup
This application makes two calls to a banking service, so you
must start this first if you have not already done so.

```
cd ..
cd banking-service
uv run python app.py
```

After this, open your browser to <http://127.0.0.1:9109>. You will see
a web page showing the current balances of two accounts, each of which
should initially have \$1000. As you progress through the instructions
that follow, you will see those balances change in reaction to `withdraw`
and `deposit` calls invoked by the code. You can click the **Reset All**
button in the upper-right corner of the page to restore the original 
balances of both accounts.

### Happy path
Open a new terminal to the directory containing this `README.md`
and then run the following command, which uses the banking service
to transfer \$100 between two accounts:

```command
uv run python transfer.py
```

This is expected to complete successfully, so it represents the
so-called happy path. Upon completion the source account balance
has decreased by \$100 and the destination account balance has
increased by \$100.


### Premature termination
Uncomment line 11 in `transfer.py`. The now-uncommented line will trigger
a crash between the `withdraw` and `deposit` steps. 

Initiate another transfer to make that happen:

```command
uv run python transfer.py
```
The output should indicate that the transfer terminated prematurely.
As a result, the source account balance has decreased by \$100, but
the destination account balance did not increase.

Comment out line 11 by prefixing it with a `#` character. Afterwards,
run the following command:

```command
uv run python transfer.py
```

You should observe that, while both steps completed this time, it
repeated the withdrawal from the previous attempt. As a result of
the crash, the source account balance is \$800 instead of \$900,
so \$100 has disappeared.

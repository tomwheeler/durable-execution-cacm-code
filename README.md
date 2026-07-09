# Code for Durable Execution Paper
Code samples related to Tom Wheeler's Durable Execution paper for 
the _Practice_ section of _Communication of the ACM_.

There are three code samples in the paper, each of which corresponds
to one of the following subdirectories:

* [money-transfer](money-transfer/README.md)
* [ebook-order-workflow](ebook-order-workflow/README.md)
* [payroll-workflow](payroll-workflow/README.md)

Each of these has its own `README.md` file, which describes that
project in more detail. Note that, for the sake of brevity, the
code samples in the paper are shorter than the more complete code
samples in these projects.

## A note about the Temporal service in these examples
Each project requires that the Temporal service is running, and
the instructions for each mentions using this command to start it:

```command
temporal server start-dev
```

This starts a lightweight instance of the Temporal service backed by 
an ephemeral in-memory database (SQLite). If this Temporal service is
restarted, it will not remember any event history or workflow execution
information from the previous session. 

To make the information persist across sessions, which will allow you
to restart the Temporal service without losing any data, use this 
command instead:


```command
temporal server start-dev --db-filename temporal.db
```

The `temporal.db` file will be created if it does not already exist.
Data from the current session will be persisted to this file and will
be used in future sessions that use the same command and reference that
same file. There is nothing special about the `temporal.db` argument;
the value is a file path, and you can choose any name or path that you
like.

While this local file-backed database is convenient for local 
development, it is not appropriate for a production deployment, where
the Temporal service typically spans multiple networked machines to 
form a cluster. For this reason, production deployments typically 
use a database, such as MySQL, PostgreSQL, or Apache Cassandra,
which those machines access via a network connection.

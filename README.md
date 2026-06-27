# Code for Durable Execution Paper
Code samples related to my Durable Execution paper for the Communication of the ACM Practice section

There are three code samples in the article, each of which is
found in a corresponding subdirectory:

* [money-transfer](money-transfer/README.md)
* [ebook-order-workflow](ebook-order-workflow/README.md)
* [payroll-workflow](payroll-workflow/README.md)

The `money-transfer` subdirectory contains the code from the paper
(in the `normal-execution` directory) and a banking service upon which
it depends (in the `banking-service` directory). In the `durable-execution`
directory, there is an implementation of the money transfer that uses
Temporal.

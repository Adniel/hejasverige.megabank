===========================
About Heja Sverige Megabank
===========================


Introduction
============
The Megabank Module provides integration to Megabank and exposes views for members to interact with their Megabank account.


Views
=====

list-transactions
-----------------
Shows an overview with general account details, the latest transactions and new invoices.


transactions-detail
-------------------
Shows details for a specific transaction


reject-invoice
--------------
Form for provide a note when rejecting an invoice

update-invoice
--------------
Updates an invoice an shows the result from the call.


Eventhandlers
=============
When invoices are created or if an invoice state changes, the invoice data should be replicated to Megabank. The invoice
creation is most often initiated by any external application using the Heja Sverige Api module.

Invoice data is transfered when::
* Invoice created
* Invoice retracted


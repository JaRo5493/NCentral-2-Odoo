# N-able N-central to Odoo Helpdesk API Integration

This project is a FastAPI application that serves as an intermediary between **N-able N-central** and an **Odoo helpdesk system**. It enables N-central to directly connect to the FastAPI endpoints to create, update, and resolve tickets in Odoo via an XML-RPC interface. The application also integrates with a PostgreSQL database to retrieve customer details and offers basic authentication for secure access.

The FastAPI app provides a simple and secure API layer that allows N-central to communicate with Odoo, ensuring seamless ticket management and status updates in the helpdesk system.

## Features

- **Create Odoo Helpdesk Tickets**: N-able N-central can directly create tickets in Odoo through the FastAPI application.
- **Update Existing Tickets**: Updates from N-central can append comments to existing Odoo tickets.
- **Resolve Tickets**: N-central can trigger ticket resolution by changing the ticket's status in Odoo.
- **Basic Authentication**: Uses HTTP Basic Authentication to ensure only authorized N-central instances can access the API.
- **PostgreSQL Integration**: Retrieves customer IDs from a PostgreSQL database to map N-central customers to Odoo records.
- **Description Parsing**: Parses detailed ticket descriptions from N-central and extracts relevant customer details for Odoo.


# Odoo Helpdesk API Integration

This project is a FastAPI application that integrates with an Odoo helpdesk system via an XML-RPC interface. It provides endpoints for creating, updating, and resolving tickets in Odoo, as well as parsing descriptions and retrieving customer data from a PostgreSQL database.

## Features

- **Create Odoo Helpdesk Tickets**: Creates new tickets in Odoo based on provided details.
- **Update Existing Tickets**: Appends comments to existing tickets.
- **Resolve Tickets**: Changes the status of a ticket to "Resolved."
- **Basic Authentication**: Uses HTTP Basic Authentication for securing API requests.
- **PostgreSQL Integration**: Retrieves customer IDs from a PostgreSQL database.
- **Description Parsing**: Parses ticket descriptions to extract customer-related details.

## Requirements

To run this application, ensure you have the following installed:

- Python 3.9+
- PostgreSQL
- Odoo (with API access)
- The following Python packages:
  - `fastapi`
  - `uvicorn`
  - `pydantic`
  - `psycopg2`
  - `xmlrpc.client`
  - `logger` (custom logger setup)

You can install the required dependencies using `pip`:

```bash
pip install fastapi uvicorn pydantic psycopg2

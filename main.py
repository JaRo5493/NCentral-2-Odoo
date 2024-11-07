import json
import psycopg2
import xmlrpc.client
import uvicorn
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, Json
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
from logger import setup_logger


logger = setup_logger()


# Import Config File
base_path = Path(__file__).parent
file_path = (base_path / "./config_api.json").resolve()
with open(file_path) as f:
    config = json.load(f)
config_api = config[config["selector"]]

# Odoo API Config
odoo_url = config_api["odoo_url"]
odoo_db = config_api["odoo_db"]
odoo_uid = config_api["odoo_uid"]
odoo_api_key = config_api["odoo_api_key"]

# Get Odoo Models
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(odoo_url))

# FastAPI App Security Setup
security = HTTPBasic()
app = FastAPI(dependencies=[Depends(security)])

# FastAPI Basic Auth User
users = config_api["users"]


# N-Central Ticket Request Base Model
class Item(BaseModel):
    action: str
    title: str
    details: str
    ncentralTicketId: str
    psaTicketNumber: Optional[int] = None
    customTags: Dict[str, str]


def verification(creds: HTTPBasicCredentials = Depends(security)):
    username = creds.username
    password = creds.password
    if username in users and password == users[username]["password"]:
        logger.info(f"User: {username} - Valid Credentials")
        return True
    else:
        logger.error(f"User: {username} - Invalid Credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


def parse_description_to_json(description: str) -> str:
    try:
        # Split the description into lines
        lines = description.split('\n')

        # Initialize an empty dictionary to hold the parsed data
        parsed_data = {}

        # Iterate over each line and extract key-value pairs
        for line in lines:
            if ': ' in line:
                key, value = line.split(': ', 1)
                key = key.strip()
                value = value.strip()
                # Handle special cases for key renaming
                if key == "Description":
                    # Extract the actual customer value
                    if "Customer: " in value:
                        value = value.split("Customer: ", 1)[1]
                    key = "Customer"
                parsed_data[key] = value

        # Convert the dictionary to a JSON object
        json_data = json.dumps(parsed_data, indent=4)
        return json_data
    except Exception as e:
        logger.error(f"Couldn't Process JSON: {e}")
    return description


def get_customer_id(customer_name: str) -> Optional[int]:
    try:
        logger.debug(f"Connecting to the database to get customer ID for: {customer_name}")
        with psycopg2.connect(
            dbname=config_api['database'],
            user=config_api['user'],
            password=config_api['password'],
            host=config_api['host'],
            port=config_api['port'],
            connect_timeout=10
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT odoo_customer_id FROM n_central_customers WHERE customername = %s", (customer_name,))
                result = cursor.fetchone()
                if result:
                    logger.debug(f"Customer ID for {customer_name}: {result[0]}")
                    return result[0]
                else:
                    logger.debug(f"No customer ID found for {customer_name}")
                    return None
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return 0


@app.post("/ticketRequests")
async def create_ticket(item: Item, verification_dep=Depends(verification)):
    if verification_dep:
        try:
            json_result = parse_description_to_json(item.details)
            parsed_dict = json.loads(json_result)
            customer_id = get_customer_id(parsed_dict['Customer'])

            if customer_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer not found or invalid."
                )
        except Exception as e:
            logger.error(f"Couldn't Parse JSON: {e}")
            customer_id = 0

        if item.action == "CREATE":
            logger.debug(f"Item: {item}")
            new_id = models.execute_kw(odoo_db, odoo_uid, odoo_api_key, 'helpdesk.ticket', 'create', [
                {
                    'name': item.title,
                    'partner_id': customer_id,
                    'description': item.details,
                    'area_id': 1,
                    'team_id': 5,
                    'ticket_type_id': 6,
                    'put_off_email': True,
                }
            ])
            created_ticket = {
                "externalTicketId": new_id,
                "ticketUrl": f"{odoo_url}/web#id={new_id}&view_type=form&model=helpdesk.ticket"
            }
            logger.info(f"Creating Ticket: {new_id}")
            return created_ticket

        if item.action == "UPDATE":
            logger.info(f"Updating Ticket: {item.psaTicketNumber}")
            result = models.execute_kw(odoo_db, odoo_uid, odoo_api_key, 'mail.message', 'create', [{
                'model': 'helpdesk.ticket',
                'res_id': item.psaTicketNumber,
                'body': item.details,
                'message_type': 'comment',
            }])
            updated_ticket = {
                "externalTicketId": item.psaTicketNumber,
                "ticketUrl": f"{odoo_url}/web#id={item.psaTicketNumber}&view_type=form&model=helpdesk.ticket"
            }
            if result:
                return updated_ticket
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ticket Update Failed",
                )

        if item.action == "RESOLVE":
            logger.info(f"Resolving Ticket: {item.psaTicketNumber}")
            ticket = models.execute_kw(odoo_db, odoo_uid, odoo_api_key, 'helpdesk.ticket', 'read',
                                       [[item.psaTicketNumber], ['stage_id']])
            if ticket:
                stage_id = ticket[0].get('stage_id')[0]
                # If stage_id is not "Solved" move the Ticket to "Auto Resolved Monitoring"
                if stage_id != 68:
                    fields_to_update = {
                        'stage_id': 69,
                    }
                    result = models.execute_kw(odoo_db, odoo_uid, odoo_api_key, 'helpdesk.ticket', 'write',
                                               [[item.psaTicketNumber], fields_to_update])
                    updated_ticket = {
                        "externalTicketId": item.psaTicketNumber,
                        "ticketUrl": f"{odoo_url}/web#id={item.psaTicketNumber}&view_type=form&model=helpdesk.ticket"
                    }
                    if result:
                        return updated_ticket
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ticket Update Failed",
                        )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)

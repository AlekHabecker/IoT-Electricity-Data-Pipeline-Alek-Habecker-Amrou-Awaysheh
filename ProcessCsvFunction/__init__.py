import os, logging, csv, io
from datetime import datetime
from azure.storage.blob import BlobServiceClient
import azure.functions as func # Azure Functions runtime types
import logging

def main(myblob: func.InputStream):
    logging.info(f"Processing blob: {myblob.name}")
def main(myblob: func.InputStream):
    logging.info(f"Blob trigger function processed file: {myblob.name}, Size:{myblob.length} bytes")
    try:
# Read blob contents into text
        blob_bytes = myblob.read() # read blob as bytes
        blob_text = blob_bytes.decode('utf-8') # decode to text (assuming CSV
#is UTF-8 encoded)
# Parse CSV content
        reader = csv.DictReader(io.StringIO(blob_text))
# Set up Cosmos DB client using environment variables for security
        cosmos_endpoint = os.environ['COSMOS_DB_URI'] # e.g. "https://
#<your-account>.documents.azure.com:443/"
        cosmos_key = os.environ['COSMOS_DB_KEY'] # Primary key for
#your Cosmos account
        database_name = os.environ['COSMOS_DB_DATABASE'] # e.g. "IoTData"
        container_name = os.environ['COSMOS_DB_CONTAINER'] # e.g.
#"SensorReadings"
        cosmos_client = BlobServiceClient(cosmos_endpoint, cosmos_key)
        database = cosmos_client.get_database_client(database_name)
        container = database.get_container_client(container_name)
# Current time for processing (UTC)
        processed_time = datetime.utcnow().isoformat()
# Iterate over each record (row) in the CSV and upsert into Cosmos DB
        for record in reader:
            record['ProcessedTime'] = processed_time # add timestamp field
            container.create_item(body=record) # write record to Cosmos
#DB container
        logging.info(f"Inserted {reader.line_num} records into Cosmos DB container '{container_name}'.")
    except Exception as e:
        logging.error(f"Error processing blob file: {e}")
        raise

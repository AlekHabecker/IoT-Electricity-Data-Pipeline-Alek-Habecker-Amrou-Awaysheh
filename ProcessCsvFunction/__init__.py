import os
import logging
import csv
import io
import uuid  # new import
from datetime import datetime
import azure.functions as func
from azure.cosmos import CosmosClient

def main(myblob: func.InputStream):
    logging.info(f"\U0001F680 Function triggered for blob: {myblob.name}, Size: {myblob.length} bytes")

    try:
        # Read blob contents
        blob_bytes = myblob.read()
        blob_text = blob_bytes.decode('utf-8')

        # Parse CSV content
        reader = csv.DictReader(io.StringIO(blob_text))

        # Cosmos DB connection setup
        cosmos_endpoint = os.environ['COSMOS_DB_URI']
        cosmos_key = os.environ['COSMOS_DB_KEY']
        database_name = os.environ['COSMOS_DB_DATABASE']
        container_name = os.environ['COSMOS_DB_CONTAINER']

        cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
        database = cosmos_client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Timestamp
        processed_time = datetime.utcnow().isoformat()

        inserted = 0
        for record in reader:
            # Add partition key field (TimestampID)
            record['TimestampID'] = record.get('timestamp')
            
            # Add unique id
            record['id'] = str(uuid.uuid4())
            
            # Insert into Cosmos DB
            container.create_item(body=record)
            inserted += 1

        logging.info(f"✅ Successfully inserted {inserted} records into Cosmos DB container '{container_name}'.")

    except Exception as e:
        logging.exception(f"❌ Error processing blob file: {e}")
        raise

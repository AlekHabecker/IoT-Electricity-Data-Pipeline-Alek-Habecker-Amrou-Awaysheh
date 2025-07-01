import azure.functions as func
import logging
import csv
import io
import uuid
from datetime import datetime
from azure.cosmos import CosmosClient
import os
import time

app = func.FunctionApp()

def test_cosmos_auth():
    try:
        cosmos_endpoint = os.environ['COSMOS_DB_URI']
        cosmos_key = os.environ['COSMOS_DB_KEY']
        
        client = CosmosClient(cosmos_endpoint, cosmos_key)
        
        # Try to list databases (minimal permission needed)
        databases = list(client.list_databases())
        logging.info(f"Authentication successful. Found {len(databases)} databases")
        return True
    except Exception as e:
        logging.error(f"Authentication failed: {e}")
        return False

def process_in_batches(container, rows, batch_size=1000):
    """Process rows in batches for better performance"""
    total_rows = len(rows)
    successful_inserts = 0
    failed_inserts = 0
    
    for i in range(0, total_rows, batch_size):
        batch = rows[i:i + batch_size]
        batch_start_time = time.time()
        
        batch_successful = 0
        batch_failed = 0
        
        for record in batch:
            try:
                # Add partition key field (TimestampID)
                record['TimestampID'] = record.get('timestamp', 'default')
                
                # Add unique id
                record['id'] = str(uuid.uuid4())
                
                # Insert into Cosmos DB
                container.create_item(body=record)
                batch_successful += 1
                
            except Exception as e:
                batch_failed += 1
                # Only log first few errors to avoid spam
                if batch_failed <= 3:
                    logging.error(f"Failed to insert record: {e}")
        
        successful_inserts += batch_successful
        failed_inserts += batch_failed
        
        batch_time = time.time() - batch_start_time
        progress = ((i + batch_size) / total_rows) * 100
        
        # Log progress every batch instead of every row
        logging.info(f"Batch {i//batch_size + 1}: {batch_successful} successful, {batch_failed} failed. "
                    f"Progress: {progress:.1f}% ({successful_inserts}/{total_rows}). "
                    f"Batch time: {batch_time:.2f}s")
    
    return successful_inserts, failed_inserts

def process_csv_efficiently(blob_text, container):
    """More efficient CSV processing for large files"""
    
    # Parse CSV content
    reader = csv.DictReader(io.StringIO(blob_text))
    
    # Get column info
    fieldnames = reader.fieldnames
    logging.info(f"CSV columns detected: {fieldnames}")
    
    # Convert to list once (this is the memory-intensive part)
    start_time = time.time()
    rows = list(reader)
    parse_time = time.time() - start_time
    
    logging.info(f"CSV parsing completed: {len(rows)} rows in {parse_time:.2f} seconds")
    
    # Validate data structure
    if not rows:
        logging.warning("No data rows found in CSV")
        return 0, 0
    
    # Check if required fields exist
    sample_row = rows[0]
    if 'timestamp' not in sample_row:
        logging.warning("No 'timestamp' column found. Using default partition key.")
    
    # Process in batches
    logging.info("Starting batch processing...")
    start_time = time.time()
    
    successful, failed = process_in_batches(container, rows, batch_size=1000)
    
    total_time = time.time() - start_time
    
    logging.info(f"Processing completed: {successful} successful, {failed} failed in {total_time:.2f} seconds")
    logging.info(f"Average: {len(rows) / total_time:.1f} rows/second")
    
    return successful, failed

@app.blob_trigger(arg_name="myblob", path="iotdatacontainer/{name}", connection="AzureWebJobsStorage") 
def ProcessCsvFunction(myblob: func.InputStream):
    logging.info(f"🚀 Function triggered for blob: {myblob.name}, Size: {myblob.length} bytes")
    
    # Test CosmosDB connection first
    if not test_cosmos_auth():
        logging.error("CosmosDB authentication failed - stopping processing")
        return
    
    try:
        # Read blob contents
        start_time = time.time()
        blob_bytes = myblob.read()
        blob_text = blob_bytes.decode('utf-8')
        read_time = time.time() - start_time
        
        logging.info(f"Blob read completed in {read_time:.2f} seconds. Content size: {len(blob_text)} characters")
        
        # Setup Cosmos DB connection
        cosmos_endpoint = os.environ['COSMOS_DB_URI']
        cosmos_key = os.environ['COSMOS_DB_KEY']
        database_name = os.environ['COSMOS_DB_DATABASE']
        container_name = os.environ['COSMOS_DB_CONTAINER']
        
        cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
        database = cosmos_client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Process CSV efficiently
        successful, failed = process_csv_efficiently(blob_text, container)
        
        if successful > 0:
            logging.info(f"✅ Successfully processed {successful} records into CosmosDB container '{container_name}'")
        
        if failed > 0:
            logging.warning(f"⚠️ {failed} records failed to process")
        
    except Exception as e:
        logging.exception(f"❌ Error processing blob file: {e}")
        raise
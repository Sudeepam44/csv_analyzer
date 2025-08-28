import csv
import logging
import cantools
import os
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_dbc(dbc_file):
    """Load and parse the DBC file."""
    try:
        if not os.path.exists(dbc_file):
            raise FileNotFoundError(f"DBC file not found: {dbc_file}")
        db = cantools.database.load_file(dbc_file)
        logging.info(f"Loaded DBC file: {dbc_file}, found {len(db.messages)} messages")
        return db
    except Exception as e:
        logging.error(f"Error parsing DBC file: {e}")
        raise

def normalize_data_field(data):
    """Normalize the data field to a hex string without spaces or 0x prefixes."""
    try:
        # Remove '0x' prefixes and spaces, handle various formats
        data = data.strip().replace('"', '')
        # Replace multiple spaces or 0x-separated values
        data = re.sub(r'\s+', '', data)  # Remove all whitespace
        data = re.sub(r'0x', '', data, flags=re.IGNORECASE)  # Remove '0x'
        # Ensure even length for hex
        if len(data) % 2 != 0:
            raise ValueError(f"Invalid hex string length: {data}")
        # Validate hex characters
        if not re.match(r'^[0-9A-Fa-f]+$', data):
            raise ValueError(f"Invalid hex characters: {data}")
        return data
    except Exception as e:
        raise ValueError(f"Failed to normalize data field: {e}")

def decode_can_data(csv_file, db):
    """Read CSV and decode CAN data using the DBC database."""
    decoded_data = []
    row_count = 0
    skipped_rows = 0
    
    try:
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            if not all(col in reader.fieldnames for col in ['timestamp', 'can_id', 'data']):
                raise ValueError("CSV must have columns: timestamp,can_id,data")
            
            for row_num, row in enumerate(reader, start=2):
                row_count += 1
                try:
                    timestamp = row['timestamp'].strip().replace('"', '')
                    can_id_str = row['can_id'].strip().replace('"', '')
                    data = row['data']
                    
                    # Validate inputs
                    if not timestamp or not can_id_str or not data:
                        logging.warning(f"Skipping row {row_num}: Missing timestamp, can_id, or data")
                        skipped_rows += 1
                        continue
                    
                    # Parse CAN ID (handle hex or decimal)
                    try:
                        can_id = int(can_id_str, 16) if can_id_str.startswith('0x') else int(can_id_str)
                    except ValueError:
                        logging.warning(f"Skipping row {row_num}: Invalid CAN ID: {can_id_str}")
                        skipped_rows += 1
                        continue
                    
                    # Normalize and convert data to bytes
                    try:
                        normalized_data = normalize_data_field(data)
                        data_bytes = bytes.fromhex(normalized_data)
                    except ValueError as e:
                        logging.warning(f"Skipping row {row_num}: Invalid data format: {data} ({e})")
                        skipped_rows += 1
                        continue
                    
                    # Find matching message in DBC
                    message = None
                    for msg in db.messages:
                        if msg.frame_id == can_id:
                            message = msg
                            break
                    
                    if not message:
                        logging.debug(f"Row {row_num}: No DBC message found for CAN ID {hex(can_id)}")
                        decoded_data.append({
                            'timestamp': timestamp,
                            'can_id': hex(can_id),
                            'message_name': f"Unknown_{hex(can_id)[2:].upper()}",
                            'signal_name': None,
                            'raw_value': None,
                            'physical_value': None,
                            'state': None,
                            'unit': None
                        })
                        continue
                    
                    # Decode signals
                    try:
                        decoded_signals = message.decode(data_bytes, allow_truncated=True)
                        for signal_name, value in decoded_signals.items():
                            signal = message.get_signal_by_name(signal_name)
                            state = str(value) if signal.choices else None
                            physical_value = float(value) if not signal.choices else None
                            unit = signal.unit or ''
                            
                            decoded_data.append({
                                'timestamp': timestamp,
                                'can_id': hex(can_id),
                                'message_name': message.name,
                                'signal_name': signal_name,
                                'raw_value': value,
                                'physical_value': physical_value,
                                'state': state,
                                'unit': unit
                            })
                    except Exception as e:
                        logging.warning(f"Row {row_num}: Error decoding message {message.name}: {e}")
                        decoded_data.append({
                            'timestamp': timestamp,
                            'can_id': hex(can_id),
                            'message_name': message.name,
                            'signal_name': None,
                            'raw_value': None,
                            'physical_value': None,
                            'state': None,
                            'unit': None
                        })
                    
                except Exception as e:
                    logging.error(f"Error processing row {row_num}: {e}")
                    skipped_rows += 1
                    continue
                
        logging.info(f"Processed {row_count} rows, decoded {len(decoded_data)} signals, skipped {skipped_rows} rows")
        return decoded_data
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        raise

def save_decoded_data(decoded_data, output_file):
    """Save decoded data to a CSV file."""
    headers = ['timestamp', 'can_id', 'message_name', 'signal_name', 'raw_value', 'physical_value', 'state', 'unit']
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in decoded_data:
                writer.writerow({
                    'timestamp': row['timestamp'],
                    'can_id': row['can_id'],
                    'message_name': row['message_name'],
                    'signal_name': row['signal_name'] or 'N/A',
                    'raw_value': row['raw_value'] if row['raw_value'] is not None else 'N/A',
                    'physical_value': f"{row['physical_value']:.3f}" if row['physical_value'] is not None else 'N/A',
                    'state': row['state'] or 'N/A',
                    'unit': row['unit'] or ''
                })
        logging.info(f"Saved decoded data to {output_file}")
    except Exception as e:
        logging.error(f"Error saving output CSV: {e}")
        raise

def main():
    """Main function to run the CAN data analysis."""
    try:
        # File paths
        dbc_file = 'Small_CAR_CANbus.dbc'
        csv_file = 'can_log_2025-08-27T13-59-15.925+05-30.csv'
        output_file = 'decoded_signals.csv'
        
        # Parse DBC
        db = parse_dbc(dbc_file)
        
        # Decode CAN data
        decoded_data = decode_can_data(csv_file, db)
        
        # Save results
        save_decoded_data(decoded_data, output_file)
        
        logging.info("CAN data analysis completed successfully")
    except Exception as e:
        logging.error(f"Analysis failed: {e}")

if __name__ == '__main__':
    main()
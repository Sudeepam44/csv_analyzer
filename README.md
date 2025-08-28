# CAN Data Decoder

This project provides a Python-based tool for decoding raw CAN bus log files into human-readable signals using a DBC database.  
It reads a CSV log file (`timestamp`, `can_id`, `data`), decodes each frame with the help of a DBC file, and saves the decoded signals into a new CSV file.

---

## Features
- Parse and validate a **DBC** file using [cantools](https://github.com/eerimoq/cantools).
- Read raw CAN log files in CSV format.
- Normalize hex data fields to ensure consistent decoding.
- Decode signals into **physical values**, **states**, and **units** (if defined in the DBC).
- Handle missing/invalid data gracefully with logging.
- Save decoded results into a structured CSV file.

---

## Requirements
- Python 3.8 or later
- Install dependencies:

```bash
pip install cantools
````

---

## Project Structure

```
project/
├── Small_CAR_CANbus.dbc              # Example DBC file
├── can_log_2025-08-27T13-59-15.csv   # Example raw CAN log (CSV)
├── decode_can.py                     # Main script
└── decoded_signals.csv               # Output after running
```

---

## Input CSV Format

The input CSV must have these columns:

| timestamp | can\_id | data                     |
| --------- | ------- | ------------------------ |
| 0.001     | 0x123   | 0x11 0x22 0x33 0x44 0x55 |
| 0.002     | 0x456   | 1122334455667788         |

* `timestamp`: message timestamp (string or numeric).
* `can_id`: CAN identifier (hex `0x123` or decimal `291`).
* `data`: CAN payload, as hex bytes (`0x11 0x22 ...` or `112233...`).

---

## Usage

### 1. Place your files

* DBC file (e.g., `Small_CAR_CANbus.dbc`)
* CAN log CSV (e.g., `can_log_2025-08-27T13-59-15.csv`)

### 2. Run the script

```bash
python decode_can.py
```

### 3. Output

A decoded CSV will be created (`decoded_signals.csv`), with columns:

| timestamp | can\_id | message\_name | signal\_name | raw\_value | physical\_value | state | unit |
| --------- | ------- | ------------- | ------------ | ---------- | --------------- | ----- | ---- |

---

## Logging

The script logs important events:

* `INFO`: normal progress messages
* `WARNING`: skipped rows or invalid frames
* `ERROR`: parsing/decoding failures

Logs look like:

```
2025-08-27 14:05:01,123 - INFO - Loaded DBC file: Small_CAR_CANbus.dbc, found 120 messages
2025-08-27 14:05:02,456 - INFO - Processed 500 rows, decoded 450 signals, skipped 50 rows
```

---

## Example Workflow

```bash
# Run decoder
python decode_can.py

# Check results
cat decoded_signals.csv
```

---

## License

MIT License – feel free to use and modify.

```

---

Would you like me to also add a **sample input CSV + output CSV snippet** inside the README so others can see exactly how the decoding looks?
```



# SEPPMail Converter

This python tool allows you to convert [SEPPMail](https://www.seppmail.com/) encrypted email files (`html`) to `.eml` files.

## Usage

```
Usage: main.py [OPTIONS] INPUT_FILE

Options:
  -o, --output PATH
  -u, --username TEXT
  --password TEXT
  --help               Show this message and exit.
```

Relevant environment variables:

| Name | Description |
| ---- | ----------- |
| `SEPPMAIL_USERNAME` | Email supplied during login |
| `SEPPMAIL_PASSWORD` | Password supplied during login|

Unless specified, the script will place the output file next to the input file and name it after the original file.

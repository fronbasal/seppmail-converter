# SEPPMail Converter

This python tool allows you to convert [SEPPMail](https://www.seppmail.com/) encrypted email files (`html`) to `.eml` files.

## Usage

```
Usage: seppmail-converter [OPTIONS] INPUT_FILE

Options:
  -u, --username TEXT
  -p, --password TEXT
  -o, --output PATH
  -f, --force          Skip SEPPMail input file validation
  -d, --delete         Delete input file after conversion
  -o, --overwrite      Overwrite output file if it exists
  -e, --extract        Extract attachments from .eml file
  -q, --quiet          Suppress all output except final path
  -v, --version        Show the version and exit.
  --help               Show this message and exit.
```

Relevant environment variables:

| Name                | Description                    |
|---------------------|--------------------------------|
| `SEPPMAIL_USERNAME` | Email supplied during login    |
| `SEPPMAIL_PASSWORD` | Password supplied during login |

Unless specified, the script will place the output file next to the input file and name it after the original file.

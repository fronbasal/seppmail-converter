import email
import pathlib
import re
from email import policy

import click
import requests
from bs4 import BeautifulSoup

from seppmail_converter.exceptions import AuthenticationError, ExportError
from seppmail_converter import __version__


def get_valid_filename(name):
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        return None
    return s


@click.command()
@click.argument(
    "input_file",
    type=click.Path(
        exists=True, readable=True, resolve_path=True, path_type=pathlib.Path
    ),
)
@click.option("--username", "-u", prompt=True)
@click.password_option("--password", "-p", confirmation_prompt=False)
@click.option(
    "--output",
    "-o",
    type=click.Path(
        file_okay=True,
        writable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    prompt=True,
    prompt_required=False,
)
@click.option(
    "--force",
    "-f",
    help="Skip SEPPMail input file validation",
    type=click.BOOL,
    is_flag=True,
)
@click.option(
    "--delete",
    "-d",
    help="Delete input file after conversion",
    type=click.BOOL,
    is_flag=True,
)
@click.option(
    "--overwrite",
    "-o",
    help="Overwrite output file if it exists",
    type=click.BOOL,
    is_flag=True,
)
@click.option(
    "--extract",
    "-e",
    help="Extract attachments from .eml file",
    type=click.BOOL,
    is_flag=True,
    default=False,
)
@click.option(
    "--quiet",
    "-q",
    help="Suppress all output except final path",
    type=click.BOOL,
    is_flag=True,
)
@click.version_option(__version__, "-v", "--version", message="%(version)s")
def cli(
    input_file: pathlib.Path,
    output: pathlib.Path,
    username: str,
    password: str,
    force: bool,
    delete: bool,
    overwrite: bool,
    extract: bool,
    quiet: bool,
):
    input_file_data = input_file.read_text("utf-8")

    # Extract key-value pairs from form
    if "secmail" not in input_file_data and not force:
        raise click.FileError(
            str(input_file.absolute()), "The input file provided seems to be invalid"
        )

    soup = BeautifulSoup(input_file_data, "lxml")
    value_map = {
        node.attrs.get("name"): node.attrs.get("value")
        for node in soup.find_all("input")
    }

    # Submit the created form to receive session
    target_url = soup.find("form").attrs["action"]
    req = requests.post(target_url, data=value_map)
    if not req.ok:
        raise click.FileError(
            str(input_file.absolute()),
            "Could not submit or find form details, check input file",
        )

    soup = BeautifulSoup(req.text, "lxml")
    value_map = {
        node.attrs.get("name"): node.attrs.get("value")
        for node in soup.find_all("input")
    }
    value_map["email"] = username
    value_map["password"] = password

    # Login with given credentials to export mail as .eml
    req = requests.post(target_url, data=value_map)
    if not req.ok:
        raise AuthenticationError("Failed to log in, check credentials")

    soup = BeautifulSoup(req.text, "lxml")
    if soup.find(id="inputConfirm"):
        raise AuthenticationError(
            "Failed to log in, unknown email create account manually"
        )

    value_map = {
        node.attrs.get("name"): node.attrs.get("value")
        for node in soup.find(id="inputSaveAs").parent.find_all("input")
    }
    del value_map["access"]

    req = requests.post(
        target_url, data={**value_map, "submit": "yes", "access": "raw"}
    )

    if not req.ok:
        raise ExportError("Could not retrieve export from SeppMail")

    if not output:
        filename = str(
            re.findall("filename=(.+)", req.headers["content-disposition"])[0]
        )[1:-1]
        output = pathlib.Path(
            str(
                input_file.parent.joinpath(
                    get_valid_filename(filename) or ".".join((input_file.stem, "eml"))
                )
            )
        )
        if output.exists() and overwrite:
            output.unlink()

    output.write_bytes(req.content)
    output.touch()

    if delete:
        input_file.unlink()
    if quiet:
        click.echo(output.absolute())
    else:
        click.echo(
            f"Decoded {click.format_filename(input_file.absolute())} to {click.format_filename(output.absolute())}"
        )

    if extract:
        msg = email.message_from_bytes(output.read_bytes(), policy=policy.default)
        for attachment in msg.iter_attachments():
            if not attachment.get_content_disposition() == "attachment":
                # Skip over inline attachments
                continue
            try:
                attachment_filename = attachment.get_filename()
            except AttributeError:
                continue
            if not attachment_filename:
                continue
            attachment_output = pathlib.Path(
                pathlib.Path.joinpath(output.parent, attachment_filename)
            )
            attachment_output.write_bytes(attachment.get_payload(decode=True))
            attachment_output.touch()

            if not quiet:
                click.echo(
                    f"Extracted {click.format_filename(attachment_output.absolute())}"
                )


def entry():
    cli(auto_envvar_prefix="SEPPMAIL")


if __name__ == "__main__":
    entry()

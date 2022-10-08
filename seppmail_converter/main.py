import pathlib
import re

import click
import requests
from bs4 import BeautifulSoup

from seppmail_converter.exceptions import AuthenticationError, ExportError


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
@click.option("--username", "-u", prompt=True)
@click.option(
    "--force", "-f", help="Skip SEPPMail input file validation", type=click.BOOL, is_flag=True
)
@click.option(
    "--delete", "-d", help="Delete input file after conversion", type=click.BOOL, is_flag=True
)
@click.password_option("--password", "-p", confirmation_prompt=False)
def cli(
    input_file: pathlib.Path,
    output: pathlib.Path,
    username: str,
    password: str,
    force: bool,
    delete: bool,
):
    # Extract key-value pairs from form
    if "secmail" not in input_file.read_text("utf-8") and not force:
        raise click.FileError(
            str(input_file.absolute()), "The input file provided seems to be invalid"
        )
    soup = BeautifulSoup(input_file.read_text("utf-8"), "lxml")
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
    output.write_bytes(req.content)
    if delete:
        input_file.unlink()
    click.echo(
        f"Decoded {click.format_filename(input_file.absolute())} to {click.format_filename(output.absolute())}"
    )


def entry():
    cli(auto_envvar_prefix="SEPPMAIL")


if __name__ == "__main__":
    entry()

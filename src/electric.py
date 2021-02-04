######################################################################
#                            ELECTRIC CLI                            #
######################################################################

from timeit import default_timer as timer
from cli import SuperChargeCLI
from getpass import getpass
from info import __version__
from subprocess import *
from constants import *
from extension import *
from logger import *
from utils import *
import click
import json
import keyboard


@click.group(cls=SuperChargeCLI)
@click.version_option(__version__)
@click.pass_context
def cli(_):
    pass


@cli.command(aliases=['i'])
@click.argument('package_name', required=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose mode for installation')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode for installation')
@click.option('--no-progress', '-np', is_flag=True, default=False, help='Disable progress bar for installation')
@click.option('--no-color', '-nc', is_flag=True, help='Disable colored output for installation')
@click.option('--log-output', '-l', 'logfile', help='Log output to the specified file')
@click.option('--install-dir', '-dir', 'install_directory', help='Specify an installation directory for a package')
@click.option('--virus-check', '-vc', is_flag=True, help='Check for virus before installation')
@click.option('--no-cache', '-nocache', is_flag=True, help='Prevent usage of cached installations')
@click.option('-y', '--yes', is_flag=True, help='Accept all prompts during installation')
@click.option('--silent', '-s', is_flag=True, help='Completely silent installation without any output to console')
@click.option('--reduce', '-rd', is_flag=True, help='Cleanup all traces of package after installation')
@click.option('--rate-limit', '-rl', type=int, default=-1)
def install(
    package_name: str,
    verbose: bool,
    debug: bool,
    no_progress: bool,
    no_color: bool,
    logfile: bool,
    yes: bool,
    silent : bool,
    install_directory: str,
    virus_check: bool,
    no_cache: bool,
    reduce: bool,
    rate_limit: int,
    ):

    metadata = generate_metadata(no_progress, silent, verbose, debug, no_color, yes, logfile, virus_check, reduce)

    super_cache = check_supercache_valid()

    if no_cache:
        super_cache = False
    

    packages = package_name.strip(' ').split(',')

    if super_cache:
        res, time = handle_cached_request()
        res = json.loads(res)

    else:
        res, time = send_req_all()
        update_supercache(res)
        res = json.loads(res)
        del res['_id']
    
    correct_names = get_correct_package_names(res)
    corrected_package_names = []
    for name in packages:
        if name in correct_names:
            corrected_package_names.append(name)
        else:
            corrections = difflib.get_close_matches(name, correct_names)
            if corrections:
                if silent:
                    click.echo(click.style(
                        'Incorrect / Invalid Package Name Entered. Aborting Installation.', fg='red'))
                    log_info(
                        'Incorrect / Invalid Package Name Entered. Aborting Installation', logfile)
                    sys.exit(1)

                if yes:
                    write(
                        f'Autocorrecting To {corrections[0]}', 'green', metadata)
                    log_info(
                        f'Autocorrecting To {corrections[0]}', logfile)
                    write(
                        f'Successfully Autocorrected To {corrections[0]}', 'green', metadata)
                    log_info(
                        f'Successfully Autocorrected To {corrections[0]}', logfile)
                    corrected_package_names.append(corrections[0])

                else:
                    write(
                        f'Autocorrecting To {corrections[0]}', 'bright_magenta', metadata)
                    write_verbose(
                        f'Autocorrecting To {corrections[0]}', metadata)
                    write_debug(
                        f'Autocorrecting To {corrections[0]}', metadata)
                    log_info(
                        f'Autocorrecting To {corrections[0]}', logfile)
                    if click.prompt('Would You Like To Continue? [y/n]') == 'y':
                        package_name = corrections[0]
                        corrected_package_names.append(package_name)
                    else:
                        sys.exit()
            else:
                write(
                    f'Could Not Find Any Packages Which Match {name}', 'bright_magenta', metadata)
                write_debug(
                    f'Could Not Find Any Packages Which Match {name}', metadata)
                write_verbose(
                    f'Could Not Find Any Packages Which Match {name}', metadata)
                log_info(
                    f'Could Not Find Any Packages Which Match {name}', logfile)
                sys.exit(1)

    write_debug(install_debug_headers, metadata)
    for header in install_debug_headers:
        log_info(header, logfile)

    index = 0

    for package in corrected_package_names:
        pkg = res[package]
        log_info('Generating Packet For Further Installation.', metadata.logfile)
        packet = Packet(package, pkg['package-name'], pkg['darwin'], pkg['darwin-type'], None)
        log_info('Searching for existing installation of package.', metadata.logfile)
        installation = find_existing_installation(package, packet.json_name)
        if installation:
            write_debug(
                f"Found existing installation of {packet.json_name}.", metadata)
            write_verbose(
                f"Found an existing installation of => {packet.json_name}", metadata)
            write(
                f"Found an existing installation {packet.json_name}.", 'bright_yellow', metadata)
            installation_continue = click.prompt(
                f'Would you like to reinstall {packet.json_name} [y/n]')
            if installation_continue == 'y' or installation_continue == 'y' or yes:
                os.system(f'electric uninstall {packet.json_name}')
                os.system(f'electric install {packet.json_name}')
                return
            else:
                sys.exit(1)
        
        write_verbose(
            f"Package to be installed: {packet.json_name}", metadata)
        log_info(f"Package to be installed: {packet.json_name}", metadata.logfile)

        if index == 0:
            if super_cache:
                write(
                    'Rapidquery Successfully SuperCached {} in {:.5f}s'.format(packet.json_name, time), 'bright_yellow', metadata)
                write_debug(
                    f'Rapidquery Successfully SuperCached {packet.json_name} in {round(time, 9)}s', metadata)
                log_info(
                    f'Rapidquery Successfully SuperCached {packet.json_name} in {round(time, 6)}s', metadata.logfile)
            else:
                write(
                    f'Rapidquery Successfully Received {packet.json_name}.json in {round(time, 6)}s', 'bright_yellow', metadata)
                write_debug(
                    f'Rapidquery Successfully Received {packet.json_name}.json in {round(time, 9)}s', metadata)
                log_info(
                    f'Rapidquery Successfully Received {packet.json_name}.json in {round(time, 6)}s', metadata.logfile)

        write('Initializing Rapid Download...', 'green', metadata)
        log_info('Initializing Rapid Download...', metadata.logfile)

        # Downloading The File From Source
        write_debug(f'Downloading {packet.display_name} from => {packet.darwin}', metadata)
        write_verbose(
            f"Downloading from '{packet.darwin}'", metadata)
        log_info(f"Downloading from '{packet.darwin}'", metadata.logfile)
        
        result = download(packet)
        install_package(result)
    
"""
@cli.command()
@click.argument('package_name', required=True)
def uninstall(package_name: str):
    pass
    """

@cli.command(aliases=['remove', 'u'])
@click.argument('package_name', required=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose mode for uninstallation')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode for uninstallation')
@click.option('--no-color', '-nc', is_flag=True, help='Disable colored output for uninstallation')
@click.option('--log-output', '-l', 'logfile', help='Log output to the specified file')
@click.option('-y', '--yes', is_flag=True, help='Accept all prompts during uninstallation')
@click.option('--silent', '-s', is_flag=True, help='Completely silent uninstallation without any output to console')
@click.option('--python', '-py', is_flag=True, help='Specify a Python package to uninstall')
@click.option('--no-cache', '-nocache', is_flag=True, help='Prevent cache usage for uninstallation')
def uninstall(
    package_name: str,
    verbose: bool,
    debug: bool,
    no_color: bool,
    logfile: str,
    yes: bool,
    silent: bool,
    python: bool,
    no_cache: bool
):
    print("WARN: UNINSTALL IS IN BETA AND IS NOT RECCOMENDED, PROCEED WITH CAUTION, OR MOVE THE APP TO YOUR TRASH")
   
    #os.system('sudo rm /Applications/' + difflib.get_close_matches(package_name, os.listdir('/Applications')[0]))
    matches = difflib.get_close_matches(package_name, os.listdir('/Applications'))
    if matches:
        delete_confirm = click.prompt(
                f'Are you sure you want to uninstall {package_name}? [y/n]')
        if delete_confirm == 'y' or delete_confirm == 'y' or yes:
                os.system('sudo rm -Rf "' + matches[0] + '"')
                confirm = True

    #try:
    matches = difflib.get_close_matches(package_name, os.listdir('/Library/Application Support'))
    if matches:
        if confirm == True:
            os.system('sudo rm -Rf "' + matches[0] + '"')


    matches = difflib.get_close_matches(package_name, os.listdir('/Library/Preferences'))
    if matches:
        if confirm == True:
            os.system('sudo rm -Rf "' + matches[0] + '"')
    #except:
       # print("Something went worng, but it should be fine.")


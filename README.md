# dumbo-esse3

Esse3 command line utility, to save my future time!

I often struggle with websites like Esse3, which requires tens of clicks and interactions to accomplish tasks that are often similar and repetitive.
I decided to help myself with a command line interface.
It's here, in case you want to help yourself as well.


## Install

As a preliminary requirement, you need ChromeDriver installed for your machine.
Please, download and install the most appropriate version from the following link:

https://sites.google.com/chromium.org/driver/downloads?authuser=0

You also need the [Poetry](https://python-poetry.org/) Python package manager.
On Debian-like OSes it can be installed with the following command:
```bash
$ sudo apt install python3-poetry
```

After that, you can proceed either via PyPI, or by cloning the repository and install dependencies.
If you opt for PyPI, run the following command:
```bash
$ pip install dumbo_esse3
Defaulting to user installation because normal site-packages is not writeable
Collecting dumbo_esse3
  Downloading dumbo_esse3-0.1.5-py3-none-any.whl (14 kB)
...
Installing collected packages: dumbo_esse3
Successfully installed dumbo_esse3-0.1.5
```

After that, **dumbo-esse3** can be run with
```bash
$ python -m dumbo_esse3
Usage: python -m dumbo_esse3 [OPTIONS] COMMAND [ARGS]...
Try 'python -m dumbo_esse3 --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────────────────────╮
│ Missing command.                                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```

If you instead opt for poetry, run the following commands:
```bash
$ git clone git@github.com:alviano/dumbo-esse3.git
Cloning into 'dumbo-esse3'...
remote: Enumerating objects: 34, done.
remote: Counting objects: 100% (34/34), done.
remote: Compressing objects: 100% (26/26), done.
remote: Total 34 (delta 7), reused 30 (delta 7), pack-reused 0
Receiving objects: 100% (34/34), 23.39 KiB | 469.00 KiB/s, done.
Resolving deltas: 100% (7/7), done.

$ cd dumbo-esse3

$ poetry install
Creating virtualenv dumbo-esse3-52Wpohwy-py3.10 in /home/malvi/.cache/pypoetry/virtualenvs
Installing dependencies from lock file

Package operations: 33 installs, 0 updates, 0 removals

  • Installing attrs (22.1.0)
  • Installing async-generator (1.10)
  ...

Installing the current project: dumbo-esse3 (0.1.1)
```

Poetry may take some time to complete this step.


## Configuration

You may want to add a few environment variables to save more of your time.
If you use Bash, modify and add the following lines to your `.bashrc`:

```bash
export DUMBO_ESSE3_USERNAME='YOUR-USERNAME'
export DUMBO_ESSE3_PASSWORD='YOUR-PASSWORD'
export DUMBO_ESSE3_EXAM_TYPE='SO'
export DUMBO_ESSE3_EXAM_DESCRIPTION='Scritto, discussione ed eventuale orale'
export DUMBO_ESSE3_EXAM_NOTES="Aula indicata sul sito del corso. L'orale è facoltativo. (Room is reported on the website of the course. Oral examination is optional.)"
```

Take into account that you are storing your credentials in a configuration file on your home directory.
If you are not sure that you are the only one who can read this file, DO NOT store your password in it.
You can omit one or more lines above, and they will be asked via a prompt if needed.


## Security Concerns

Take into account that **dumbo-esse3** needs your credentials to simulate your activities in the browser.
Such credentials are only used for the login procedures of Esse3, but you MUST HAVE clear that by using **dumbo-esse3** you are placing a lot of TRUST on me.
If you do not trust me (e.g., you don't know me, or you cannot understand the code shared via this repository, or you don't know anyone trusting this repository), my suggestion is to NOT USE **dumbo-esse3**.

That said, the most secure option to provide your password to **dumbo-esse3** is via the prompt.
However, it's also the most time-consuming.
Alternatively, the password can be provided as a command-line option, but also in this case take into account the fact that very likely it will be stored in some history file, and even worse it will be also visible when listing processes.
I consider this alternative the less secure.
Exporting an environment variable falls in the middle (it's safe as soon as your account is not compromised).


## Usage

The CLI can be run in several ways.
The simplest is likely via `poetry run ./dumbo_esse3_cli.py`.

Have a look at the help by adding the flag `--help`:

```bash
$ poetry run ./dumbo_esse3_cli.py --help

 Usage: dumbo_esse3_cli.py [OPTIONS] COMMAND [ARGS]...

 Esse3 command line utility, to save my future time!

╭─ Options ────────────────────────────────────────────────────────────────────────────────────╮
│ *  --username                  TEXT                           [env var:                      │
│                                                               DUMBO_ESSE3_USERNAME]          │
│                                                               [default: None]                │
│                                                               [required]                     │
│ *  --password                  TEXT                           [env var:                      │
│                                                               DUMBO_ESSE3_PASSWORD]          │
│                                                               [default: None]                │
│                                                               [required]                     │
│    --debug                                                    Don't minimize browser         │
│    --install-completion        [bash|zsh|fish|powershell|pws  Install completion for the     │
│                                h]                             specified shell.               │
│                                                               [default: None]                │
│    --show-completion           [bash|zsh|fish|powershell|pws  Show completion for the        │
│                                h]                             specified shell, to copy it or │
│                                                               customize the installation.    │
│                                                               [default: None]                │
│    --help                                                     Show this message and exit.    │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────╮
│ add-exams  Adds exams provided as command-line arguments.                                    │
│ courses    Prints the list of courses. The number associated with each course is used an ID. │
│ exams      Prints exams and registered students. Filtering options are available.            │
│ theses     Prints the list of theses. The number associated with each student is used as an  │
│            ID. Theses can be shown in the browser and signed automatically.                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```


Run one of the provided commands by adding it to the command-line:

```bash
$ poetry run ./dumbo_esse3_cli.py courses
                                 Courses
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Course                                                            ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ ARCHITETTURA DEGLI ELABORATORI [27007790]                         │
│ 2 │ GESTIONE DELLA SICUREZZA E SVILUPPO DI SOFTWARE SICURO [27008712] │
│ 3 │ KNOWLEDGE REPRESENTATION [27007796]                               │
│ 4 │ SECURE SOFTWARE DESIGN [27006179]                                 │
│ 5 │ INFORMATICA APPLICATA AI BENI CULTURALI [27001252]                │
└───┴───────────────────────────────────────────────────────────────────┘
```


Read the dedicated help of a command of interest by adding the flag `--help` after the command:

```bash
$ poetry run ./dumbo_esse3_cli.py exams --help

 Usage: dumbo_esse3_cli.py exams [OPTIONS]

 Prints exams and registered students. Filtering options are available.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────╮
│ --of                     INTEGER  Index of the course                                        │
│ --all            -a               Show all exams, not only the next                          │
│ --with-students  -s               Also fetch students                                        │
│ --help                            Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```


Add options and arguments to obtain what you want, with no (or minimal) further interaction:

```bash
$ poetry run ./dumbo_esse3_cli.py exams --of 2
──────────────────────────────────────────── Exams ─────────────────────────────────────────────
 2. GESTIONE DELLA SICUREZZA E SVILUPPO DI SOFTWARE SICURO [27008712]
  - 17/09/2022 09:00,   1 students
```


Below is an asciicast taken with asciinema (not 100% accurate):

[![asciicast](https://asciinema.org/a/5ONj9ykRH7u3Gr4ta6zkSdNZf.png)](https://asciinema.org/a/5ONj9ykRH7u3Gr4ta6zkSdNZf)
# Contributing

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

You can contribute in many ways:

# Types of Contributions

## Report Bugs

Report bugs at <https://github.com/OliverDrechsler/front_door_intercom_automation/issues>

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

## Fix Bugs

Look through the GitHub issues for bugs.
Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

## Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

## Write Documentation

It could always use more documentation and faq, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

## Submit code

Pull request docu can be found [here in docs/pull_request_template.md](docs/pull_request_template.md)

## Submit Feedback

The best way to send feedback is to file an issue at <https://github.com/OliverDrechsler/front_door_intercom_automation/discussions>.

If you are proposing a new feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions are welcome :)

## Local Development Workflow

The following example shows a safe local workflow for checking out the repository, creating a development branch, installing dependencies, running tests, committing your work, and restoring the original `master` branch environment afterwards.

1. Clone the repository and enter the project directory.

```bash
git clone <your-repository-url>
cd front_door_intercom_automation_2
```

2. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

3. Check out `master`, update it, and create a local development branch.

```bash
git checkout master
git pull origin master
git checkout -b my-local-dev-branch
```

4. Install the project requirements.

```bash
python -m pip install -r requirements.txt
```

5. Make your changes and run the test suite.

```bash
python -m pytest
```

6. Commit your changes on the development branch.

```bash
git status
git add .
git commit -m "Describe your change"
```

7. Switch back to `master`.

```bash
git checkout master
```

8. Restore the original dependency file from `master` and reinstall the original requirements.

This step is important if you changed `requirements.txt` while working on your branch and want your local `master` environment to match the repository again.

```bash
git restore requirements.txt
python -m pip install --upgrade --force-reinstall -r requirements.txt
```

9. Optional: remove the local development branch after your work has been merged or is no longer needed.

```bash
git branch -d my-local-dev-branch
```
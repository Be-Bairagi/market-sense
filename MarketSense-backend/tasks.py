# tasks.py
from invoke import task


@task
def hello(c):
    print("Invoke is working!")


@task
def install(c):
    c.run("pip install -r requirements.txt")


@task
def freeze(c):
    c.run("pip freeze > requirements.txt")


@task
def lint(c):
    c.run("flake8 . && mypy app/")


@task
def run(c):
    c.run("uvicorn app.main:app --reload")

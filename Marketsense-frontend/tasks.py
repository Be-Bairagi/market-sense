# tasks.py
from invoke import task


@task
def run(c):
    c.run("streamlit run Home.py")


@task
def install(c):
    c.run("pip install -r requirements.txt")


@task
def freeze(c):
    c.run("pip freeze > requirements.txt")

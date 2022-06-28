# Storewise Backend

Welcome to the Storewise backend repo.

### Technologies Used

1. [FastAPI](https://developers.google.com/amp) - State-of-the-art component library for building performant web pages

2. [SQLAlchemy](https://sqlalchemy.org/) - ORM for PostgreSQL

Additionally, we are using `FastAPI_Users` for our User management.

Our server is for the most part asynchronous, hence familiarity with Async / Await is recommended.

---

<h2 id="my-anchor"> Setting up </h2>

Follow the following steps

1. Clone this repo on your local machine. Read the [how to](https://www.atlassian.com/git/tutorials/setting-up-a-repository/git-clone) if you aren't sure.
2. Make sure `poetry` is installed. You can find the installation guide at [Poetry's webpage](https://python-poetry.org/docs/). You can use [`pip` to install poetry](https://python-poetry.org/docs/#installing-with-pip) too.
3. Install `postgresql` CLI (https://www.postgresql.org/download/)
4. ```bash
   poetry run pre-commit install --hook-type pre-commit
   poetry run pre-commit install --hook-type pre-push
   ```
5. Execute the following command in the directory
   ```bash 
   # make sure to `cd <project-directory>` before running the command
   poetry install
   psql -f init.sql
   ```
6. Run migrations 
   ```bash
   poetry run alembic upgrade head
   ```
7. Finally, start the app
   ```bash 
   # in the same project-directory
   poetry run uvicorn app.main:app  --workers 1 --reload   
   ```

8. Upload the data directory to Google Drive using
   ```bash
   gdrive sync upload --keep-remote ....../Data/Storewise 1Q8P1aoNzvMTmBDDQfndHzixGVm4IUAWt
   ```

TODO: Setup ignoreRevs
--- 
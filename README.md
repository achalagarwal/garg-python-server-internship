# Garg Internship Assignment (Python Server)

Hi and welcome to the Garg internship home assignment. 

Before we begin, let's familiarize ourselves with the technologies that we will be using in the test.


### Technologies Used

1. [FastAPI](https://developers.google.com/amp) - State-of-the-art component library for building performant web pages

2. [SQLAlchemy](https://nextjs.org/) - ORM for PostgreSQL

Additionally, we are using `FastAPI_Users` for our User management. On top, it would be nice to have familiarity with `AsyncIO in Python`, `REST APIs`, and `HTML Forms`.



---

<h2 id="my-anchor"> Setting up </h2>

Follow the following steps

1. Clone this repo on your local machine. Read the [how to](https://www.atlassian.com/git/tutorials/setting-up-a-repository/git-clone) if you aren't sure.
2. Make sure `poetry` is installed. You can find the installation guide at [Poetry's webpage](https://python-poetry.org/docs/). You can use [`pip` to install poetry](https://python-poetry.org/docs/#installing-with-pip) too.
3. Install `postgresql` [CLI](https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/).
4. Execute the following command in the directory
   ```bash 
   # make sure to `cd <project-directory>` before running the command
   poetry install
   psql -f init.sql
   cp .env.example .env
   poetry run bash init.sh
   bash init.sh
   ```
5. Finally, start the app
   ```bash 
   # in the same project-directory
   poetry run uvicorn app.main:app  --workers 1 --reload
   ```

--- 

## Assignment

In the assignment, we would like to you carry out two subtasks.

### Subtask 1

Allow the user to login from `https://localhost:8000/login-page` (your port might be different) and get redirected to `https://localhost:8000/home`

### Subtask 2

Allow an authenticated user to upload an image. Keep in mind that the auth token should be generated from the login flow (sent as a query parameter) and used when submitting the image. Check out the code in `app/templates/image_upload.html:44-47`.

---

## Submission

There are multiple ways you may submit your code.

1. Create a `private` Github repository and give us access to the page. This option is preferred
2. Mail a zipped folder of the project to us
3. Please ensure that the app runs without any errors. Warnings are fine :)

---

## FAQ

Q. What are the parameters of scoring for the test? <br/>
A. The parameters are clean code, optimal usage of libraries, and completion of subtasks.

Q. How will the subtasks be checked? <br/>
A. We will clone/download your code and follow the `setting-up` steps to run the server.

Q. Can I make additions outside the subtasks? <br/>
A. Of course, any improvement in the code will be considered in your favour.

Q. What if I only complete one subtask? <br/>
A. We will go through your code and evaluate your submission based on the completed subtask.

Q. What will I learn from these challenges? <br/>
A. You will learn about state-of-the-art technologies like FastAPI; Libraries like SQLAlchemy; and HTML Forms. If you are selected for the internship, you will be working on these technologies during the period of your internship.

Q. I have spent a lot of time on these challenges but have not made much progress? What should I do? <br/>
A. First, don't feel disheartened, our challenges are in no way a perfect measure of your skills. If you are not satisfied with your solution, we would appreciate a write-up on how you attempted to solve the challenge, the steps you undertook, along with whatever code you have to provide.

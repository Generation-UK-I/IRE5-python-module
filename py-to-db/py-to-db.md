# Persisting Data to a Database with Python

## Why Move From CSV to a Database?

CSV files are great for early learning, but they have limitations:

- No concurrency (two users writing at once corrupts data)
- No indexing or fast searching
- No relationships between data
- No data validation
- Hard to scale

A SQL database solves all of these by providing:
- Structured tables
- Querying with SQL
- Data types (text, numeric, foreign keys)
- ACID guarantees
- Persistence across sessions

## Connecting to a Database

>NOTE: This guide assumes you are using VSCode, if you are working from Jupyter you may need to add `psycopg` to your requirements.txt and restart your environment - *or install it using Jupyter magics to run bash commands*

### Setup

Deploy a Postgres database and Adminer management front-end by following the [instructions here](https://github.com/Generation-UK-I/DE-NAT4-TECH-CONTENT/blob/main/databases/Deploy-postgres-adminer.md).

Technically we don't need Adminer, but it's useful for quickly verifying that your code worked, such as seeing your new table appearing.

>Optional: Create a virtual environment with python -m venv ./venv then activate it with .venv\Scripts\activate.ps1

In order to interact with Postgres Python requires an additional library called `psycopg`, install it with `pip install psycopg`

## Connecting Python to PostgreSQL

A connection is like opening a communication channel to the database, and when connected a cursor is used to execute SQL commands.

Open a connection to your DB as follows:

```python
import psycopg2

def get_connection():
    return psycopg2.connect(
        host="[DOCKER_VM_IP]",
        port=5432,
        database="postgres",
        user="postgres",
        password="mysecretpassword"
    )
```

- `psycopg2.connect(...)` the connection *method* provided by the `psycopg` library; returns an object containing all of the connection parameters.

These values match the Docker container settings, the function can be reused as needed, and if connection fails, Python will raise an exception.

Since `get_connection` is a function it will only execute when called, typically by a different function which carries out an action against the DB.

The get_connection() function will return a connection object if successful, but we're not actually doing anything with it currently, so let's add a few lines below it to call the function, and print a success/failure message.

```py
...
connection = get_connection()
if connection:
    print("Connection successful!")
else:
    print("Connection failed")    
connection.close()
```

The `if` statement simply checks if a **connection object** has been returned, and if so prints a success message, `else` prints a failure message.

There are two problems with our code which we'll deal with one by one.

### Connecting with a Context (the right way - using `with`)

The example above will work (assuming your DB is correctly configured), but our first problem is that if the application code fails before the connection is closed, it may hang open unknowingly.

To overcome this problem we use a `Try-Except` block and the `with` keyword; instead of having to manually close the connection with specific lines of code `e.g. connection.close()`, the `with` keyword acts like an automatic door - it opens when you need it, but closes by itself when you're done, or something goes wrong.'

```py
def check_database():
    try:
        # The 'with' statement handles closing the connection automatically
        with get_connection() as conn:
            print("Connection successful!")

    except Exception as e:
        print(f"Connection failed: {e}")

check_database()
```

You can think of `with` like a *guardian*, 'waiting' for the connection object, returned by the `get_connection()` function. If the function fails, the code indented after the `with` never runs.

## `.env` Files

Connecting with a context ensures that the connection is never left open, but the second problem with our code is that you should NEVER hard code credentials into your code - it's too easy to reveal them when sharing, or `git push`ing your code to GitHub. There are a couple of steps to working around this, the first step is by creating an `.env` file.

An `.env` file stores key value pairs outside of your application code, which can include configuration information, and sensitive data, such as usernames, passwords, API keys, connection endpoints, etc.

A common security risk is developers who 'hard-code' values into their app for convenience during development, and then forget to move them to an `.env` file before pushing to GitHub.

>To avoid the above scenario, **NEVER** commit your `.env` file to `git`; Add ".env" to your `.gitignore` file to ensure Git excludes it.

Here is an example .env file containing the credentials to connect to our DB.

```text
POSTGRES_HOST=192.168.1.138
DB_PORT=5432
POSTGRES_USER=postgres
POSTGRES_DB=postgres
POSTGRES_PASSWORD=mysecretpassword
```

Unfortunately, we cannot call these values directly from the `.env` file into our Python code, so the next step is to import a couple of extra libraries to load the values, and enable us to work with them:

- `python-dotenv`: This module contains functions which allow Python to work with environment variables.
- `os`: The os package contains functions which allow Python to interact with the host operating system.

>The `python-dotenv` module is not included in the **Python Standard Library**, you can install it with `pip install python-dotenv` or by adding it to your `requirements.txt`; The `os` module is included as standard.

### Operating System Environments

When you log into an operating system an environment is created for you, as you interact with your system you do so from within your environment; It might make sense if you consider multiple user accounts - Each user might have their own desktop icons and options, they might want different language, accessibility, and contrast settings, they have different apps and OS config, and so on. Environment variables contain values related to your specific environment and configuration, a different user on the same system will have different values for the variables.

>Another environment variable that you may have encountered is `PATH` which contains the locations on the system which applications may be executed from. If you didn't tick this box when installing Python you may encounter issues when running your code from different locations.

The below code:

1. Imports the required libraries
1. Loads `.env` variables into the operating system's environment
1. Calls our `check_database` function, which in turn calls `get_connection`
1. Accesses the connection details from within the code

Try to identify each stage before reading the points below:

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

def check_database():
    try:
        with get_connection() as conn:
            print("Connection successful!")

    except Exception as e:
        print(f"Connection failed: {e}")

check_database()
```

- `os`, `psycopg2`, and the `load_dotenv` functions from the `dotenv` library, are all imported.
- `load_dotenv()`: This function loads the contents of the `.env` file into the operating system's environment.
- `os.getenv`: This method, from the os library, allows Python to retrieve the OS environment variables directly, which now includes our DB connection details.

## Planning Database Tables

Based on the values and data types in your app you will need to design `CREATE TABLE` statements suitable for the keys and values. But before you do so, you may find it useful to draw out the tables, identify `PRIMARY` keys, `FOREIGN` key relationships, and data types.

>When planning your tables, dictionary `keys` will map to `field` names in a table, and `values` will be individual `record` entries.

### Creating SQL DB Tables Using a Cursor Object

We can create a connection object using our `get_connection` function which returns a **connection object**. To create tables we need to call this object and execute our `CREATE TABLE` commands, just as though we were typing them ourselves through the DBs CLI.

This is done by opening a **cursor object** against this **connection object** to our DB, and have Python enter the relevant commands for us.

Below we have a `create_tables()` function, with one `CREATE TABLE` statement as an example:

```py
...
   
def create_tables():
    conn = get_connection() # Call the get_connection() function
    cur = conn.cursor() # Call the cursor method against the 'conn' object

    # Create a table using the cursor's execute method
    cur.execute("""
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        );
    """)
    
    conn.commit() # Commit changes to DB
    cur.close() # Close cursor
    conn.close() # Close connection
    print("Table created successfully!")
    
create_tables() # Call function
```

- Calls `get_connection`
- The returned object is stored in the `conn` variable
- The **connection object** has a `cursor()` method which creates a **cursor object**
- The **cursor object** has it's own methods it can call...

The cursor methods we've used so far are:

- `.execute()`: Execute SQL Commands - Used to run SQL queries
- `.commit()` Commit Changes: To permanently save the changes following commands that modify data (INSERT/UPDATE/DELETE).
- `.close()`: Close the cursor and connection to free database resources
  - **NOTE**: The `cur` and `conn` objects are both closed.

>Always close your cursor & connection

The `cur.execute()` lines call the execute method, and passes our `CREATE TABLE...` statements as strings to the database CLI. This same methodology can be applied to INSERT, UPDATE, and SELECT statements, but SELECT has a couple of extra steps because it's returning records that we have to deal with.

## Selecting Records with Python

We can add and modify data in our database, how about retrieving it?

In order to retrieve some records, we'll need to provide some input to choose what to retrieve with a SELECT statement.

Below we have a function to retrieve a contact from the contact table, some of the code is hopefully familiar by now, but there are some new concepts to explore (*TIP: Due to long comments, it'll be easier to read if you maximise the width - not best practice, I know!*).

```py
def get_contact_by_name():
    name_to_search = input("Enter the name of the contact: ") # User inputs name
    try: # Notice double 'with' statements after 'try'
        with get_connection() as conn: # Ensure connection closes
            with conn.cursor() as cur: # Ensure cursor closes
                # Use a placeholder (%s) for safety
                sql = "SELECT id, name, phone FROM contacts WHERE name = %s;"
                
                # Pass the variable as the second argument (must be a tuple)
                cur.execute(sql, (name_to_search,))
                
                # Fetch one record
                contact = cur.fetchone()

                if contact:
                    print(f"Found: ID {contact[0]} | Name: {contact[1]} | Phone: {contact[2]}")
                else:
                    print(f"No contact found with the name '{name_to_search}'.")

    except Exception as e:
        print(f"An error occurred: {e}")
```

### SQL Injection

>One of the biggest security risks in software is `SQL Injection`, where a malicious user types their own SQL statements into an input field, **tricking** the database to retrieve sensitive records, modify, or delete your database.

In the previous example:

1. We capture user input and store it in a variable called `name_to_search`
1. open connection and cursor objects
1. Write our SELECT statement and store it in a variable called `sql`, but instead of concatenating it with the `name_to_search` string, we use a placeholder `%s`:

```sql
sql = "SELECT id, name, phone FROM contacts WHERE name = %s;"
```

#### Mitigating SQL Injection with the `%s` Placeholder

The `%s` placeholder protects us from SQL Injection, without it anything the user provides as input will be added directly into the `SELECT` statement. The syntax is of course trickier than this (but not much), but without the `%s` an attacker could effectively be creating a statement like:

```sql
sql = "SELECT id, name, phone FROM contacts WHERE name = ALL;"
-- or the user could input: "; DROP TABLE contacts;" then the SELECT statement becomes
sql = "SELECT id, name, phone FROM contacts WHERE name = * ; DROP TABLE contacts;"
-- and your contacts table disappears
```

Our `name_to_search` variable comes in on the next line: `cur.execute(sql, (name_to_search,))`, which is actually doing quite a lot...

We've used the `.execute()` method already, but rather than providing a **CREATE** or **INSERT** statement as a long string, we're passing our `sql` variable (*containing our SELECT statement*), and the `name_to_search` variable separately. This is how we safely execute SELECT statements, while protecting against SQL Injection attacks.

---

To illustrate how this works consider the following simple code:

```py
my_var = "world"

print("hello " + my_var)
```

The output of this will of course be `hello world`, but that phrase never exists as a complete string, only the string "hello " from our `print` statement, and the variable "world" from `my_var` - so `hello world` is like our SQL statement, and the whole thing never exists completely in one place, only across two (or more) variables.

>We should use %s for any SQL statements that capture user input, including CREATE, INSERT, UPDATE if for example we were prompting the user with something like: "*Enter the name of the table to be created*".
---

One more thing to point out in the `cur.execute(sql, (name_to_search,))` line of code, we pass two values with our `.execute()` method, `sql` and `(name_to_search,)` as discussed, but notice the syntax here, specifically the 'trailing comma'.

When passing multiple values with the `.execute()` method, `psycopg` expects a tuple; In Python syntax `(this)` is a string in parenthesis, but `(this,)` is a tuple with one value.

### Retrieving Records

Below is the second half of our `get_contact_by_name()` function (to save you scrolling up and down).

```py
...
                # Fetch one record
                contact = cur.fetchone()

                if contact:
                    print(f"Found: ID {contact[0]} | Name: {contact[1]} | Phone: {contact[2]}")
                else:
                    print(f"No contact found with the name '{name_to_search}'.")

    except Exception as e:
        print(f"An error occurred: {e}")
```

- `.fetchone()`: Returns a single tuple (one row). Perfect for searching by a unique name or ID. In our case the returned record is stored in the `contact` variable.
- `.fetchall()` (**NOT USED ABOVE**): Returns a list of tuples. Use this if you expect multiple results (e.g., searching for every product containing "Coffee").

In our case we've only fetched one record, because we're only expecting one contact to be returned. The returned record is stored in a tuple, with the record's fields making up the items in the tuple.

Since a tuple behaves just like a list (except tuples are immutable), once retrieved, our `if` statement simply uses the index values of the tuple to insert the relevant values into the print statement.

If you add the `get_contact_by_name` function below the previous `check_database` function, then call `get_contact_by_name()` at the end of your script, you should see the following output (if using the sample data):

```sh
Connection successful!
Enter the name of the contact: Bob Smith
Found: ID 2 | Name: Bob Smith | Phone: 07234567890
```

---

If all of the previous steps were successful you should have a sample app demonstrating the key functionality of persisting data from a Python app to a SQL database.

This is the key functionality required for sprint 5.

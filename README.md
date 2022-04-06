I added the `/editSensorData` function and completely reorganized the **framework layout**.

After our last meeting, I examined the framework and thought about the steps that
would be needed to add new tables to the database.  How trivial would it be to
copy the existing functions, rename parameters, and integrate requests with minimal
effort and errors.

With the current framework design, simply copying existing functions and adjusting
parameters turned out to be more challenging than I had previously imagined and
proved to be quite confusing to keep track of the arguments being passed around.

The two existing tables, "users" and "oximeter", referenced many independant
functions and operations with only a few that wereoverlapping.
Clearly, both tables were using more functions than needed.

So, I decided to condense the framework by replacing the "indepent-to-table"
functions with efficient and adaptable core functions that would integrate
with all existing tables and adapt to future tables.

To organize and simplify the framework, I defined a set of **Design Rules** for all **`tables`**,  **`column_names`**, and `core functions`.
Adhering to these *design contraints* will allow for quick integrations of additional `tables` with minimal code updates.

# Web Framework
[https://m2band.hopto.org](https://m2band.hopto.org)

Framework is loosely modeled after CRUD: [C]reate [R]ead [U]pdate [D]elete

**Features:**
 * *Admin Functions* - **`/createTable`** and **`/deleteTable`**
 * *User Functions* - **`/login`** and **`/logout`**
 * *Core Functions* - [**`/add`**](#1-add), [**`/get`**](#2-get), [**`/edit`**](#3-edit), [**`/delete`**](4-delete)
 * Query and URL path paramater support
 * Additional **filter** parameter - enables SQLite expressions containing operators 
 * In-place column editing with SQLite3 expression support
 * [**`/get`**](#2-get), [**`/edit`**](#3-edit), [**`/delete`**](4-delete) support single and multiple simultaneous table transactions
 * Changes made to the **m2band.db** database are now automatically updated to the github repo in *real-time*

**Design Constrains:**
* All  **`table_names`** and **`column_names`** are defined with **lowercase** letters
* A column name with suffix **`_id`** reference a **unique item** or a **unique item group**.
* A column name with suffix **`_time`** reference a **unique datetime item**
* All tables must have a **`user_id_`** column and a second **`{ref}_id`** `column`
  * The **`users`** table is the only exception and only has one **`{ref}_id`** column: **`user_id`**
* All tables must have one **`{ref}_time`** `column`

**4 Core Functions:**
These functions represent the main endpoints of the framework and will handle the majority of all requests. 
1. [**`/add`**](#1-add) - Add a *single* entry to a `table`
2. [**`/get`**](#2-get) - Fetch a *single* entry or *multiple* entries from a `table`
3. [**`/edit`**](#3-edit) - Edit a *single* entry or *multiple* entries in a `table`
4. [**`/delete`**](4-delete) - Delete a *single* entry or *multiple* entries from a `table`

#### Debugging Tip
To see all of the available `tables` along with the `column_names` and the `column_types`, make a request to the root path of any core function

Request:
```ruby
https://m2band.hopto.org/add
https://m2band.hopto.org/get
https://m2band.hopto.org/edit
https://m2band.hopto.org/delete
```

Response:
```json
{ "message": "active tables in the database",
  "tables": [
    { "name": "users",
      "type": "table",
      "columns": [
        { "name": "user_id", "type": "INTEGER PRIMARY KEY" },
        { "name": "username", "type": "TEXT NOT NULL" },
        { "name": "password", "type": "TEXT NOT NULL" },
        { "name": "create_time", "type": "DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))" }
      ]
    },
    { "name": "oximeter", 
      "type": "table",
      "columns": [
        { "name": "entry_id", "type": "INTEGER PRIMARY KEY" },
        { "name": "user_id", "type": "INTEGER NOT NULL" },
        { "name": "heart_rate", "type": "INTEGER NOT NULL" },
        { "name": "blood_o2", "type": "INTEGER NOT NULL" },
        { "name": "temperature", "type": "DOUBLE NOT NULL" },
        { "name": "entry_time", "type": "DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))" }
      ]
    }
  ]
}
```

# Usage
The examples listed below will cover the **4 core functions** and the **2 admin functions**.
All examples shown are executed via a **GET** request and can be tested with any browser.
All endpoints support 4  *HTTP_METHODS*: **GET**, **POST**, **PUT**, **DELETE**

# 1. `/add`
**Add a *single* entry to a `table`**

**Endpoints:**

| resource | description  |
|:--|:--|
| **`/add`**  | returns a list of all existing tables in the database |
| **`/add/usage`**  | returns a message for how to use this function |
| **`/add/{table_name}`**  | returns the required parameters need to add an entry to a table |
| **`/add/{table_name}/{param_name}/{param_value}`**  | add a single entry to the table  using path parameters |
| **`/add/{table_name}?param_name=param_value`**  | add a single entry to the table using query parameters |

**Requirements:**

| parameters | comment  |
|:--|:--|
| `user_id` and all parameters not **`*_id`** or **`*_time`** | Exception: `user_id` is required for **`users`** table |

> Note: <br />
> 
> The old functions `/addUser` and `/addSensorData` still work but are kept for backward compatibility. <br />
> `/addUser` has migrated to: `/add/users` <br />
> `/addSensorData` has migrated to: `/add/oximeter` <br />
> It is recommened to update the existing *mp32* and *swift* code to follow the new format

## Workflow Example:
* Let's add 2 users to the **`users`** table: `alice` and `bob`
* Then, add sensor data to the **`oximeter`** table for both users

#### Adding `alice` to the **`users`** table
The endpoint for adding a user to the **`users`** is **`/add/users`**.
Making a request to the endpoint without providing **parameters** returns a `missing parameters` message:

Request:
```ruby
/add/users
```

Response:
```json
{
  "message": "missing paramaters", 
  "required": [{"username": "TEXT", "password": "TEXT"}], 
  "missing": [{"username": "TEXT", "password": "TEXT"}], 
  "submitted": [{}]
}
```

Making a request with only 1 of the 2 **required_parameters** updates the `missing parameters` message:

Request:
```ruby
/add/users/username/alice
```

Response:
```json
{
  "message": "missing paramaters",
  "required": [{"username": "TEXT", "password": "TEXT"}],
  "missing": [{"password": "TEXT"}],
  "submitted": [{"username": "alice"}]
}
```

To add the user `alice`, we need to provide the **username** and **password** parameters
There are several ways to do this: using **url_parameters**, **query_parameters**, or a combination of both.

**Recommended Method: Using url_arameters**
```ruby
/add/users/username/alice/password/alice
```
Response:
```json
{
  "message": "data added to {users}",
  "user_id": 7
}
```

*Alternative Methods: Any of these will work but the format may get confusing when using the other **core functions***
```ruby
/add/users?username=alice&password=alice
/add/users/username/alice?password=alice
/add/users/password=alice?username=alice
```

Attempting to add the existing user `alice` will respond with a `user exists` message:

Request
```ruby
/add/users/username/alice/password/alice
```
Response:
```json
{
  "message": "user exists",
  "username": "alice"
}
```

#### Adding `bob` to the **`users`** table
Request:
```ruby
/add/users/username/bob/password/bob
```
Response:
```json
{
  "message": "data added to {users}",
  "user_id": 8
}
```

#### Adding sensor data for the user `alice` to the **`oximeter`** table
When we added the user `alice` to the **`users`** table, we were provided with the **`user_id = 7`** 
To get the required parameters for adding an `entry` to the **`oximeter`**, make a request without parameters:

Request:
```ruby
/add/oximeter
```

Response:
```json
{
    "message": "missing paramaters",
    "required": [{"user_id": "INTEGER", "heart_rate": "INTEGER", "blood_o2": "INTEGER", "temperature": "DOUBLE"}],
    "missing": [{"user_id": "INTEGER", "heart_rate": "INTEGER", "blood_o2": "INTEGER", "temperature": "DOUBLE"}],
    "submitted": [{}]
}
```

Let's add some sensor data for the user `alice` to the **`oximeter`** table by making the following requests:

Request:
```ruby
/add/oximeter/user_id/7/heart_rate/134/blood_o2/97/temperature/97.6691638391727
/add/oximeter/user_id/7/heart_rate/129/blood_o2/98/temperature/97.45331222228752
/add/oximeter/user_id/7/heart_rate/128/blood_o2/100/temperature/97.35755335543793
/add/oximeter/user_id/7/heart_rate/134/blood_o2/96/temperature/97.03691402965539
/add/oximeter/user_id/7/heart_rate/132/blood_o2/96/temperature/97.78609598543946
/add/oximeter/user_id/7/heart_rate/130/blood_o2/98/temperature/97.262831668111
```

Each request had a unique response:
Response:
```json
{"message": "data added to {oximeter}", "entry_id": 43, "user_id": "7"}
{"message": "data added to {oximeter}", "entry_id": 44, "user_id": "7"}
{"message": "data added to {oximeter}", "entry_id": 45, "user_id": "7"}
{"message": "data added to {oximeter}", "entry_id": 46, "user_id": "7"}
{"message": "data added to {oximeter}", "entry_id": 47, "user_id": "7"}
{"message": "data added to {oximeter}", "entry_id": 48, "user_id": "7"}
```

Now let's add some sensor data for the user `bob` to the **`oximeter`** table by making the following requests:

Request:
```ruby
/add/oximeter/user_id/8/heart_rate/143/blood_o2/97/temperature/97.23579109761334
/add/oximeter/user_id/8/heart_rate/127/blood_o2/97/temperature/97.7532770488335
/add/oximeter/user_id/8/heart_rate/131/blood_o2/95/temperature/97.89202180155488
/add/oximeter/user_id/8/heart_rate/124/blood_o2/95/temperature/97.81020200542864
/add/oximeter/user_id/8/heart_rate/133/blood_o2/95/temperature/101.7115308733577
/add/oximeter/user_id/8/heart_rate/133/blood_o2/100/temperature/103.10357503270177
/add/oximeter/user_id/8/heart_rate/144/blood_o2/98/temperature/103.35133621760384
/add/oximeter/user_id/8/heart_rate/134/blood_o2/98/temperature/102.16442367992002
/add/oximeter/user_id/8/heart_rate/132/blood_o2/98/temperature/101.79215076652413
/add/oximeter/user_id/8/heart_rate/130/blood_o2/99/temperature/102.76488036781804
```

Response:
```json
{"message": "data added to {oximeter}", "entry_id": 49, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 50, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 51, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 52, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 53, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 54, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 55, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 56, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 57, "user_id": "8"}
{"message": "data added to {oximeter}", "entry_id": 58, "user_id": "8"}
```

Now that we have added users and sensor data, let's take a look at the next **core function**: [**`/get`**](#2-get)

# 2. `/get`
**Fetch a *single* entry or *multiple* entries from a `table`**

**Endpoints:**

| resource | description  |
|:--|:--|
| **`/get`** | returns a list of all existing tables in the database |
| **`/get/usage`** | returns a message for how to use this function |
| **`/get/{table_name}`** | returns all entries for the table: `{table_name}` |
| **`/get/{table_name}/{param_name}/{param_value}`** | return all entries for table: `{table_name}` matching `/name/value` pairs (name=value) |
| **`/get/{table_name}?param_name=param_value`**  | return all entries for table: `{table_name}` matching `name=value` pairs |
| **`/get/{table_name}/filter/{filter_string}`**  | return entries matching `/name/value` pairs and `filter` by: `{filter_string}` |
| **`/get/{table_name}?filter=filter_string`**  | return entries matching `name=value` pairs and `filter` by: `{filter_string}` |

**The Filter Parameter:**
- `name=value` pairs are limited to `column` paramaters with an *exact match*! (ex: username=alice, user_id=8, etc.)
- the **`{filter_string}`** supports **expressions** containing **comparrison and logical operators** as well ass **functions**
- We will examine how to use the **`filter`** parameter in the examples ahead

> Note: <br />
> 
> The old functions `/getUser`, `/getUsers`, `/getSensorData`, and `/getAllSensorData` still work but are kept for backward compatibility. <br />
> `/getUser` has migrated to: `/get/users` <br />
> `/getUsers` has migrated to: `/get/users` <br />
> `/getSensorData` has migrated to: `/get/oximeter` <br />
> `/getAllSensorData` has migrated to: `/get/oximeter` <br />
> It is recommened to update the existing *mp32* and *swift* code to follow the new format

## Workflow Example:
* Let's query the **`users`** table to find the 2 users we created earlier
* Next, we will query the **`oximeter`** table to retrieve the sensor data for each user
* Finally, we will examine the **`filter`** parameter and test out a few **test cases**
  * Test Case: Determine which user possibly has a **fever**
  * Test Case: What was the range of **`temperature`** for this user? **min**? **max**?
  * Test Case: Filter users created after a *start date* but before an *end date*.


Examine the **`users`** table
Request:
```ruby
/get/users
```

Response:
```json
{
    "message": "found 8 user entries",
    "data": [
        {"user_id": 1, "username": "user_1", "password": "794001bff7f6ae7ded745c7de77043873b4173fad011d3ee5ba42bea334d99486f38d77f246009a052277d7b56dddd90337d5f18cf7fa065ed287e6b8661a279", "create_time": "2022-04-01 23:09:19.000"},
        {"user_id": 2, "username": "user_2", "password": "828beaa5b092bc374d1a443847ea68f1d83e4991b83c2e95e961ce4817138b7c53c7eb8be731d5bb0c3bfbe7d0335fe3f5ccc1b674d93c89c27d6b644da56875", "create_time": "2022-04-01 23:16:26.000"},
        {"user_id": 3, "username": "user_3", "password": "a3bfdbe9284aecf165cf3fad3ff9c66c3ffa08fe930a2de52094a039062573b00642870e7a304500b1c62a9d0b50d0ffab4a4e08ffc028c86b2f46acae92be74", "create_time": "2022-04-01 23:16:36.000"},
        {"user_id": 4, "username": "user_4", "password": "e820f57e418d387107bfb9e57119e9aa7c3e1db9ef06b1b107c0eb8444b57b69cee1fac48feeb33c7dc34904e0a38e84dd9b6b44fd51078c8359fc272d5af13d", "create_time": "2022-04-01 23:16:41.000"},
        {"user_id": 5, "username": "user_5", "password": "a3cc8fd887edb257f9e630383eb5569d35d2f2600333cd3ff828e5f35edbedbba64bfac5a7da46013a6877934f57d1e3807116205c556aeef83521d6561408fb", "create_time": "2022-04-01 23:16:48.000"},
        {"user_id": 6, "username": "M2band", "password": "30823caee74ca49fd5699c8de172b515f7a00ab04a04d0641107677af5f372c169746ccdf08b3ba1542c0626d73cb5ebcfec762016cab411e06596e4d2211b34", "create_time": "2022-04-03 15:29:41.223"},
        {"user_id": 7, "username": "alice", "password": "df564e993decffa1a96454f7fa0dc48f0bf66c981f141aaf9b140f18c7f3aed90727ec05e4fcef23af66830dd6883b6b899414eff98aa2669443bc8d42470c9a", "create_time": "2022-04-05 03:25:57.163"},
        {"user_id": 8, "username": "bob", "password": "8ca79597eb2bc1eebd93a1d595e921fcc64a2c00f175cc5dfa59a728122bc846f1bba08457795d539145508d99747a43049cee0c0f696c7d1b088131b45fa0d4", "create_time": "2022-04-05 03:41:12.857"}
    ]
}
```

We just want our 2 users **`alice`** and **`bob`**, let's try querying with different parameters

Request:
```ruby
/get/users/username/alice
```

Response:
```json
{
  "message": "1 user entry found",
  "data": {"user_id": 7, "username": "alice", "password": "df564e993decffa1a96454f7fa0dc48f0bf66c981f141aaf9b140f18c7f3aed90727ec05e4fcef23af66830dd6883b6b899414eff98aa2669443bc8d42470c9a", "create_time": "2022-04-05 03:25:57.163"}
}
```

Request:
```ruby
/get/users/username/bob
```

Response:
```json
{
    "message": "1 user entry found",
    "data": {"user_id": 8, "username": "bob", "password": "8ca79597eb2bc1eebd93a1d595e921fcc64a2c00f175cc5dfa59a728122bc846f1bba08457795d539145508d99747a43049cee0c0f696c7d1b088131b45fa0d4", "create_time": "2022-04-05 03:41:12.857"}
}
```

Request:
```ruby
/get/users/user_id/7
```

Response:
```json
{
    "message": "1 user entry found",
    "data": {"user_id": 7, "username": "alice", "password": "df564e993decffa1a96454f7fa0dc48f0bf66c981f141aaf9b140f18c7f3aed90727ec05e4fcef23af66830dd6883b6b899414eff98aa2669443bc8d42470c9a", "create_time": "2022-04-05 03:25:57.163"}
}
```


Request:
```ruby
/get/users/user_id/8
```

Response:
```json
{
    "message": "1 user entry found",
    "data": {"user_id": 8, "username": "bob", "password": "8ca79597eb2bc1eebd93a1d595e921fcc64a2c00f175cc5dfa59a728122bc846f1bba08457795d539145508d99747a43049cee0c0f696c7d1b088131b45fa0d4", "create_time": "2022-04-05 03:41:12.857"}
}
```

#### Let's try out the **`filter`** parameter to get just the users: **`alice`** and **`bob`**

Request:
```ruby
/get/users?filter=(user_id = 7 OR user_id = 8)
```

Response:
```json
{
    "message": "found 2 user entries",
    "data": [
        {"user_id": 7, "username": "alice", "password": "df564e993decffa1a96454f7fa0dc48f0bf66c981f141aaf9b140f18c7f3aed90727ec05e4fcef23af66830dd6883b6b899414eff98aa2669443bc8d42470c9a", "create_time": "2022-04-05 03:25:57.163"},
        {"user_id": 8, "username": "bob", "password": "8ca79597eb2bc1eebd93a1d595e921fcc64a2c00f175cc5dfa59a728122bc846f1bba08457795d539145508d99747a43049cee0c0f696c7d1b088131b45fa0d4", "create_time": "2022-04-05 03:41:12.857"}
    ]
}
```


Request:
```ruby
/get/users?filter=(user_id = "7" OR user_id = "8")
```

Response:
```json
{
    "message": "found 2 user entries",
    "data": [
        {"user_id": 7, "username": "alice", "password": "df564e993decffa1a96454f7fa0dc48f0bf66c981f141aaf9b140f18c7f3aed90727ec05e4fcef23af66830dd6883b6b899414eff98aa2669443bc8d42470c9a", "create_time": "2022-04-05 03:25:57.163"},
        {"user_id": 8, "username": "bob", "password": "8ca79597eb2bc1eebd93a1d595e921fcc64a2c00f175cc5dfa59a728122bc846f1bba08457795d539145508d99747a43049cee0c0f696c7d1b088131b45fa0d4", "create_time": "2022-04-05 03:41:12.857"}
    ]
}
```


Request:
```ruby
/get/users?filter=(user_id > 6 AND user_id < 9)
```

Response:
```json
{
    "message": "found 2 user entries",
    "data": [
        {"user_id": 7, "username": "alice", "password": "df564e993decffa1a96454f7fa0dc48f0bf66c981f141aaf9b140f18c7f3aed90727ec05e4fcef23af66830dd6883b6b899414eff98aa2669443bc8d42470c9a", "create_time": "2022-04-05 03:25:57.163"},
        {"user_id": 8, "username": "bob", "password": "8ca79597eb2bc1eebd93a1d595e921fcc64a2c00f175cc5dfa59a728122bc846f1bba08457795d539145508d99747a43049cee0c0f696c7d1b088131b45fa0d4", "create_time": "2022-04-05 03:41:12.857"}
    ]
}
```


Request:
```ruby
/get/users/filter/(username="bob" OR username="alice")
```

Response:
```json
{
    "message": "found 2 user entries",
    "data": [
        {"user_id": 7, "username": "alice", "password": "df564e993decffa1a96454f7fa0dc48f0bf66c981f141aaf9b140f18c7f3aed90727ec05e4fcef23af66830dd6883b6b899414eff98aa2669443bc8d42470c9a", "create_time": "2022-04-05 03:25:57.163"},
        {"user_id": 8, "username": "bob", "password": "8ca79597eb2bc1eebd93a1d595e921fcc64a2c00f175cc5dfa59a728122bc846f1bba08457795d539145508d99747a43049cee0c0f696c7d1b088131b45fa0d4", "create_time": "2022-04-05 03:41:12.857"}
    ]
}
```

##### Note on {filter_string}:
* QUERY FORMAT : ?filter=(param_name > "param_value")
* QUERY EXAMPLE: **`/get/users?filter=(user_id = "7" OR username="bob")`**
* PATH FORMAT : /filter/(param_name="param_value" OR param_name="param_value")
* PATH EXAMPLE: /get/users/filter/(username="bob" OR username="alice")
* the keyword: **`filter`** indicates that the statement following the keyword is to be applied as the **`filter`**
* the **`param_name`** must never be wrapped in quotations as it is treated as a **variable** referring to the **column_name**
* the **`"param_value"`** is usually wrapped in **"single"** or **"double"** quotations, with the exception of **NUMBERS**.
  * **NUMBERS** do not have to be wrapped in quotations
  * *However*:  It is recommended that you do wrap **NUMBERS** in quotations as to consistent with the format of
                **not wrapping** **`param_names`** and **wrapping** **`"param_values"`**.
* spaces are allowed within an *expression*
                
#### `/get` sensor data for `alice` and `bob`

Oximeter data for just `alice`:

Request:
```ruby
https://m2band.hopto.org/get/oximeter/user_id/7
```

Response
```json
{
    "message": "found 6 oximeter entries",
    "data": [
        {"entry_id": 43, "user_id": 7, "heart_rate": 134, "blood_o2": 97, "temperature": 97.6691638391727, "entry_time": "2022-04-05 12:06:01.397"},
        {"entry_id": 44, "user_id": 7, "heart_rate": 129, "blood_o2": 98, "temperature": 97.45331222228752, "entry_time": "2022-04-05 12:06:01.528"},
        {"entry_id": 45, "user_id": 7, "heart_rate": 128, "blood_o2": 100, "temperature": 97.35755335543793, "entry_time": "2022-04-05 12:06:01.740"},
        {"entry_id": 46, "user_id": 7, "heart_rate": 134, "blood_o2": 96, "temperature": 97.03691402965539, "entry_time": "2022-04-05 12:06:01.994"},
        {"entry_id": 47, "user_id": 7, "heart_rate": 132, "blood_o2": 96, "temperature": 97.78609598543946, "entry_time": "2022-04-05 12:06:02.469"},
        {"entry_id": 48, "user_id": 7, "heart_rate": 130, "blood_o2": 98, "temperature": 97.262831668111, "entry_time": "2022-04-05 12:06:02.669"}
    ]
}
```

Oximeter data for just `bob`:

Request:
```ruby
https://m2band.hopto.org/get/oximeter/user_id/8
```

Response
```json
{
    "message": "found 10 oximeter entries",
    "data": [
        {"entry_id": 49, "user_id": 8, "heart_rate": 143, "blood_o2": 97, "temperature": 97.23579109761334, "entry_time": "2022-04-05 12:16:11.420"},
        {"entry_id": 50, "user_id": 8, "heart_rate": 127, "blood_o2": 97, "temperature": 97.7532770488335, "entry_time": "2022-04-05 12:16:11.592"},
        {"entry_id": 51, "user_id": 8, "heart_rate": 131, "blood_o2": 95, "temperature": 97.89202180155488, "entry_time": "2022-04-05 12:16:11.747"},
        {"entry_id": 52, "user_id": 8, "heart_rate": 124, "blood_o2": 95, "temperature": 97.81020200542864, "entry_time": "2022-04-05 12:16:11.897"},
        {"entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.7115308733577, "entry_time": "2022-04-05 12:16:54.651"},
        {"entry_id": 54, "user_id": 8, "heart_rate": 133, "blood_o2": 100, "temperature": 103.10357503270177, "entry_time": "2022-04-05 12:16:54.808"},
        {"entry_id": 55, "user_id": 8, "heart_rate": 144, "blood_o2": 98, "temperature": 103.35133621760384, "entry_time": "2022-04-05 12:16:54.931"},
        {"entry_id": 56, "user_id": 8, "heart_rate": 134, "blood_o2": 98, "temperature": 102.16442367992002, "entry_time": "2022-04-05 12:16:55.068"},
        {"entry_id": 57, "user_id": 8, "heart_rate": 132, "blood_o2": 98, "temperature": 101.79215076652413, "entry_time": "2022-04-05 12:16:55.213"},
        {"entry_id": 58, "user_id": 8, "heart_rate": 130, "blood_o2": 99, "temperature": 102.76488036781804, "entry_time": "2022-04-05 12:16:55.351"}
    ]
}
```

Oximeter data for users with (**`user_id`** BETWEEN "6" AND "9")

Request:
```ruby
https://m2band.hopto.org/get/oximeter/filter/(user_id BETWEEN "6" AND "9")
```

Response
```json
{
    "message": "found 16 oximeter entries",
    "data": [
        {"entry_id": 43, "user_id": 7, "heart_rate": 134, "blood_o2": 97, "temperature": 97.6691638391727, "entry_time": "2022-04-05 12:06:01.397"},
        {"entry_id": 44, "user_id": 7, "heart_rate": 129, "blood_o2": 98, "temperature": 97.45331222228752, "entry_time": "2022-04-05 12:06:01.528"},
        {"entry_id": 45, "user_id": 7, "heart_rate": 128, "blood_o2": 100, "temperature": 97.35755335543793, "entry_time": "2022-04-05 12:06:01.740"},
        {"entry_id": 46, "user_id": 7, "heart_rate": 134, "blood_o2": 96, "temperature": 97.03691402965539, "entry_time": "2022-04-05 12:06:01.994"},
        {"entry_id": 47, "user_id": 7, "heart_rate": 132, "blood_o2": 96, "temperature": 97.78609598543946, "entry_time": "2022-04-05 12:06:02.469"},
        {"entry_id": 48, "user_id": 7, "heart_rate": 130, "blood_o2": 98, "temperature": 97.262831668111, "entry_time": "2022-04-05 12:06:02.669"},
        {"entry_id": 49, "user_id": 8, "heart_rate": 143, "blood_o2": 97, "temperature": 97.23579109761334, "entry_time": "2022-04-05 12:16:11.420"},
        {"entry_id": 50, "user_id": 8, "heart_rate": 127, "blood_o2": 97, "temperature": 97.7532770488335, "entry_time": "2022-04-05 12:16:11.592"},
        {"entry_id": 51, "user_id": 8, "heart_rate": 131, "blood_o2": 95, "temperature": 97.89202180155488, "entry_time": "2022-04-05 12:16:11.747"},
        {"entry_id": 52, "user_id": 8, "heart_rate": 124, "blood_o2": 95, "temperature": 97.81020200542864, "entry_time": "2022-04-05 12:16:11.897"},
        {"entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.7115308733577, "entry_time": "2022-04-05 12:16:54.651"},
        {"entry_id": 54, "user_id": 8, "heart_rate": 133, "blood_o2": 100, "temperature": 103.10357503270177, "entry_time": "2022-04-05 12:16:54.808"},
        {"entry_id": 55, "user_id": 8, "heart_rate": 144, "blood_o2": 98, "temperature": 103.35133621760384, "entry_time": "2022-04-05 12:16:54.931"},
        {"entry_id": 56, "user_id": 8, "heart_rate": 134, "blood_o2": 98, "temperature": 102.16442367992002, "entry_time": "2022-04-05 12:16:55.068"},
        {"entry_id": 57, "user_id": 8, "heart_rate": 132, "blood_o2": 98, "temperature": 101.79215076652413, "entry_time": "2022-04-05 12:16:55.213"},
        {"entry_id": 58, "user_id": 8, "heart_rate": 130, "blood_o2": 99, "temperature": 102.76488036781804, "entry_time": "2022-04-05 12:16:55.351"}
    ]
}
```

#### Test Case: Fever?
Now let's determine who may have been suspected for having a fever.
Using this definition: *Anything above 100.4 F is considered a fever.*

Request:
```ruby
/get/oximeter/filter/(temperature > "100.4") GROUP BY user_id
```

Response
```json
{"message": "1 oximeter entry found", "data": {"entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.7115308733577, "entry_time": "2022-04-05 12:16:54.651"}}
```

Only **`bob`** reached temperatures above `100.4 F`

#### Test Case: MIN, MAX, Temperature Range?
Let's get the range of temperatures from **MIN** to **MAX**

Request:
```ruby
/get/oximeter/filter/(user_id = "8") ORDER BY temperature
```

Response
```json
{
    "message": "found 10 oximeter entries",
    "data": [
        {"entry_id": 49, "user_id": 8, "heart_rate": 143, "blood_o2": 97, "temperature": 97.23579109761334, "entry_time": "2022-04-05 12:16:11.420"},
        {"entry_id": 50, "user_id": 8, "heart_rate": 127, "blood_o2": 97, "temperature": 97.7532770488335, "entry_time": "2022-04-05 12:16:11.592"},
        {"entry_id": 52, "user_id": 8, "heart_rate": 124, "blood_o2": 95, "temperature": 97.81020200542864, "entry_time": "2022-04-05 12:16:11.897"},
        {"entry_id": 51, "user_id": 8, "heart_rate": 131, "blood_o2": 95, "temperature": 97.89202180155488, "entry_time": "2022-04-05 12:16:11.747"},
        {"entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.7115308733577, "entry_time": "2022-04-05 12:16:54.651"},
        {"entry_id": 57, "user_id": 8, "heart_rate": 132, "blood_o2": 98, "temperature": 101.79215076652413, "entry_time": "2022-04-05 12:16:55.213"},
        {"entry_id": 56, "user_id": 8, "heart_rate": 134, "blood_o2": 98, "temperature": 102.16442367992002, "entry_time": "2022-04-05 12:16:55.068"},
        {"entry_id": 58, "user_id": 8, "heart_rate": 130, "blood_o2": 99, "temperature": 102.76488036781804, "entry_time": "2022-04-05 12:16:55.351"},
        {"entry_id": 54, "user_id": 8, "heart_rate": 133, "blood_o2": 100, "temperature": 103.10357503270177, "entry_time": "2022-04-05 12:16:54.808"},
        {"entry_id": 55, "user_id": 8, "heart_rate": 144, "blood_o2": 98, "temperature": 103.35133621760384, "entry_time": "2022-04-05 12:16:54.931"}
    ]
}
```

Get **`temperature`** Range of fever

Request:
```ruby
/get/oximeter/user_id/8/filter/(temperature > "100.4") ORDER BY temperature
```

Response
```json
{
    "message": "found 6 oximeter entries",
    "data": [
        {"entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.7115308733577, "entry_time": "2022-04-05 12:16:54.651"},
        {"entry_id": 57, "user_id": 8, "heart_rate": 132, "blood_o2": 98, "temperature": 101.79215076652413, "entry_time": "2022-04-05 12:16:55.213"},
        {"entry_id": 56, "user_id": 8, "heart_rate": 134, "blood_o2": 98, "temperature": 102.16442367992002, "entry_time": "2022-04-05 12:16:55.068"},
        {"entry_id": 58, "user_id": 8, "heart_rate": 130, "blood_o2": 99, "temperature": 102.76488036781804, "entry_time": "2022-04-05 12:16:55.351"},
        {"entry_id": 54, "user_id": 8, "heart_rate": 133, "blood_o2": 100, "temperature": 103.10357503270177, "entry_time": "2022-04-05 12:16:54.808"},
        {"entry_id": 55, "user_id": 8, "heart_rate": 144, "blood_o2": 98, "temperature": 103.35133621760384, "entry_time": "2022-04-05 12:16:54.931"}
    ]
}
```


Get entry with **MIN** **`temperature`** 

Request:
```ruby
/get/oximeter/user_id/8/filter/(temperature > "100.4") ORDER BY temperature LIMIT 1
```

Response
```json
{"message": "1 oximeter entry found", "data": {"entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.7115308733577, "entry_time": "2022-04-05 12:16:54.651"}}
```

Get entry with **MAX** **`temperature`** 

Request:
```ruby
/get/oximeter/user_id/8/filter/(temperature > "100.4") ORDER BY temperature DESC
```

Response
```json
{
    "message": "found 6 oximeter entries",
    "data": [
        {"entry_id": 55, "user_id": 8, "heart_rate": 144, "blood_o2": 98, "temperature": 103.35133621760384, "entry_time": "2022-04-05 12:16:54.931"},
        {"entry_id": 54, "user_id": 8, "heart_rate": 133, "blood_o2": 100, "temperature": 103.10357503270177, "entry_time": "2022-04-05 12:16:54.808"},
        {"entry_id": 58, "user_id": 8, "heart_rate": 130, "blood_o2": 99, "temperature": 102.76488036781804, "entry_time": "2022-04-05 12:16:55.351"},
        {"entry_id": 56, "user_id": 8, "heart_rate": 134, "blood_o2": 98, "temperature": 102.16442367992002, "entry_time": "2022-04-05 12:16:55.068"},
        {"entry_id": 57, "user_id": 8, "heart_rate": 132, "blood_o2": 98, "temperature": 101.79215076652413, "entry_time": "2022-04-05 12:16:55.213"},
        {"entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.7115308733577, "entry_time": "2022-04-05 12:16:54.651"}
    ]
}
```

Get **MAX**

Request:
```ruby
/get/oximeter/user_id/8/filter/(temperature > "100.4") ORDER BY temperature DESC LIMIT 1
```

Response
```json
{"message": "1 oximeter entry found", "data": {"entry_id": 55, "user_id": 8, "heart_rate": 144, "blood_o2": 98, "temperature": 103.35133621760384, "entry_time": "2022-04-05 12:16:54.931"}}
```


# 3. `/edit`
**Edit a single entry or multiple entries of a table**

Request Formats:
* **`/edit`** - returns a list of all existing tables in the database
* **`/edit/usage`** - returns a message for how to use this function
* **`/edit/{table_name}`** - returns all entries for the table: `{table_name}`
* **`/edit/{table_name}/{param_name}/{param_value}/*/*`** - edit a single entry or multiple entries of the table `{table_name}` using path parameters of `/name/value` pairs
* **`/edit/{table_name}?param_name=param_value&*=*`** - edit a single entry or multiple entries of the table `{table_name}` using query parameters of `name=value` pairs
  * **Requires**: at least 1 parameter to **`edit`** and 1 paramter to query or filter by
  * **Returns**: number of entries editted in the **`table`**
* **`/edit/{table_name}/{param_name}/{param_value}/*/*/filter/{filter_string}`** -  `/name/value` pairs and `filter` by: `{filter_string}`
* **`/edit/{table_name}?param_name=param_value&*=*&filter={filter_string}`** - return entries matching `name=value` pairs and `filter` by: `{filter_string}`
**The Filter Parameter**
- `name=value` pairs are limited to `column` paramaters with an *exact match*! (ex: username=alice, user_id=8, etc.)
- the **`{filter_string}`** supports **expressions** containing **comparrison and logical operators** as well ass **functions**
- We will examine how to use the **`filter`** parameter in the examples ahead
> Note: The old functions `/editUser`, `/editUsers`, `/editSensorData`, and `/editAllSensorData` still work but are kept for backward compatibility.
> `/editUser` has migrated to: `/edit/users`
> `/editUsers` has migrated to: `/edit/users`
> `/editSensorData` has migrated to: `/edit/oximeter`
> `/editAllSensorData` has migrated to: `/edit/oximeter`
> It is recommened to update the existing *mp32* and *swift* code to follow the new format

**Workflow Example:**
* Let's query the **`users`** table to find the 2 users we created earlier
* Next, we will query the **`oximeter`** table to retrieve the sensor data for each user
* Finally, we will examine the **`filter`** parameter and test out a few **test cases**
  * Test Case: Determine which user possibly has a **fever**
  * Test Case: What was the range of **`temperature`** for this user? **min**? **max**?
  * Test Case: Filter users created after a *start date* but before an *end date*.

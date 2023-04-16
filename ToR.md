# Terms of reference


## Purpose

Main purpose is decreasing time wasted for time managment at work 
(time spent on task, description of the work done, preparing report for ticket system).


## Required functionality

- Manage Tasks
    - Create new `Task` with some name
    - Link a `Task` to one or more `Tickets` in an `External ticket system`
    - Link a `Task` to one or more `Clients`
    - Delete `Task` (with the possibility of recovery)
- Account spent time
    - Start accounting `Time interval` for one of the task (with automaticaly stopping other tasks)
    - Stop accounting `Time interval`
    - Optional assign `Type of work` for each `Time interval`.
    For example: `git`, `documentation`, `testing`, `releasing`, `deploying` and other
    - Adding rich `Note` to each `Time interval`
    - Continue accouting `Time interval` with the same `Note`
    - Appending, editing and deleting past `Time intervals`
    - Splitting single `Time interval` to several `Time intervals`
    - Optional assign `Payment ration`, for example: `0` for office tasks, `1` for common clients tasks or `2` (double pay) for clients tasks done out of hours.
- Reports
    - Summary report for a day including:
        - List of tasks with time spent on each of them
        - Total time spent during the day
        - Spent time grouped by `Type of work`
    - Report for each task including:
        - Link to `Ticket` in an `External ticket system`
        - Date of `Task`
        - Start time of first `Time interval` of the day
        - End time of last `Time interval` of the day
        - Total time spent on task
        - `Notes` of each `Time interval` during the day (with total time)


## User interface

The following Telegram bot interface is planned to be used as the main interface:

- `/new [-c <client_code>[,<client_code>]] <task_code> <task_name>` - create new task 
with code `task_code` and name `<task_name>` and link it to one or more clients with code `<client_code>` 
(with creating clients if it doesn't exists)
- `/switch <task_code>` -  change current task to task with code `<task_code>`
- `/current` - show information of current task
- `/start` - start time accounting for current task
- `/stop` - stop time accounting for current task
- `/start [-c <client_code>[,<client_code>]] <task_name>` as alias for sequence 
    - `/new_task [-c <client_code>[,<client_code>]] <task_name>` (if task with `<task_name>` doesn't exists)
    - `/switch <task_code>`
    - `/start`
- `<text>` - add note to current task
- `/finish [<task_code>]` - mark task (current or with passed `<task_code>`) as finished
- `/accept [<task_code>]` - mark task (current or with passed `<task_code>`) as accepted
- `/active [<task_code>]` - mark task (current or with passed `<task_code>`) as active
- `/pause [<task_code>] [-u <until_date>]` - mark task (current or with passed `<task_code>`) as paused
    (if `-u` passed task will be return to active after `<until_date>`)
- `/list [-a] [N]` - show list of tasks ordered by last time accounting
    - `-a` - show all tasks, including `finished` (done by implementer), 
    `completed` (accepted by the client) and `paused`; otherwise show only `active`
    - `N` - show only N last tasks
- `/config <key> [-d|-v <value>]` - Manage user configurations. Shows value of config with key `<key>`. 
    - `<key>` - key of config
    - `-d` - drop/delete value of config with key `<key>`
    - `-v <value>` - set value `<value>` for config with key `<key>`


## Entities

- Primary (required for MVP version)
    - Task
        - (pk) task_id
        - task_code
        - task_name
        - task_status (0 - active, 1 - paused, 2 - finished, 3 - completed, 4 - archived)
        - _(fk) user_id_
    - Time_Interval
        - (pk) time_interval_id
        - (fk) task_id
        - started
        - ended
    - Note
        - (pk) note_id
        - (fk) time_interval_id
        - (fk) task_id
        - note_text
- Additional (required for full version)
    - Client
        - (pk) client_id
        - client_code
        - client_name
    - Task_Client
        - (pk) task_id
        - (pk) client_id
    - Ticket_System
        - (pk) ticket_system_id
        - ticket_system_code
        - ticket_system_name
        - ticket_system_url
        - ticket_system_access_token - uuid of localy and separate stored credentials
    - Ticket
        - (pk) ticket_id
        - (fk) ticket_system_id
        - ticket_title
        - ticket_url
    - Task_Ticket
        - (pk) task_id
        - (pk) ticket_id
    - User
        - (pk) user_id
        - user_name
        - user_telegram_id
        - user_telegram_nickname
    - User_Config
        - (pk) user_id
        - (pk) config_key
        - config_value

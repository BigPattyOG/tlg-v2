# Database Tables Overview with SQL Types

## 1. `cogs` Table

| Column     | SQLAlchemy Type | SQL Type     | Constraints            | Description                |
| ---------- | --------------- | ------------ | ---------------------- | -------------------------- |
| cog_module | String(100)     | VARCHAR(100) | PRIMARY KEY            | Module name as primary key |
| is_enabled | Boolean         | BOOLEAN      | NOT NULL, DEFAULT TRUE | Whether cog is enabled     |
| version    | String(20)      | VARCHAR(20)  | NULL                   | Cog version                |

## 2. `users` Table

| Column     | SQLAlchemy Type          | SQL Type    | Constraints                                                      | Description           |
| ---------- | ------------------------ | ----------- | ---------------------------------------------------------------- | --------------------- |
| user_id    | BigInteger               | BIGINT      | PRIMARY KEY                                                      | Discord user ID       |
| nickname   | String(32)               | VARCHAR(32) | NULL                                                             | User nickname         |
| timezone   | String(50)               | VARCHAR(50) | NULL                                                             | IANA timezone         |
| birthday   | Date                     | DATE        | NULL                                                             | User birthday         |
| coins      | Integer                  | INTEGER     | NOT NULL, DEFAULT 0                                              | Game currency         |
| exp        | Integer                  | INTEGER     | NOT NULL, DEFAULT 0                                              | Experience points     |
| is_banned  | Boolean                  | BOOLEAN     | NOT NULL, DEFAULT FALSE                                          | Ban status            |
| created_at | TIMESTAMP(timezone=True) | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP                              | Creation timestamp    |
| updated_at | TIMESTAMP(timezone=True) | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP | Last update timestamp |

## 3. `games` Table

| Column      | SQLAlchemy Type | SQL Type     | Constraints                 | Description      |
| ----------- | --------------- | ------------ | --------------------------- | ---------------- |
| game_id     | Integer         | INTEGER      | PRIMARY KEY, AUTO_INCREMENT | Game identifier  |
| name        | String(100)     | VARCHAR(100) | NOT NULL, UNIQUE            | Game name        |
| description | Text            | TEXT         | NULL                        | Game description |

## 4. `events` Table

| Column            | SQLAlchemy Type          | SQL Type     | Constraints                 | Description       |
| ----------------- | ------------------------ | ------------ | --------------------------- | ----------------- |
| event_id          | BigInteger               | BIGINT       | PRIMARY KEY, AUTO_INCREMENT | Event identifier  |
| event_name        | String(200)              | VARCHAR(200) | NOT NULL                    | Event name        |
| event_description | Text                     | TEXT         | NULL                        | Event description |
| start_time        | TIMESTAMP(timezone=True) | TIMESTAMPTZ  | NULL                        | Event start time  |
| end_time          | TIMESTAMP(timezone=True) | TIMESTAMPTZ  | NULL                        | Event end time    |
| metadata          | JSON                     | JSON/JSONB   | NULL                        | Event metadata    |
| participants      | Integer                  | INTEGER      | NOT NULL, DEFAULT 0         | Participant count |
| status            | String(20)               | VARCHAR(20)  | NOT NULL, DEFAULT 'pending' | Event status      |

## 5. `event_logs` Table

| Column    | SQLAlchemy Type          | SQL Type    | Constraints                             | Description        |
| --------- | ------------------------ | ----------- | --------------------------------------- | ------------------ |
| log_id    | BigInteger               | BIGINT      | PRIMARY KEY, AUTO_INCREMENT             | Log identifier     |
| event_id  | BigInteger               | BIGINT      | NOT NULL, FOREIGN KEY → events.event_id | Reference to event |
| user_id   | BigInteger               | BIGINT      | NOT NULL, FOREIGN KEY → users.user_id   | Reference to user  |
| data      | JSON                     | JSON/JSONB  | NULL                                    | Log data           |
| logged_at | TIMESTAMP(timezone=True) | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP     | Log timestamp      |

## 6. `profiles` Table

| Column       | SQLAlchemy Type          | SQL Type     | Constraints                                                      | Description                |
| ------------ | ------------------------ | ------------ | ---------------------------------------------------------------- | -------------------------- |
| profile_id   | Integer                  | INTEGER      | PRIMARY KEY, AUTO_INCREMENT                                      | Profile identifier         |
| user_id      | BigInteger               | BIGINT       | NOT NULL, FOREIGN KEY → users.user_id                            | Reference to user          |
| game_id      | Integer                  | INTEGER      | NOT NULL, FOREIGN KEY → games.game_id                            | Reference to game          |
| profile_name | String(100)              | VARCHAR(100) | NULL                                                             | Profile name               |
| data         | JSON                     | JSON/JSONB   | NULL                                                             | Game-specific profile data |
| created_at   | TIMESTAMP(timezone=True) | TIMESTAMPTZ  | NOT NULL, DEFAULT CURRENT_TIMESTAMP                              | Creation timestamp         |
| updated_at   | TIMESTAMP(timezone=True) | TIMESTAMPTZ  | NOT NULL, DEFAULT CURRENT_TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP | Last update timestamp      |

## 7. `bot_roles` Table

| Column      | SQLAlchemy Type | SQL Type    | Constraints                 | Description        |
| ----------- | --------------- | ----------- | --------------------------- | ------------------ |
| role_id     | Integer         | INTEGER     | PRIMARY KEY, AUTO_INCREMENT | Role identifier    |
| name        | String(50)      | VARCHAR(50) | NOT NULL, UNIQUE            | Role name          |
| description | Text            | TEXT        | NULL                        | Role description   |
| bit_value   | BigInteger      | BIGINT      | NOT NULL                    | Permission bitmask |
| active      | Boolean         | BOOLEAN     | NOT NULL, DEFAULT TRUE      | Role status        |

## 8. `command_usage` Table

| Column        | SQLAlchemy Type          | SQL Type     | Constraints                           | Description          |
| ------------- | ------------------------ | ------------ | ------------------------------------- | -------------------- |
| usage_id      | Integer                  | INTEGER      | PRIMARY KEY, AUTO_INCREMENT           | Usage identifier     |
| user_id       | BigInteger               | BIGINT       | NOT NULL, FOREIGN KEY → users.user_id | Reference to user    |
| command_name  | String(100)              | VARCHAR(100) | NOT NULL                              | Command name         |
| guild_id      | BigInteger               | BIGINT       | NULL                                  | Discord guild ID     |
| error_message | Text                     | TEXT         | NULL                                  | Error message if any |
| executed_at   | TIMESTAMP(timezone=True) | TIMESTAMPTZ  | NOT NULL, DEFAULT CURRENT_TIMESTAMP   | Execution timestamp  |

## 9. `achievements` Table

| Column         | SQLAlchemy Type          | SQL Type     | Constraints                         | Description             |
| -------------- | ------------------------ | ------------ | ----------------------------------- | ----------------------- |
| achievement_id | Integer                  | INTEGER      | PRIMARY KEY, AUTO_INCREMENT         | Achievement identifier  |
| name           | String(100)              | VARCHAR(100) | NOT NULL, UNIQUE                    | Achievement name        |
| description    | Text                     | TEXT         | NOT NULL                            | Achievement description |
| rarity         | String(20)               | VARCHAR(20)  | NOT NULL, DEFAULT 'common'          | Rarity level            |
| coin_reward    | Integer                  | INTEGER      | NOT NULL, DEFAULT 0                 | Coin reward             |
| exp_reward     | Integer                  | INTEGER      | NOT NULL, DEFAULT 0                 | Experience reward       |
| icon_url       | String(255)              | VARCHAR(255) | NULL                                | Achievement icon URL    |
| category       | String(50)               | VARCHAR(50)  | NULL                                | Achievement category    |
| is_active      | Boolean                  | BOOLEAN      | NOT NULL, DEFAULT TRUE              | Active status           |
| is_hidden      | Boolean                  | BOOLEAN      | NOT NULL, DEFAULT FALSE             | Hidden until unlocked   |
| created_at     | TIMESTAMP(timezone=True) | TIMESTAMPTZ  | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Creation timestamp      |

## 10. `user_achievements` Table

| Column         | SQLAlchemy Type          | SQL Type    | Constraints                                            | Description                 |
| -------------- | ------------------------ | ----------- | ------------------------------------------------------ | --------------------------- |
| user_id        | BigInteger               | BIGINT      | PRIMARY KEY, FOREIGN KEY → users.user_id               | Reference to user           |
| achievement_id | Integer                  | INTEGER     | PRIMARY KEY, FOREIGN KEY → achievements.achievement_id | Reference to achievement    |
| progress       | Integer                  | INTEGER     | NOT NULL, DEFAULT 100                                  | Completion percentage       |
| unlocked_at    | TIMESTAMP(timezone=True) | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP                    | Unlock timestamp            |
| unlock_data    | JSON                     | JSON/JSONB  | NULL                                                   | Achievement unlock metadata |

UPDATE subagents
   SET wake_triggers = REPLACE(wake_triggers, '"user_response"', '"user_message"')
 WHERE wake_triggers LIKE '%user_response%';

import sqlite3
import json
import uuid
import sys

def main():
    db_path = "/opt/novaic/data/gateway.db"
    print(f"Connecting to {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
        
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all messages
    cursor.execute("SELECT id, content, agent_id FROM chat_messages")
    messages = cursor.fetchall()
    print(f"Scanning {len(messages)} total messages...")
    
    updated_count = 0
    registered_files = 0
    
    for msg in messages:
        msg_id = msg["id"]
        agent_id = msg["agent_id"]
        content_raw = msg["content"]
        if not content_raw:
            continue
        
        try:
            content = json.loads(content_raw)
        except Exception:
            # Not JSON
            continue
        
        if not isinstance(content, dict) or "attachments" not in content:
            continue
        
        attachments = content.get("attachments", [])
        if not attachments or not isinstance(attachments, list):
            continue
        
        # Get user_id for the agent
        cursor.execute("SELECT user_id FROM agents WHERE id = ?", (agent_id,))
        agent_row = cursor.fetchone()
        if not agent_row:
            continue
        user_id = agent_row["user_id"]
        
        changed = False
        for att in attachments:
            if not isinstance(att, dict):
                continue
                
            # Check if it already has a file_id AND that file_id exists in registry
            existing_file_id = att.get("file_id")
            if existing_file_id:
                cursor.execute("SELECT id FROM files WHERE id = ?", (existing_file_id,))
                if cursor.fetchone():
                    continue # Already registered correctly

            # We need to register it
            url = att.get("url")
            if not url or not isinstance(url, str):
                continue
                
            if not url.startswith("/api/files/") and not url.startswith("/api/images/"):
                # E.g. external http URL or something else
                if url.startswith("/"):
                    # Might be legacy local path that isn't /api/files/, let's assume it's /api/files/...
                    pass
                else:
                    continue
            
            # Generate new file_id
            file_id = "f_" + uuid.uuid4().hex[:12]
            att["file_id"] = file_id
            changed = True
            
            storage_key = url
            size = att.get("size", 0)
            if not isinstance(size, int):
                try:
                    size = int(size)
                except:
                    size = 0
                    
            mime_type = att.get("type", "application/octet-stream")
            filename = att.get("name", "attachment")
            
            print(f"Registering old attachment in msg {msg_id}: {filename} -> {file_id} ({storage_key})")
            cursor.execute(
                """
                INSERT INTO files (id, user_id, agent_id, category, mime_type, size, filename, storage_backend, storage_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, user_id, agent_id, "chat_attachments", mime_type, size, filename, "local", storage_key)
            )
            registered_files += 1
            
        if changed:
            new_content_raw = json.dumps(content)
            cursor.execute("UPDATE chat_messages SET content = ? WHERE id = ?", (new_content_raw, msg_id))
            updated_count += 1
            
    conn.commit()
    print(f"Done. Updated {updated_count} messages, registered {registered_files} files.")

if __name__ == "__main__":
    main()

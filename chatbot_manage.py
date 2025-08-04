#chatbot_manage.py
import datetime
import sqlite3
import os
from dotenv import load_dotenv
from gemini_api import call_gemini_api
from db_utilities import get_user_id, get_title_for_session, get_summary_for_session


load_dotenv()
debugging = os.getenv("debugging", "false").lower() == "true"

def chat_with_gemini(username, message, session_id=None, first_message=False):
    stateful = bool(username and session_id)
    user_id = get_user_id(username)

    if stateful:
        if first_message:
            first_prompt = [
                {"author": "system",    "content": "You are a helpful assistant."},
                {"author": "user",      "content": "Prompt: " + message}
            ]
            try:
                reply = call_gemini_api(first_prompt)

                first_prompt.append({"author": "assistant", "content": "GPT Answer: " + reply})
                first_prompt.append({
                    "author": "system",
                    "content": "Give me the summary of this conversation so far. "
                               "Do not skip important details while keeping it concise."
                               "Especially technical details, if exists."
                               "Also put the preferred language in the summary if it is mentioned in the conversation."
                               "I will use this as context for the next message."
                })
                summary = call_gemini_api(first_prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            title_prompt = [
                {"author": "system",
                 "content": "Give me a very short (3-5 word) title summarizing this conversation so far."
                 "Just return the title without any additional text. It should be concise and descriptive."
                 "Do not go beyond 5 words. Do not use quotes or any other punctuation. Do not use 'title' in the response."
                 "Do not say here is the title or anything similar. Answer in language of the user's prompt."
                 "Do not use any special characters or formatting. Just 3 to 5 plain words."},
                {"author": "assistant", "content": "GPT Conversation Summary: " + summary}
            ]
            try:
                title_candidate = call_gemini_api(title_prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API for title:", e)
                return None
            if debugging:
                print("Title candidate:", title_candidate)
            generated_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
            if debugging:
                print("Generated title:", generated_title)

            user_msg_id = add_message_to_session(session_id, "user", message, "")
            bot_msg_id  = add_message_to_session(session_id, "bot",  reply,   summary)

            update_session_title(session_id, generated_title)

            return {
                "session_id": session_id,
                "user_id":    user_id,
                "title": generated_title,
                "messages": [
                    {"message_id": user_msg_id, "sender": "user", "content": message},
                    {"message_id": bot_msg_id,  "sender": "bot",  "content": reply}
                ]
            }
        
        else:
            session_title = get_title_for_session(session_id)
            prompt = [
                {"author": "system",
                 "content": "These are the summary and title so far. Use them "
                            "and the following message as context for the next reply."
                            "Do not repeat the summary or title in your reply."
                            "Do not say 'based on the title and summary' and/or refer to the summary."
                            "Do not say given the context or anything similar. Unless the user asks for it, do not repeat the summary or title."
                            "Answer in the language of the user's preference, if it is mentioned."
                            "This will be used as context for the next message as follow-up."},
                {"author": "assistant", "content": "Title: " + session_title},
                {"author": "assistant", "content": "Summary so far: " + get_summary_for_session(session_id)},
                {"author": "user",      "content": "Prompt: " + message}
            ]

            try:
                reply = call_gemini_api(prompt)
                prompt.append({"author": "assistant", "content": "GPT Answer: " + reply})
                prompt.append({
                    "author": "system",
                    "content": "Give me the summary of this conversation so far. "
                               "It includes old summary, title, your last reply, and the new user message."
                               "Do not skip important details while keeping it concise."
                               "Especially technical details, if exists."
                               "Also put the preferred language in the summary if it is mentioned in the conversation."
                               "I will use this as context for the next message."
                })
                summary = call_gemini_api(prompt)
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            if session_title == "New Conversation":
                title_prompt = [
                    {"author": "system",
                    "content": "Give me a very short (3-5 word) title summarizing this conversation so far."
                    "Just return the title without any additional text. It should be concise and descriptive."
                    "Do not go beyond 5 words. Do not use quotes or any other punctuation. Do not use 'title' in the response."
                    "Do not say here is the title or anything similar. Answer in language of the user's prompt."
                    "Do not use any special characters or formatting. Just 3 to 5 plain words."},
                    {"author": "assistant", "content": "GPT Conversation Summary: " + summary}
                ]
                try:
                    title_candidate = call_gemini_api(title_prompt)
                except Exception as e:
                    if debugging:
                        print("Error while calling Gemini API for title:", e)
                    return None
                if debugging:
                    print("Title candidate:", title_candidate)
                session_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
                if debugging:
                    print("Generated title:", session_title)
                update_session_title(session_id, session_title)

            user_msg_id = add_message_to_session(session_id, "user", message, "")
            bot_msg_id  = add_message_to_session(session_id, "bot",  reply,   summary)

            return {
                "session_id": session_id,
                "user_id":    user_id,
                "title":     session_title,
                "messages": [
                    {"message_id": user_msg_id, "sender": "user", "content": message},
                    {"message_id": bot_msg_id,  "sender": "bot",  "content": reply}
                ]
            }
    else:
        try:
            reply = call_gemini_api([{"author": "user", "content": message}])
            return {
                "session_id": "None",
                "user_id":    "guest",
                "messages": [
                    {"message_id": "None", "sender": "user", "content": message},
                    {"message_id": "None",  "sender": "bot",  "content": reply}
                ]
            }
        except Exception as e:
            if debugging:
                print("Error while calling Gemini API:", e)
            return None

def create_session_for_user(username, title=None):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM user WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            if debugging:
                print(f"User '{username}' not found; cannot create session.")
            return None
        user_id = row[0]
        cur.execute(
            "INSERT INTO session (user_id, title, isDeleted) VALUES (?, ?, ?)",
            (user_id, title, 'FALSE')
        )
        conn.commit()
        session_id = cur.lastrowid
        if debugging:
            print(
                f"Created session id={session_id} for username='{username}' "
                f"(user_id={user_id}) with isDeleted='FALSE'"
            )
        return session_id

    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in create_session_for_user:", e)
        return None

    finally:
        cur.close()
        conn.close()

def add_message_to_session(session_id, sender, content, summary):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO message (session_id, sender, content, summary, created_at) "
            "VALUES (?, ?, ?, ?, ?) RETURNING id",
            (session_id, sender, content, summary, created_at)
        )
        row = cur.fetchone()
        conn.commit()
        message_id = row[0] if row else None
        if debugging:
            print(
                f"Inserted message id={message_id} in session_id={session_id}: "
                f"sender={sender}, content={content}, summary={summary}, at={created_at}"
            )
        return message_id
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in add_message_to_session:", e)
        return None
    finally:
        cur.close()
        conn.close()

def update_session_title(session_id, new_title):
    conn = sqlite3.connect('database.sqlite')
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE session SET title = ? WHERE id = ?",
            (new_title, session_id)
        )
        conn.commit()
        if debugging:
            print(f"Updated session {session_id} title to: {new_title}")
        return cur.rowcount == 1
    except sqlite3.Error as e:
        if debugging:
            print("SQLite error in update_session_title:", e)
        return False
    finally:
        cur.close()
        conn.close()
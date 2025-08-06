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
                {"author": "user", "content": "You are a helpful assistant. Please respond to this message: " + message}
            ]
            try:
                reply = call_gemini_api(first_prompt, use_tools=True)

                summary_prompt = [
                    {"author": "user", "content": f"User asked: {message}"},
                    {"author": "assistant", "content": f"I responded: {reply}"},
                    {"author": "user", "content": "Give me a summary of this conversation so far. "
                                                  "Do not skip important details while keeping it concise. "
                                                  "Especially technical details, if they exist. "
                                                  "Also note the preferred language if mentioned. "
                                                  "Keep the last code if you answered with code to make adjustments on the next message. "
                                                  "I will use this as context for the next message."}
                ]
                summary = call_gemini_api(summary_prompt, use_tools=False)  # Summary doesn't need tools
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            title_prompt = [
                {"author": "user", "content": f"Based on this conversation where user said: '{message}' "
                                              f"and I responded with: '{reply}', "
                                              f"give me a very short 3-5 word title. "
                                              f"Just return the title without quotes or extra text. "
                                              f"Answer in the same language as the user's message."}
            ]
            try:
                title_candidate = call_gemini_api(title_prompt, use_tools=False)  # Title generation doesn't need tools
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API for title:", e)
                return None
                
            if debugging:
                print("Title candidate:", title_candidate)
            generated_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
            if debugging:
                print("Generated title:", generated_title)

            if message and reply and summary and generated_title:
                user_msg_id = add_message_to_session(session_id, "user", message, "")
                bot_msg_id = add_message_to_session(session_id, "bot", reply, summary)
                update_session_title(session_id, generated_title)
            else:
                if debugging:
                    print("Missing one of the required fields for message/session creation")
                return None
            return {
                "session_id": session_id,
                "user_id": user_id,
                "title": generated_title,
                "messages": [
                    {"message_id": user_msg_id, "sender": "user", "content": message},
                    {"message_id": bot_msg_id, "sender": "bot", "content": reply}
                ]
            }
        
        else:
            session_title = get_title_for_session(session_id)
            session_summary = get_summary_for_session(session_id)
            
            prompt = [
                {"author": "user", "content": f"Context - Title: {session_title}\n"
                                              f"Summary: {session_summary}\n"
                                              f"Current message: {message}\n\n"
                                              f"Please respond naturally to the current message using the context provided. "
                                              f"Don't refer to the summary or title unless relevant."}
            ]

            try:
                reply = call_gemini_api(prompt, use_tools=True)  # Main conversation needs tools
                
                summary_prompt = [
                    {"author": "user", "content": f"Previous context: {session_summary}\n"
                                                  f"User just said: {message}\n"
                                                  f"I responded: {reply}\n\n"},
                    {"author": "user", "content": "Give me a summary of this conversation so far. "
                                                  "Do not skip important details while keeping it concise. "
                                                  "Especially technical details, if they exist. "
                                                  "Also note the preferred language if mentioned. "
                                                  "Keep the last code if you answered with code to make adjustments on the next message. "
                                                  "I will use this as context for the next message."}
                ]
                summary = call_gemini_api(summary_prompt, use_tools=False)  # Summary doesn't need tools
            except Exception as e:
                if debugging:
                    print("Error while calling Gemini API:", e)
                return None

            if session_title == "New Conversation":
                title_prompt = [
                    {"author": "user", "content": f"Based on this conversation summary: {summary}, "
                                                  f"give me a 3-5 word title. "
                                                  f"Just return the title without quotes or extra text."}
                ]
                try:
                    title_candidate = call_gemini_api(title_prompt, use_tools=False)  # Title generation doesn't need tools
                    session_title = (title_candidate or "New Conversation").strip().strip('"').strip('*')
                    if session_title:
                        update_session_title(session_id, session_title)
                        if debugging:
                            print("Updated session title to:", session_title)
                except Exception as e:
                    if debugging:
                        print("Error while calling Gemini API for title:", e)

            if message and reply and summary:
                user_msg_id = add_message_to_session(session_id, "user", message, "")
                bot_msg_id = add_message_to_session(session_id, "bot", reply, summary)
            else:
                if debugging:
                    print("Missing one of the required fields for message/session creation")
                return None
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "title": session_title,
                "messages": [
                    {"message_id": user_msg_id, "sender": "user", "content": message},
                    {"message_id": bot_msg_id, "sender": "bot", "content": reply}
                ]
            }
    else:
        try:
            prompt = [{"author": "user", "content": message}]
            reply = call_gemini_api(prompt, use_tools=True)  # Guest chat also gets tools
            return {
                "session_id": "None",
                "user_id": "guest",
                "messages": [
                    {"message_id": "None", "sender": "user", "content": message},
                    {"message_id": "None", "sender": "bot", "content": reply}
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
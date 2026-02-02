import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Callable


LOG_FILE = "conversation_history.txt"
KB_FILE = "knowledge_base.json"


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


class RuleBasedChatbot:
    """
    Simple rule-based chatbot using:
    - pattern matching (regex)
    - intents (greeting, help, small talk, exit, thanks, time, etc.)
    - small knowledge base for domain Q&A
    - console interaction + conversation logging
    """

    def __init__(self, kb_path: str = KB_FILE, log_path: str = LOG_FILE):
        self.kb_path = Path(kb_path)
        self.log_path = Path(log_path)
        self.kb: Dict[str, str] = self._load_kb()
        self.user_name: Optional[str] = None

        # Ordered rules: first match wins
        self.rules: List[Tuple[str, str, Callable]] = [
            ("greeting", r"^(hi|hello|hey|assalamualaikum|salam)\b.*", self._reply_greeting),
            ("help", r"^(help|how to use|commands|menu)\b.*", self._reply_help),
            ("set_name", r"^(my name is|i am)\s+([a-zA-Z ]{2,40})$", self._reply_set_name),
            ("ask_name", r"^(what is my name|who am i)\b.*", self._reply_ask_name),
            ("small_talk_howareyou", r"^(how are you|how r you|how're you)\b.*", self._reply_how_are_you),
            ("small_talk_whoareyou", r"^(who are you|what are you)\b.*", self._reply_who_are_you),
            ("thanks", r"^(thanks|thank you|thx)\b.*", self._reply_thanks),
            ("time", r"^(time|what time is it)\b.*", self._reply_time),
            ("exit", r"^(exit|quit|bye|goodbye)\b.*", self._reply_exit),
            ("kb_what_is", r"^(what is|define)\s+(.+)$", self._reply_kb_what_is),
            ("kb_direct", r"^(.+)$", self._reply_kb_direct_or_fallback),
        ]

    def _load_kb(self) -> Dict[str, str]:
        if self.kb_path.exists():
            return json.loads(self.kb_path.read_text(encoding="utf-8"))
        return {}

    def log(self, speaker: str, message: str) -> None:
        line = f"[{now_stamp()}] {speaker}: {message}\n"
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line)

    def respond(self, user_input: str) -> str:
        text = normalize(user_input)

        for intent, pattern, handler in self.rules:
            m = re.match(pattern, text)
            if m:
                reply = handler(m)
                self.log("USER", f"{user_input}  (intent={intent})")
                self.log("BOT", reply)
                return reply

        reply = "I didn't understand. Type 'help' to see options."
        self.log("USER", user_input)
        self.log("BOT", reply)
        return reply

    # --------- intent handlers ---------

    def _reply_greeting(self, _m) -> str:
        if self.user_name:
            return f"Hello, {self.user_name}! How can I help you today?"
        return "Hello! I’m a simple rule-based chatbot. Type 'help' to see what I can do."

    def _reply_help(self, _m) -> str:
        return (
            "Here are some things you can try:\n"
            "- Say: hi / hello\n"
            "- Tell me your name: 'my name is Ammar'\n"
            "- Ask: 'what is AI' or 'define machine learning'\n"
            "- Ask: 'how to submit task'\n"
            "- Type: time\n"
            "- Type: exit\n"
        )

    def _reply_set_name(self, m) -> str:
        name = m.group(2).strip().title()
        self.user_name = name
        return f"Nice to meet you, {name}! Ask me: 'what is AI'."

    def _reply_ask_name(self, _m) -> str:
        if self.user_name:
            return f"Your name is {self.user_name} (as you told me)."
        return "I don't know your name yet. You can say: 'my name is ...'."

    def _reply_how_are_you(self, _m) -> str:
        return "I’m doing good! I’m here and ready to help. What would you like to ask?"

    def _reply_who_are_you(self, _m) -> str:
        return "I’m a simple rule-based chatbot. I use pattern matching and a knowledge base to answer questions."

    def _reply_thanks(self, _m) -> str:
        return "You’re welcome! If you need more help, just type 'help'."

    def _reply_time(self, _m) -> str:
        return f"Current time is: {now_stamp()}"

    def _reply_exit(self, _m) -> str:
        return "Goodbye! Conversation saved in conversation_history.txt"

    # --------- knowledge base ---------

    def _kb_lookup(self, key: str) -> Optional[str]:
        key = normalize(key)
        if key in self.kb:
            return self.kb[key]

        k2 = re.sub(r"[^a-z0-9 ]+", "", key).strip()
        if k2 in self.kb:
            return self.kb[k2]

        for k in self.kb.keys():
            if k in key or key in k:
                return self.kb[k]
        return None

    def _reply_kb_what_is(self, m) -> str:
        topic = m.group(2).strip()
        qkey = f"what is {topic}"
        ans = self._kb_lookup(qkey)
        if ans:
            return ans
        return (
            f"I don't have '{topic}' in my knowledge base yet.\n"
            "Try: 'what is AI', 'what is NLP', or type 'help'."
        )

    def _reply_kb_direct_or_fallback(self, m) -> str:
        question = m.group(1).strip()
        ans = self._kb_lookup(question)
        if ans:
            return ans
        return (
            "I’m not sure about that.\n"
            "Try:\n"
            "- 'what is AI'\n"
            "- 'define machine learning'\n"
            "- 'help'\n"
        )


def main():
    print("=== Simple Rule-Based Chatbot (Console) ===")
    print("Type 'help' to see commands. Type 'exit' to quit.\n")

    bot = RuleBasedChatbot()
    bot.log("SYSTEM", "--- New chat session started ---")

    while True:
        user = input("You: ")
        reply = bot.respond(user)
        print(f"Bot: {reply}\n")

        if normalize(user) in {"exit", "quit", "bye", "goodbye"}:
            break


if __name__ == "__main__":
    main()

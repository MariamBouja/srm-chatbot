from chatbot.conversation import handle_message, new_state
from chatbot.rag import get_source_metadata


def format_response(result):
    parts = [f"Réponse:\n{result['answer']}"]

    if result["sources"]:
        lines = []
        for source in result["sources"]:
            meta = get_source_metadata(source)
            if meta["url"]:
                lines.append(f"• {meta['title']} — {meta['url']}")
            else:
                lines.append(f"• {meta['title']}")
        parts.append("Sources utilisées :\n" + "\n".join(lines))

    return "\n\n".join(parts)


def main():
    print("SRM-SM Chatbot — tapez 'exit' pour quitter.\n")

    state = new_state()

    while True:
        question = input("Question: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        try:
            result = handle_message(question, state)
        except Exception as e:
            print(f"Erreur: {e}\n")
            continue

        print(f"\n{format_response(result)}\n")


if __name__ == "__main__":
    main()

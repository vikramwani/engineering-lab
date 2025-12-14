from src.client import LLMService

def main():
    llm = LLMService()
    reply = llm.chat("Write a 1-sentence fun fact about software engineering.")
    print(reply)

if __name__ == "__main__":
    main()

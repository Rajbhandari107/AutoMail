from app.auth import get_gmail_credentials


def main():
    credentials = get_gmail_credentials()

    if credentials and credentials.valid:
        print("Gmail authentication successful!")
    else:
        print("Gmail authentication failed.")


if __name__ == "__main__":
    main()
import asyncio
import csv
import getpass
import re
from twscrape import API

async def scrape_user_tweets(api: API, username: str, keyword: str) -> None:
    """Search tweets from a user containing a keyword and save to CSV."""
    normalized_username = username.lstrip("@").strip()
    normalized_keyword = keyword.strip()
    query = f"from:{normalized_username} {normalized_keyword}"
    safe_keyword = re.sub(r"[^A-Za-z0-9_-]+", "_", normalized_keyword).strip("_") or "keyword"
    filename = f"{normalized_username}_{safe_keyword}_tweets.csv"
    count = 0

    def write_tweet_row(writer: csv.writer, tweet) -> None:
        writer.writerow([
            tweet.id,
            tweet.date,
            tweet.user.username,
            tweet.rawContent,
            tweet.likeCount,
            tweet.retweetCount
        ])

    # Open the CSV file and set up the writer
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header row
        writer.writerow(["Tweet ID", "Date", "Author", "Text", "Likes", "Retweets"])

        print(f"Scraping tweets for: {query}...")

        # Stream the tweets and write them to the CSV
        tweet_stream = api.search(query, limit=-1)
        try:
            first_tweet = await tweet_stream.__anext__()
            write_tweet_row(writer, first_tweet)
            count += 1

            async for tweet in tweet_stream:
                write_tweet_row(writer, tweet)
                count += 1
        except StopAsyncIteration:
            print(f"No tweets found for '{username}' with keyword '{keyword}'.")
            return
        except (asyncio.TimeoutError, TimeoutError):
            if count > 0:
                print(f"Network timeout while collecting tweets. Saved {count} tweets to {filename}.")
            else:
                print("The request timed out before any tweets were collected. Please try again.")
            return
        except Exception as exc:
            if "No active accounts" in str(exc) or "No account" in str(exc):
                print("No active logged-in scraper account is available. Verify credentials and try again.")
                return
            if count > 0:
                print(f"An unexpected error occurred after collecting {count} tweets: {exc}")
            else:
                print(f"An unexpected error occurred while collecting tweets: {exc}")
            return

    print(f"Successfully saved {count} tweets to {filename}")

async def main() -> None:
    # Initialize the API
    api = API("accounts.db", raise_when_no_account=True)

    print("-" * 40)
    print("Enter your X account details used for scraping login.")
    scraper_username = input("Scraper X username (without @): ").strip()
    scraper_password = getpass.getpass("Scraper X password: ").strip()
    scraper_email = input("Scraper email: ").strip()
    scraper_email_password = getpass.getpass("Scraper email password: ").strip()
    print("-" * 40)

    # Add and log in the scraper account
    await api.pool.add_account(
        scraper_username,
        scraper_password,
        scraper_email,
        scraper_email_password,
    )
    await api.pool.login_all(usernames=[scraper_username])

    # Get dynamic inputs from the user in the console
    print("-" * 40)
    target_username = input("Enter the target X username (e.g., @elonmusk): ").strip()
    target_keyword = input("Enter the search keyword (e.g., space): ")
    print("-" * 40)

    # Run the scraper with the user's inputs
    await scrape_user_tweets(api, target_username, target_keyword)

if __name__ == "__main__":
    asyncio.run(main())

# lemonAPI
Small part of larger API. Gives random fact related to lemons. The larger API is not yet published.

## Usage
**This project is built to run in docker, basically only because of PostgreSQL**
You may connect to your own postgresql host by modifying `./lemonapi/utils/config.py` ``Server`` class.

## Credentials
The default admin credentials are `admin` with password `weakadmin`, change those!
> [!IMPORTANT]
> Make sure to copy over the contents of `.env-template` to `.env` with the appropriate credentials.

### Docker usage
Project has `Dockerfile` and `docker-compose.yml` pre made.
1) clone repo
2) in terminal type `docker compose up --build` to run and build or `docker compose build` to only build image
3) API should be running

### Using the API

The API should be running at `http://localhost:5001` check `http://localhost:5001/docs` to view endpoints.

## How to make a request to get API token?
Most of functionality can be tested alone in the `/docs` endpoint, but you may as well interact with code.
This example will give you access to authorization token used to authenticate your request to endpoints requiring OAuth2.
Also if you prefer the default docs, you can find them from `/redoc` for redoc docs and `/altdocs` for swagger.

With curl when endpoint is running with https:
```bash
curl -d "username=admin&password=weakadmin" --ssl-no-revoke -X POST https://localhost:5001/token
```
Example below shows basic usage to allow you to receive your API tokens and use them against protected endpoints.
```py
import requests
import json

# Define user login data
data = {"username": "admin", "password": "weakadmin"}

# request to get refresh_token
resp = requests.post(
    "http://localhost:5001/token",
    data=data,
)
refresh_token = resp.json()["refresh"]

# json.dumps is required, otherwise `requests` will try to send form.
# request to get access_token
access_token_resp = requests.post(
    "http://localhost:5001/authenticate",
    data=json.dumps({"refresh_token": refresh_token}),
    headers={"Content-type": "application/json", "accept": "application/json"},
)


# And to test that all is working, running this section as well.
# You need to pass in the token to get your userinformation.
access_token = access_token_resp.json()["access_token"]
foo = requests.get(
    "http://localhost:5001/users/me",
    headers={"Authorization": f"Bearer {access_token}"},
)

# tests against another protected endpoint requiring auth
bar = requests.get(
    "http://localhost:5001/lemon/verbs",
    headers={"Authorization": f"Bearer {access_token_resp.json()["access_token"]}"},
)
print(foo.status_code)  # you should be granted with status code 200
print(foo.json(), "\n")  # this would display your user information

print(bar.status_code)  # you should be granted with status code 200
print(bar.json())  # should return random verb describing lemons!
```
That's it, you should be able to get started with the basics
## Errors

If you find a bug or error, open an issue and give a required information such as function/line where it happens in at, what is wrong and possibly other information (optional)

Want to know more about the API? Open an issue with label **question** or DM me in discord or something idk.

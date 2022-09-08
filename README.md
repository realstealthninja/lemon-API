# lemonAPI
Small part of larger API. Gives random fact related to lemons. The larger API is not yet published.

## Usage
**docker is recommended even if you have redis running locally**

## Credentials
Basic credentials for API are the following
> username: johndoe
> password: secret

### Docker usage
Project has `Dockerfile` and `docker-compose.yml` pre made.
1) clone repo
2) in terminal type `docker-compose up --build` to run and build or `docker-compose build` to only build image
3) API should be running 

### Using the API

The API should be running at `http://localhost:5001` check `http://localhost:5001/docs` to view endpoints.

## Errors

If you find a bug or error, open an issue and give a required information such as function/line where it happens in at, what is wrong and possibly other information (optional)

Want to know more about the API? Open an issue with label **question** or DM me in discord or something idk.

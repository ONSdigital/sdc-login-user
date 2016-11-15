# External user login
This component provides authentication for external users and returns a JWT on successful login.

There are two endpoints on this service as follows:

## /login

Send a *post* to this endpoint with a json message containing 'email' and 'password' in order to authenticate.

## /profile

Send a *get* to this endpoint, passing the JWT in a 'token' header to retrieve the profile.

Send a *post* to this endpoint, passing the JWT in a 'token' header to update the profile.

## User profile

A user profile contains the following information:

| User           |
| -------------- |
| respondent_id  |
| name           |
| email          |

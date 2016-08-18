#!/bin/bash
curl -v -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com"}' http://localhost:5000/login
